import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import json

from app.services.llm import BaseLLMService

# Define GMT+7 timezone
GMT7 = timezone(timedelta(hours=7))

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
        super().__init__(api_key, api_key_env_name="GEMINI_API_KEY1")
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
            # Get current date info for context using GMT+7
            current_time = datetime.now(GMT7)
            date_context = {
                "current_date": current_time.strftime("%Y-%m-%d"),
                "current_day": current_time.strftime("%A"),
                "current_month": current_time.strftime("%B"),
                "current_year": current_time.year,
                "current_timestamp": int(current_time.timestamp())
            }
            
            # Calculate today's time range in GMT+7
            start_of_day = datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0, tzinfo=GMT7)
            start_timestamp = int(start_of_day.timestamp())
            
            end_of_day = datetime(current_time.year, current_time.month, current_time.day, 23, 59, 59, tzinfo=GMT7)
            end_timestamp = int(end_of_day.timestamp())
            
            # Default query for today if no time references found - use GMT+7 format
            default_today_query = f"SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations WHERE timestamp >= {start_timestamp} AND timestamp <= {end_timestamp} ORDER BY timestamp ASC"
            
            # Create an enhanced prompt that instructs the agent
            enhanced_prompt = f"""Analyze this user message and generate an appropriate SQL query to retrieve relevant conversations:
            
            User message: "{prompt}"

            INSTRUCTIONS:
            1. First, determine if this message contains ANY specific time references (like today, yesterday, May 10, last week, etc.)
            2. If NO time references are found, return EXACTLY this query:
               {default_today_query}
            3. If time references ARE found, generate a SQL query that:
               - Targets the specific time period mentioned
               - Uses "SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations"
               - Includes appropriate timestamp filters using WHERE clauses
               - Orders by timestamp DESC
               - Limits to 10 results

            Your response should be ONLY THE SQL QUERY with no explanations or additional text."""

            system_prompt = self._build_system_prompt(date_context, default_today_query)
            model = genai.GenerativeModel(self.model, system_instruction=system_prompt)
            
            # Generate the SQL query
            response = model.generate_content(
                enhanced_prompt,
                generation_config={"temperature": 0.01}  # Very low temperature for consistent output
            )
            
            # Clean the response
            sql_query = self._clean_sql_response(response.text)
            
            
            # Validate the query
            if not self._validate_sql_query(sql_query, allow_content=True):
                # Default to today's query if validation fails
                logger.warning(f"Generated SQL query failed validation: {sql_query}")
                return default_today_query
            
            logger.info(f"Generated temporal query: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            # Return a safe default query in case of error
            return f"SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations WHERE timestamp >= {start_timestamp} AND timestamp <= {end_timestamp} ORDER BY timestamp ASC"
    
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
    
    def _validate_sql_query(self, sql_query: str, allow_content: bool = False) -> bool:
        """
        Validate that the SQL query only selects datetime and role.
        
        Args:
            sql_query: SQL query to validate
            allow_content: Whether to allow content column in SELECT clause
            
        Returns:
            True if valid, False otherwise
        """
        # Convert to lowercase for easier checking
        sql_lower = sql_query.lower()
        
        # Check that it's a SELECT statement
        if not sql_lower.startswith("select "):
            return False
        
        # Check that it contains datetime conversion with GMT+7 timezone
        if "datetime(timestamp, 'unixepoch', '+7 hours') as datetime" not in sql_lower:
            return False
        
        # Check that it contains role
        if "role" not in sql_lower:
            return False
        
        # Check that it's querying the conversations table
        if "from conversations" not in sql_lower:
            return False
            
        # Check content column
        has_content = "content" in sql_lower.split("where")[0] if "where" in sql_lower else "content" in sql_lower
        if has_content and not allow_content:
            return False
            
        return True
    
    def _build_system_prompt(self, date_context: Dict[str, Any], default_today_query: str) -> str:
        """
        Build a system prompt for SQL query generation.
        
        Args:
            date_context: Dictionary with current date information
            default_today_query: The default query for today's messages
            
        Returns:
            Formatted system prompt text
        """
        current_date = date_context["current_date"]
        current_day = date_context["current_day"]
        current_month = date_context["current_month"]
        current_year = date_context["current_year"]
        current_timestamp = date_context["current_timestamp"]
        
        return f"""You are a specialized SQL query generator for retrieving conversation records from a database.
        Your task is to convert user messages into precise SQL queries for a conversations database.

        TODAY'S DATE: {current_date} ({current_day}, {current_month} {current_year})
        CURRENT UNIX TIMESTAMP: {current_timestamp}

        DATABASE SCHEMA:
        - Table name: conversations
        - Columns: timestamp (REAL, unix timestamp), role (TEXT, either 'user' or 'assistant'), content (TEXT, message content)

        CRITICAL INSTRUCTIONS:
        1. Look for ANY time references in the user's message (today, yesterday, last week, May 10, etc.)
        2. If NO time references are found in the message, ALWAYS return EXACTLY this query:
           {default_today_query}
        3. If time references ARE found, generate a time-specific query following these rules:
           - Use "SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations"
           - Include WHERE clauses to filter by the appropriate time range
           - Use ORDER BY timestamp DESC LIMIT 10

        IMPORTANT:
        - Your output must be ONLY the SQL query with NO additional text
        - Do not include explanations, comments, or markdown in your response
        - When there are no time references, default to today's query EXACTLY as provided
        - NEVER modify the default today query's format - it must be used exactly as shown
        - ALWAYS include the content column in all queries
        - ALWAYS use '+7 hours' in the datetime function to use GMT+7 timezone

        EXAMPLES:

        User message: "What do you know about climate change?"
        SQL (no time reference): {default_today_query}

        User message: "What did we talk about yesterday?"
        SQL (has time reference): SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations WHERE timestamp >= {current_timestamp - 86400} AND timestamp < {current_timestamp - 86400 + 86399} ORDER BY timestamp DESC LIMIT 10

        User message: "Tell me what I asked about in May"
        SQL (has time reference): SELECT datetime(timestamp, 'unixepoch', '+7 hours') as datetime, role, content FROM conversations WHERE timestamp >= strftime('%s', '2025-05-01 00:00:00') AND timestamp < strftime('%s', '2025-06-01 00:00:00') ORDER BY timestamp DESC LIMIT 10"""
                
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        This method is kept for backward compatibility but now just calls generate_sql_query
        """
        return self.generate_sql_query(prompt)