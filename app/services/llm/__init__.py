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
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service with an API key.
        
        Args:
            api_key: API key for the LLM service. If None, tries to load from environment.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No API key provided for LLM service")
    
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