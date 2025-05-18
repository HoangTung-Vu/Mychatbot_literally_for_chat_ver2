import sqlite3
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

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
            message = {
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'timestamp': row['timestamp'],
                'datetime': datetime.fromtimestamp(row['timestamp']).isoformat(),
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            }
            messages.append(message)
            
        conn.close()
        
        # Return in chronological order
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
                    
                # Add formatted datetime
                if 'timestamp' in result:
                    result['datetime'] = datetime.fromtimestamp(result['timestamp']).isoformat()
                    
                results.append(result)
                
            conn.close()
            return results
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            conn.close()
            return []