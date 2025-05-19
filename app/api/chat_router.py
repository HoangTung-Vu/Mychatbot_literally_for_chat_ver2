from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import uuid
import time
import datetime
from datetime import timezone, timedelta

from app.models.chat_models import ChatRequest, ChatResponse, MemoryEntry
from app.services.temporal_service import TemporalService
from app.services.memory_service import MemoryService
from app.services.llm.main_llm_service import MainLLMService
from app.services.llm.temporal_agent_service import TemporalAgentService
from app.services.llm.memorize_agent_service import MemorizeAgentService

# Define GMT+7 timezone
GMT7 = timezone(timedelta(hours=7))

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get service instances
def get_temporal_service():
    # In a real application, you'd load this from environment variables
    return TemporalService(db_path="./data/chat_history.db")
    
def get_memory_service():
    # In a real application, you'd load this from environment variables
    return MemoryService(db_path="./data/vector_store", collection_name="semantic_memory")
    
def get_main_llm_service():
    return MainLLMService()
    
def get_temporal_agent_service():
    return TemporalAgentService()
    
def get_memorize_agent_service():
    return MemorizeAgentService()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    temporal_service: TemporalService = Depends(get_temporal_service),
    memory_service: MemoryService = Depends(get_memory_service),
    main_llm: MainLLMService = Depends(get_main_llm_service),
    temporal_agent: TemporalAgentService = Depends(get_temporal_agent_service),
    memorize_agent: MemorizeAgentService = Depends(get_memorize_agent_service)
):
    """
    Process a chat request and generate a response with context from memory systems.
    This implements the Prompt Stage of the system.
    """
    try:
        # Step 1: Save the user's prompt in temporal memory
        temporal_service.save_interaction(
            content=request.prompt,
            role="user"
        )
        
        # Step 2: Retrieve temporal information with Temporal Agent
        sql_query = temporal_agent.generate_sql_query(request.prompt)
        print(f"Generated SQL Query: {sql_query}")
        queried_messages = temporal_service.execute_sql_query(sql_query)
        # print(f"Queried Messages: {queried_messages}")

        # Step 3: Relevance Filtering
        # In a more sophisticated system, you would use embeddings comparison here
        messages_relevant_from_time = temporal_service.filter_relevant_messages(
            request.prompt, queried_messages
        )
        
        # Step 4: Semantic Memory Retrieval
        query_for_semantic = memorize_agent.determine_query_needs(request.prompt)
        retrieved_important_info = memory_service.query_similar_documents(
            query_for_semantic, n_results=5
        )
        
        # Step 4a: Filter retrieved information by importance considering time
        current_time = datetime.datetime.now(GMT7)
        filtered_important_info_text = memorize_agent.important_till_now(
            retrieved_important_info, 
            current_time
        )
        
        # Format the filtered information as a list with a single item for the response model
        if filtered_important_info_text:
            filtered_important_info = [{
                'text': filtered_important_info_text,
                'metadata': {'source': 'filtered_by_importance', 'datetime': current_time.isoformat()},
                'id': str(uuid.uuid4())
            }]
        else:
            filtered_important_info = []
        
        # Step 5: Recent Conversation History
        recent_messages = temporal_service.get_recent_messages(count=8)
        
        # Step 6: Generate Response with Main LLM
        response_text = main_llm.generate_response(
            prompt=request.prompt,
            recent_messages=recent_messages,
            temporal_context=messages_relevant_from_time,
            semantic_context=filtered_important_info  # Using filtered information based on time relevance
        )
        
        # Save Stage: Add the response to the conversation history
        background_tasks.add_task(
            save_memory_in_background,
            request.prompt,
            response_text,
            temporal_service,
            memory_service,
            memorize_agent
        )
        
        # Return the response
        return ChatResponse(
            response_text=response_text,
            temporal_context=messages_relevant_from_time,
            semantic_context=filtered_important_info  # Return the filtered information
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request."
        )

@router.get("/chat/history")
async def get_chat_history(
    temporal_service: TemporalService = Depends(get_temporal_service)
):
    """
    Get all chat history from the temporal memory.
    This endpoint is used to load all previous messages when the UI loads.
    """
    try:
        # Retrieve all messages from temporal memory
        all_messages = temporal_service.get_all_messages()
        
        return {
            "messages": all_messages
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while retrieving chat history."
        )

async def save_memory_in_background(
    prompt: str,
    response: str,
    temporal_service: TemporalService,
    memory_service: MemoryService,
    memorize_agent: MemorizeAgentService
):
    """
    Background task to save the conversation in both temporal and semantic memory.
    This implements the Save Stage of the system.
    """
    try:
        # Step 1: Save the response to temporal memory
        temporal_service.save_interaction(
            content=response,
            role="assistant"
        )
        
        # Step 2: Extract important information from the conversation
        extracted_info = memorize_agent.extract_from_conversation(prompt, response)
        
        # Step 3: Save important information to semantic memory
        for text, metadata in extracted_info:
            try:
                # Add timestamp and datetime to metadata
                metadata.update({
                    "timestamp": time.time(),
                    "datetime": datetime.datetime.now(GMT7).isoformat()
                })
                
                memory_service.add_document(text, metadata)
            except Exception as e:
                logger.error(f"Error storing extracted information in semantic memory: {e}")
                
    except Exception as e:
        logger.error(f"Error in background memory saving: {e}", exc_info=True)