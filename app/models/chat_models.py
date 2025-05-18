from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Model for chat requests coming into the API.
    """
    prompt: str = Field(..., description="User's input text prompt")
    
    
class ChatResponse(BaseModel):
    """
    Model for responses returned by the API.
    """
    response_text: str = Field(..., description="AI generated response text")
    
    # Optional fields for returning context information used in response
    temporal_context: Optional[List[Dict[str, Any]]] = Field(None, 
        description="Temporal information retrieved from history")
    semantic_context: Optional[List[Dict[str, Any]]] = Field(None, 
        description="Semantic information retrieved from vector store")


class MemoryEntry(BaseModel):
    """
    Model for entries to be stored in memory.
    """
    text: str = Field(..., description="Text content to be stored")
    source_type: str = Field(..., description="Source of the entry (e.g., 'prompt', 'response', 'extraction')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the entry")
    timestamp: Optional[float] = None