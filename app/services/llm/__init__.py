"""
LLM services for AI responses, temporal and memory operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class BaseLLMService(ABC):
    """
    Base class for LLM services.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_key_env_name: str = "GEMINI_API_KEY"):
        """
        Initialize the LLM service with an API key.
        
        Args:
            api_key: API key for the LLM service. If None, tries to load from environment.
            api_key_env_name: Name of the environment variable to load the API key from if api_key is None.
        """
        self.api_key = api_key or os.getenv(api_key_env_name)
        if not self.api_key:
            logger.warning(f"No API key provided for LLM service (tried environment variable {api_key_env_name})")
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The text prompt to send to the LLM
            **kwargs: Additional parameters to pass to the LLM API
            
        Returns:
            Generated response text
        """
        pass