import logging
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai import types
import datetime
from datetime import datetime

from app.services.llm import BaseLLMService

logger = logging.getLogger(__name__)

class MainLLMService(BaseLLMService):
    """
    Service for the main LLM that generates responses to user prompts.
    This uses a more powerful model than the specialized agents.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        """
        Initialize the Main LLM service.
        
        Args:
            api_key: API key for Google Gemini API
            model: Model name to use
        """
        super().__init__(api_key)

        genai.configure(api_key=self.api_key)
        self.model_name = model
        # Load the main system prompt from file
        self.base_system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """
        Load the system prompt from a file.
        
        Returns:
            System prompt text loaded from file
        """
        try:
            # Get the absolute path to the system prompt file in the LLM folder
            prompt_path = os.path.join(os.path.dirname(__file__), "private_main_system_prompt.txt")
            
            # Check if file exists
            if not os.path.exists(prompt_path):
                logger.warning(f"System prompt file not found at: {prompt_path}")
                return "You are a helpful AI assistant with hybrid memory capabilities."
            
            # Read the prompt from file
            with open(prompt_path, "r") as f:
                return f.read().strip()
                
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            return "You are a helpful AI assistant with hybrid memory capabilities."
        
    def generate_response(self, 
                         prompt: str, 
                         recent_messages: List[Dict[str, Any]] = None,
                         temporal_context: List[Dict[str, Any]] = None,
                         semantic_context: List[Dict[str, Any]] = None,
                         **kwargs) -> str:
        """
        Generate a response using the main LLM based on the prompt and various contexts.
        
        Args:
            prompt: User's prompt text
            recent_messages: List of recent conversation messages
            temporal_context: Temporal context information retrieved from history
            semantic_context: Semantic context information retrieved from memory
            **kwargs: Additional parameters to pass to the Gemini API
            
        Returns:
            Generated response text
        """
        try:

            # Format the context information into a complete system prompt
            system_instruction = self._build_system_prompt(
                recent_messages, 
                temporal_context, 
                semantic_context
            )
            config = {
                "max_output_tokens": 512,
                "temperature": 0.1
            }
            print(f"System Instruction: {system_instruction}")
            self.model = genai.GenerativeModel(self.model_name, generation_config=config, system_instruction=system_instruction)


            # Generate the response using generate_content
            response = self.model.generate_content(
                contents=prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response from main LLM: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again."
            
    def _build_system_prompt(self,
                           recent_messages: List[Dict[str, Any]] = None,
                           temporal_context: List[Dict[str, Any]] = None,
                           semantic_context: List[Dict[str, Any]] = None) -> str:
        """
        Build a system prompt that includes all context information.
        
        Args:
            recent_messages: List of recent conversation messages
            temporal_context: Temporal context information retrieved from history
            semantic_context: Semantic context information retrieved from memory
            
        Returns:
            Formatted system prompt text
        """
        # Start with the base system prompt loaded from file
        system_prompt = self.base_system_prompt
        
        # Add time context
        system_prompt += "\n\n## Current Date and Time Context:\n"
        system_prompt += f"\n- Current Date: {datetime.now().strftime('%Y-%m-%d')}"
        system_prompt += f"\n- Current Time: {datetime.now().strftime('%H:%M:%S')}"
        system_prompt += f"\n- Current Day: {datetime.now().strftime('%A')}"

        # Add recent conversation history
        if recent_messages and len(recent_messages) > 0:
            system_prompt += "\n\n## Recent Conversation History:\n"
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                system_prompt += f"\n{role.title()}: {content}"
        
        # Add temporal context
        if temporal_context and len(temporal_context) > 0:
            system_prompt += "\n\n## Relevant Time-Based Context:\n"
            for i, ctx in enumerate(temporal_context):
                content = ctx.get('content', '')
                dt = ctx.get('datetime', '')
                system_prompt += f"\n{i+1}. ({dt}) {content}"
        
        # Add semantic context
        if semantic_context and len(semantic_context) > 0:
            system_prompt += "\n\n## Relevant Semantic Knowledge:\n"
            for i, ctx in enumerate(semantic_context):
                text = ctx.get('text', '')
                system_prompt += f"\n{i+1}. {text}"
                
        return system_prompt