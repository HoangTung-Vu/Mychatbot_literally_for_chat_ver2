import logging
from typing import Optional, Dict, Any, List, Tuple
import google.generativeai as genai
import datetime

from app.services.llm import BaseLLMService

logger = logging.getLogger(__name__)

class MemorizeAgentService(BaseLLMService):
    """
    Service for the Memorize Agent that identifies and extracts important information.
    This agent uses gemini-1.5-flash for efficient information extraction.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize the Memorize Agent service.
        
        Args:
            api_key: API key for Google Gemini API
            model: Model name to use
        """
        super().__init__(api_key, api_key_env_name="GEMINI_API_KEY2")
            # Format the system prompt for information extraction
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        system_prompt = self._build_system_prompt()
        self.model = genai.GenerativeModel(model, system_instruction=system_prompt)

        
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response identifying important information in the prompt.
        
        Args:
            prompt: Text to analyze for important information
            **kwargs: Additional parameters to pass to the Gemini API
            
        Returns:
            Generated response text with important information
        """
        try:
            # Generate the response
            response = self.model.generate_content(
                f"Text to analyze: {prompt}",
                **kwargs
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error extracting information from memorize agent: {e}")
            return ""
            
    def extract_important_information(self, text: str) -> List[str]:
        """
        Extract important pieces of information from a text.
        
        Args:
            text: Text to analyze for important information
            
        Returns:
            List of important information items
        """
        response = self.generate_response(text)
        
        # Parse the response into separate information items
        if not response:
            return []
            
        # Split by numbered items or newlines
        items = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('Important'):
                # Remove numbering if present (e.g., "1. ", "- ")
                cleaned_line = line
                if len(line) > 2 and (line[0].isdigit() and line[1:3] in ['. ', ') ']) or line.startswith('- '):
                    cleaned_line = line[line.find(' ')+1:]
                items.append(cleaned_line)
        return items
        
    def determine_query_needs(self, prompt: str) -> str:
        """
        Determine what important information may be needed to answer a prompt.
        
        Args:
            prompt: User's prompt text
            
        Returns:
            A query for searching semantic memory
        """
        enhanced_prompt = f"What important information might be needed to answer this query: '{prompt}'? Please response only keywords no addtional text."
        response = self.generate_response(enhanced_prompt)
        print(response)
        # The response should be usable as a query for semantic memory
        return response
        
    def extract_from_conversation(self, prompt: str, response: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract important information from a conversation turn (prompt and response).
        
        Args:
            prompt: User's prompt text
            response: AI's response text
            
        Returns:
            List of (text, metadata) tuples for storage in semantic memory
        """
        # Combine prompt and response for context
        conversation = f"User: {prompt}\n\nAssistant: {response}"
        
        # Ask the agent to extract important information
        extracted_info = self.extract_important_information(conversation)
        
        # Format for storage
        result = []
        for i, info in enumerate(extracted_info):
            metadata = {
                "source_type": "conversation",
                "conversation_role": "user_and_assistant",  # Changed from list to string
                "extracted_index": i,
                "original_prompt": prompt[:100],  # Store truncated original prompt in metadata
                "datetime": datetime.datetime.now().isoformat()  # Add datetime in ISO format
            }
            result.append((info, metadata))
        print(result)
        return result
        
    def important_till_now(self, retrieved_documents: List[Dict[str, Any]], current_time: datetime.datetime = None) -> str:
        """
        Evaluate the importance of retrieved documents based on their age and content relevance.
        
        Args:
            retrieved_documents: List of documents retrieved from semantic memory
            current_time: Current datetime (defaults to now if not provided)
            
        Returns:
            String containing filtered and prioritized important information
        """
        if not retrieved_documents:
            return ""
            
        if current_time is None:
            current_time = datetime.datetime.now()
            
        # Prepare documents with their age information for the LLM
        documents_with_age = []
        for doc in retrieved_documents:
            doc_datetime = None
            try:
                # Try to parse the datetime from the metadata
                if "datetime" in doc.get("metadata", {}):
                    doc_datetime = datetime.datetime.fromisoformat(doc["metadata"]["datetime"])
                elif "timestamp" in doc.get("metadata", {}):
                    doc_datetime = datetime.datetime.fromtimestamp(doc["metadata"]["timestamp"])
            except (ValueError, TypeError):
                pass
                
            # Calculate days since the document was created
            days_old = None
            if doc_datetime:
                delta = current_time - doc_datetime
                days_old = delta.days
                
            documents_with_age.append({
                "text": doc.get("text", ""),
                "days_old": days_old,
                "metadata": doc.get("metadata", {})
            })
            
        # Prepare prompt for the LLM to evaluate importance
        prompt = """Below are pieces of information from memory with their age in days. 
                    Some information may be outdated or less relevant now.
                    Please select and prioritize the most important, relevant, and current information:

"""
        for i, doc in enumerate(documents_with_age, 1):
            days_info = f" (from {doc['days_old']} days ago)" if doc['days_old'] is not None else " (unknown age)"
            prompt += f"{i}. {doc['text']}{days_info}\n"
            
        prompt += "\nProvide only still relevant information."
        
        # Generate response that filters and prioritizes information
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error evaluating importance of retrieved documents: {e}")
            # Fallback: return the text of the most recent document
            if documents_with_age:
                sorted_docs = sorted(documents_with_age, key=lambda x: x["days_old"] if x["days_old"] is not None else float('inf'))
                return sorted_docs[0]["text"]
            return ""
        
    def _build_system_prompt(self) -> str:
        """
        Build a system prompt for information extraction.
        
        Returns:
            Formatted system prompt text
        """
        return """You are a memorization agent. Your job is to identify and extract important information from text that should be remembered for future conversations.

When analyzing text:
1. Focus on factual information, preferences, personal details, and key concepts
2. Ignore pleasantries, common knowledge, and contextual conversation
3. Format each important piece of information as a separate, concise statement
4. (IMPORTANT) Include only the most salient details that would be useful in future conversations
5. Present each item on a new line, numbered (1, 2, 3, etc.)
6. Don't explain or introduce your list, just provide the extracted information
7. You may also filter important information based on its relevance and age
8. IMPORTANT: For text in Vietnamese, maintain the original pronouns and references correctly
9. Don't switch perspectives when extracting information - maintain the original perspective of the speaker

Example 1 (English):
Text to analyze: "My name is John and I work as a software engineer at Acme Corp. I've been working there for 5 years and I love hiking on weekends, especially in the Rocky Mountains."
1. John works as a software engineer at Acme Corp for 5 years
2. John enjoys hiking in the rocky mountains on weekends

Example 2 (English):
Text to analyze: "What information might we need to determine the best machine learning approach for a computer vision task involving detecting defects in manufactured parts?"
1. ML approach for computer vision
2. detecting defects in manufactured parts
3. Context requires evaluating different computer vision algorithms for defect detection
"""
