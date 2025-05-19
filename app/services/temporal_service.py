import sqlite3
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import json
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import torch 

from app.services.embedding_functions import VietnameseSBERTEmbeddingFunction

# Define GMT+7 timezone
GMT7 = timezone(timedelta(hours=7))

logger = logging.getLogger(__name__)

class TemporalService:
    """
    Service for managing temporal memory through SQLite database operations.
    Handles storage and retrieval of conversation history.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the temporal service with a path to the SQLite database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.embedding_function = VietnameseSBERTEmbeddingFunction()
        self._ensure_db_exists()
        
    def _ensure_db_exists(self) -> None:
        """
        Create the database and necessary tables if they don't exist.
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.
        
        Returns:
            SQLite connection object
        """
        return sqlite3.connect(self.db_path)
        
    def save_interaction(self, content: str, role: str = "user", 
                         metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Save a new interaction to the database.
        
        Args:
            content: The text content of the interaction
            role: The role of the speaker (user or assistant)
            metadata: Optional additional metadata
            
        Returns:
            The ID of the inserted row
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute(
            '''
            INSERT INTO conversations (role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?)
            ''',
            (role, content, timestamp, metadata_json)
        )
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return row_id
    
    def get_recent_messages(self, count: int = 4) -> List[Dict[str, Any]]:
        """
        Get the most recent messages from the database.
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
        SELECT id, role, content, timestamp, metadata
        FROM conversations
        ORDER BY timestamp DESC LIMIT ?
        '''
        
        cursor.execute(query, (count,))
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        messages = []
        for row in rows:
            # Create datetime with GMT+7 timezone
            dt = datetime.fromtimestamp(row['timestamp'], tz=GMT7)
            
            message = {
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp'],
                'datetime': dt.isoformat(),
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            }
            messages.append(message)
            
        conn.close()
        
        return list(reversed(messages)) 
    
    def execute_sql_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query on the database.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of results as dictionaries
        """
        # Modify the query to use localtime instead of UTC
        query = query.replace(
            "datetime(timestamp, 'unixepoch')", 
            "datetime(timestamp, 'unixepoch', '+7 hours')"
        )
        
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            results = []
            for row in rows:
                result = {key: row[key] for key in row.keys()}
                
                # Parse metadata if present
                if 'metadata' in result and result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                else:
                    result['metadata'] = {}
                    
                # Add formatted datetime if timestamp exists but not already converted by SQL
                if 'timestamp' in result and 'datetime' not in result:
                    dt = datetime.fromtimestamp(result['timestamp'], tz=GMT7)
                    result['datetime'] = dt.isoformat()
                    
                results.append(result)
                
            conn.close()
            return results
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            conn.close()
            return []

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages from the database in chronological order.
        
        Returns:
            List of all message dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
        SELECT id, role, content, timestamp, metadata
        FROM conversations
        ORDER BY timestamp ASC
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        messages = []
        for row in rows:
            # Create datetime with GMT+7 timezone
            dt = datetime.fromtimestamp(row['timestamp'], tz=GMT7)
            
            message = {
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp'],
                'datetime': dt.isoformat(),
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            }
            messages.append(message)
            
        conn.close()
        
        return messages
    

    def _get_embedding(self, text: str) -> np.ndarray:
        """Tokenize and get the embedding for a given text using Vietnamese SBERT."""
        # Use the embedding function to get embeddings
        return self.embedding_function([text])[0]

    def filter_relevant_messages(self, query: str, messages: List[Dict[str, Any]], threshold : float = 0.4) -> List[Dict[str, Any]]:
        """
        Filter messages based on relevance to the query using cosine similarity.
        Use keepitreal/vietnamese-sbert model for embeddings.
        """
        query_embedding = self._get_embedding(query)
        relevant_messages = []

        for msg in messages:
            content = msg.get('content', '')
            if not content:
                continue

            msg_embedding = self._get_embedding(content)
            similarity = cosine_similarity([query_embedding], [msg_embedding])[0][0]
            # print(f"Similarity: {similarity:.4f} for message: {content[:50]}...")
            if similarity >= threshold:
                print(f"Similarity: {similarity:.4f} for message: {content[:50]}...")
                msg_with_score = msg.copy()
                msg_with_score['similarity'] = float(similarity)
                relevant_messages.append(msg_with_score)

        # Sort messages by similarity score in descending order
        relevant_messages.sort(key=lambda x: x['similarity'], reverse=True)
        return relevant_messages

