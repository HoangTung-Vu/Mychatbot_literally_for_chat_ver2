import os
import time
import logging
import uuid
import datetime
from typing import List, Dict, Any, Optional, Union
from datetime import timezone, timedelta

import chromadb
from chromadb.api.models import Collection
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

# Import the custom embedding function
from app.services.embedding_functions import VietnameseSBERTEmbeddingFunction

# Define GMT+7 timezone
GMT7 = timezone(timedelta(hours=7))

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Service for managing semantic memory through vector database operations.
    Handles embedding, storage, and retrieval of semantic information.
    """
    
    def __init__(self, db_path: str, collection_name: str = "semantic_memory"):
        """
        Initialize the memory service with a path to the ChromaDB database.
        
        Args:
            db_path: Path to the ChromaDB persistent directory
            collection_name: Name of the collection to use
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        embedding_func = VietnameseSBERTEmbeddingFunction()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        try:
            # First try to get the existing collection without specifying the embedding function
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Retrieved existing collection: {self.collection_name}")
        except Exception as e:
            logger.info(f"Creating new collection: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}  # Explicitly set distance metric to cosine
            )
            
    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a document to the vector store with automatic embedding.
        
        Args:
            text: Text content to be embedded and stored
            metadata: Optional metadata for the document
            
        Returns:
            Document ID
        """
        # Generate a unique ID if none provided in metadata
        doc_id = str(uuid.uuid4())
        
        # Update metadata with timestamp if not present
        if metadata is None:
            metadata = {}
        if 'timestamp' not in metadata:
            metadata['timestamp'] = time.time()
        
        # Add ISO format datetime if not present, using GMT+7 timezone
        if 'datetime' not in metadata:
            metadata['datetime'] = datetime.datetime.now(GMT7).isoformat()
            
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            return doc_id
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise
            
    def query_similar_documents(self, 
                               query_text: str, 
                               n_results: int = 5,
                               where: Optional[Dict[str, Any]] = None,
                               threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Query the vector store for documents similar to the query text.
        
        Args:
            query_text: Text to find similar documents for
            n_results: Maximum number of results to return
            where: Optional filter criteria
            threshold: Minimum similarity score required for results (higher is better for cosine)
                       Typical values: 0.3 (lenient), 0.5 (balanced), 0.7 (strict)
            
        Returns:
            List of similar documents with their metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format the results
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                distance = results.get('distances', [[]])[0][i] if results.get('distances') else None
                
                # Convert distance to similarity score (cosine distance to cosine similarity)
                similarity = 1 - distance if distance is not None else 0
                
                # Only include results that meet the similarity threshold
                if similarity >= threshold:
                    result = {
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'id': results['ids'][0][i],
                        'similarity': similarity,
                        'distance': distance
                    }
                    formatted_results.append(result)
                
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
            
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            doc_id: ID of the document to delete
            
        Returns:
            Success status
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            return False
            
    def update_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing document in the vector store.
        
        Args:
            doc_id: ID of the document to update
            text: New text content
            metadata: New metadata
            
        Returns:
            Success status
        """
        try:
            # Update the metadata with a timestamp if not present
            if metadata is None:
                metadata = {}
            if 'timestamp' not in metadata:
                metadata['timestamp'] = time.time()
                
            # Add ISO format datetime if not present, using GMT+7 timezone
            if 'datetime' not in metadata:
                metadata['datetime'] = datetime.datetime.now(GMT7).isoformat()
                
            self.collection.update(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating document in vector store: {e}")
            return False