import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from chromadb.utils import embedding_functions


class VietnameseSBERTEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """
    Custom embedding function for ChromaDB that uses Vietnamese SBERT model.
    """
    def __init__(self, model=None, tokenizer=None):
        """
        Initialize the embedding function with the Vietnamese SBERT model.
        
        Args:
            model: Optional pre-loaded model instance
            tokenizer: Optional pre-loaded tokenizer instance
        """
        if model is None or tokenizer is None:
            # Load model and tokenizer if not provided
            self.tokenizer = AutoTokenizer.from_pretrained("keepitreal/vietnamese-sbert")
            self.model = AutoModel.from_pretrained("keepitreal/vietnamese-sbert")
        else:
            # Use provided model and tokenizer
            self.model = model
            self.tokenizer = tokenizer
        
    def __call__(self, texts):
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy.ndarray: Array of embeddings
        """
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Get embeddings from the CLS token (first token)
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings