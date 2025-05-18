"""
Database initialization module for Conversational AI with Hybrid Memory System.
Provides functions to initialize both SQLite (temporal) and ChromaDB (semantic) databases.
"""

import os
import logging
import sqlite3
import chromadb
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_temporal_db(db_path: Optional[str] = None) -> bool:
    """
    Initialize the SQLite database for temporal memory.
    
    Args:
        db_path: Path to the SQLite database file. If None, uses environment variable.
        
    Returns:
        Success status
    """
    try:
        # Get DB path from environment if not provided
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH", "./data/chat_history.db")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create conversations table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metadata TEXT
        )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Temporal database initialized successfully at: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing temporal database: {e}")
        return False
    
def init_semantic_db(db_path: Optional[str] = None, collection_name: Optional[str] = None) -> bool:
    """
    Initialize the ChromaDB for semantic memory.
    
    Args:
        db_path: Path to the ChromaDB directory. If None, uses environment variable.
        collection_name: Name of the collection to create. If None, uses environment variable.
        
    Returns:
        Success status
    """
    try:
        # Get configuration from environment if not provided
        if db_path is None:
            db_path = os.getenv("VECTOR_DB_PATH", "./data/vector_store")
            
        if collection_name is None:
            collection_name = os.getenv("VECTOR_DB_COLLECTION_NAME", "semantic_memory")
            
        # Create directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=db_path)
        
        # Check if collection exists, if not create it
        try:
            collection = client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except Exception:
            collection = client.create_collection(name=collection_name)
            logger.info(f"Created new collection: {collection_name}")
        
        logger.info(f"Semantic database initialized successfully at: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing semantic database: {e}")
        return False

def init_all_databases() -> bool:
    """
    Initialize all databases used by the application.
    
    Returns:
        Overall success status
    """
    temporal_success = init_temporal_db()
    semantic_success = init_semantic_db()
    
    return temporal_success and semantic_success

if __name__ == "__main__":
    # Configure logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize all databases
    if init_all_databases():
        logger.info("All databases initialized successfully!")
    else:
        logger.error("Database initialization failed. Check logs for details.")