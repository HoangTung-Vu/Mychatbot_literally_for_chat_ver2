import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from datetime import datetime, timedelta
import json

from app.services.llm import BaseLLMService

logger = logging.getLogger(__name__)

class TemporalAgentService(BaseLLMService):
    """
    Service for the Temporal Agent that generates SQL queries for time-based context.
    This agent uses gemini-1.5-flash for efficient query generation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize the Temporal Agent service.
        
        Args:
            api_key: API key for Google Gemini API
            model: Model name to use
        """
        super().__init__(api_key)
        self.model = model
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
    
    def generate_sql_query(self, prompt: str) -> str:
        """
        Generate a SQL query based on the user's prompt for querying the conversations table.
        
        Args:
            prompt: User's prompt text
            
        Returns:
            Generated SQL query
        """
        try:
            # Get current date info for context
            current_time = datetime.now()
            date_context = {
                "current_date": current_time.strftime("%Y-%m-%d"),
                "current_day": current_time.strftime("%A"),
                "current_month": current_time.strftime("%B"),
                "current_year": current_time.year,
                "current_timestamp": int(current_time.timestamp())
            }
            
            system_prompt = self._build_system_prompt(date_context)
            model = genai.GenerativeModel(self.model, system_instruction=system_prompt)
            
            # Generate the SQL query directly
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.05}  # Low temperature for consistent SQL output
            )
            
            # Clean the response
            sql_query = self._clean_sql_response(response.text)
            
            # Validate the query - make sure it only selects datetime and role
            if not self._validate_sql_query(sql_query):
                # Default to a safe query if validation fails
                logger.warning(f"Generated SQL query failed validation: {sql_query}")
                sql_query = "SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations ORDER BY timestamp DESC LIMIT 10"
            
            logger.info(f"Generated temporal query: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            # Return a safe default query in case of error
            return "SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations ORDER BY timestamp DESC LIMIT 10"
    
    def _clean_sql_response(self, response_text: str) -> str:
        """
        Clean the SQL response from the LLM.
        """
        # Remove any markdown formatting
        text = response_text.strip()
        
        # If response is wrapped in code blocks, extract just the SQL part
        if text.startswith("```sql"):
            text = text.replace("```sql", "", 1)
            text = text.replace("```", "", 1)
        elif text.startswith("```"):
            text = text.replace("```", "", 2)
        
        return text.strip()
    
    def _validate_sql_query(self, sql_query: str) -> bool:
        """
        Validate that the SQL query only selects datetime and role.
        """
        # Convert to lowercase for easier checking
        sql_lower = sql_query.lower()
        
        # Check that it's a SELECT statement
        if not sql_lower.startswith("select "):
            return False
        
        # Check that it contains the base selection we want
        if "datetime(timestamp, 'unixepoch') as datetime" not in sql_lower and "role" not in sql_lower:
            return False
        
        # Check that it doesn't select content or other columns
        if "content" in sql_lower.split("where")[0]:
            return False
        
        # Check that it's querying the conversations table
        if "from conversations" not in sql_lower:
            return False
            
        return True
    
    def _build_system_prompt(self, date_context: Dict[str, Any]) -> str:
        """
        Build a system prompt for SQL query generation.
        
        Args:
            date_context: Dictionary with current date information
            
        Returns:
            Formatted system prompt text
        """
        current_date = date_context["current_date"]
        current_day = date_context["current_day"]
        current_month = date_context["current_month"]
        current_year = date_context["current_year"]
        current_timestamp = date_context["current_timestamp"]
        
        return f"""You are a temporal SQL query generator that creates SQLite queries based on user requests. Your job is to convert natural language time references into precise SQL queries that retrieve conversation records.

TODAY'S DATE: {current_date} ({current_day}, {current_month} {current_year})
CURRENT UNIX TIMESTAMP: {current_timestamp}

DATABASE SCHEMA:
- Table name: conversations
- Key columns: timestamp (REAL, unix timestamp), role (TEXT, either 'user' or 'assistant')

IMPORTANT RULES:
1. ALWAYS use "SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations" as the base of your query
2. NEVER include the content column or any other columns in the SELECT clause
3. Apply appropriate timestamp-based WHERE conditions based on user's time references
4. ALWAYS ORDER BY timestamp DESC and include a LIMIT clause
5. Generate ONLY the SQL query - no explanation, no comments, no markdown

EXAMPLES:

User Query: "Show my messages from yesterday"
SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations WHERE timestamp >= {current_timestamp - 86400} AND timestamp < {current_timestamp - 0} ORDER BY timestamp DESC LIMIT 10

User Query: "What did I talk about last week?"
SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations WHERE timestamp >= {current_timestamp - 604800} AND timestamp < {current_timestamp - 86400*2} ORDER BY timestamp DESC LIMIT 10

User Query: "Show my conversations from May 10th"
SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations WHERE timestamp >= strftime('%s', '2025-05-10 00:00:00') AND timestamp < strftime('%s', '2025-05-11 00:00:00') ORDER BY timestamp DESC LIMIT 10

User Query: "Get my recent messages"
SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations ORDER BY timestamp DESC LIMIT 10

User Query: "Show interactions from 3 days ago"
SELECT datetime(timestamp, 'unixepoch') as datetime, role FROM conversations WHERE timestamp >= {current_timestamp - 86400*3} AND timestamp < {current_timestamp - 86400*2} ORDER BY timestamp DESC LIMIT 10

REMEMBER:
- Be precise with date calculations
- Use appropriate SQLite date/time functions
- Always think about the correct time ranges based on the current date
- Only output a valid SQLite query with no additional text"""
        
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        This method is kept for backward compatibility but now just calls generate_sql_query
        """
        return self.generate_sql_query(prompt)