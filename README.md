# Conversational AI with Hybrid Memory

A conversational AI system leveraging both temporal and semantic memory for enhanced conversation capabilities.

![Model diagram](Model_diagram.png)

## Features

- Conversational AI integration using Gemini API
- Hybrid memory system that helps AI remember previous conversations
- Time-aware semantic memory with importance evaluation
- Automatic filtering of outdated information
- Simple and user-friendly web interface
- RESTful API built with FastAPI
- Vector storage based on ChromaDB for semantic search

## System Requirements

- Python 3.12+
- SQLite (for chat history storage)
- Gemini API key

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv myai
   source myai/bin/activate  # On Linux/Mac
   # or
   myai\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following content:
    ```
    GEMINI_API_KEY=your_gemini_api_key_here

    SQLITE_DB_PATH=./data/chat_history.db
    VECTOR_DB_PATH=./data/vector_store

    VECTOR_DB_COLLECTION_NAME=semantic_memory
    ENVIRONMENT=development
    ```
   
   You can get your Gemini API key by:
   - Visiting Google AI Studio (https://ai.google.dev/)
   - Creating or logging into your account
   - Going to "API keys" section
   - Creating a new API key or using an existing one

5. Create a system prompt file:
   Create a file named `private_main_system_prompt.txt` in the `app/services/llm/` directory. This file defines the personality and behavior of your AI assistant. You can customize it based on your preferences.

## Setting Up Gemini API

This project uses Google's Gemini API for generating AI responses. The integration works as follows:

1. The application uses your Gemini API key from the `.env` file
2. Requests are sent to Gemini's API with your custom system prompt and conversation history
3. Responses are processed through the hybrid memory system for context retention

API usage notes:
- Free tier Gemini API has rate limits (check Google AI Studio for current limits)
- Ensure your API key has access to the models used in this application
- For production use, consider upgrading to a paid tier

## Usage

1. Run the application:
   ```
   python run.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Start chatting with the AI through the web interface.

## Project Structure

```
├── app/                  # Main application code
│   ├── api/              # API endpoints
│   ├── models/           # Data definitions
│   └── services/         # Business logic and services
│       ├── llm/          # LLM services
│       └── ...
├── data/                 # Data and databases
│   └── vector_store/     # Vector store for ChromaDB
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── run.py                # Application entry point
└── requirements.txt      # List of dependencies
```

## Development

### Adding New Features

1. Implement code in the appropriate directory
2. Update APIs in `app/api/`
3. Update services in `app/services/`
4. Update the user interface if needed

### Customizing the AI Assistant

You can modify the `private_main_system_prompt.txt` file to change how the AI responds. The system prompt defines:
- The AI's personality traits
- How it should interact with users
- What information it has access to
- Any specific response patterns or behaviors

## Troubleshooting

- **API Key Issues**: Verify your Gemini API key is correctly added to the `.env` file
- **Memory Database**: If experiencing issues, try deleting the data folder and restarting
- **Dependencies**: Make sure all requirements are installed correctly

## How It Works

### Hybrid Memory Architecture

This system uses a dual-memory architecture that mimics human memory systems:

1. **Temporal Memory System**
   - Stores complete conversation history chronologically in a SQLite database
   - Allows time-based filtering and retrieval of past conversations
   - Provides conversational history context to the AI

2. **Semantic Memory System**
   - Uses ChromaDB vector database to store important information extracted from conversations
   - Embeds information for semantic similarity search
   - Captures knowledge that should persist beyond immediate conversational context

### Processing Flow

The conversation flow follows these main stages:

1. **Prompt Stage**
   - User sends a message through the web interface or API
   - The system saves the message to temporal memory
   - Temporal Agent analyzes the message for time references and generates SQL queries
   - Recent conversation history is retrieved
   - Semantic Memory is searched for relevant information

2. **Response Generation Stage**
   - All collected context is formatted and sent to the Main LLM (Gemini)
   - The LLM generates a response considering:
     - The user's current question
     - Recent conversation history
     - Time-relevant past conversations
     - Important semantic memories

3. **Save Stage**
   - The AI's response is saved to temporal memory
   - Memorize Agent extracts important information from the conversation
   - Important information is embedded and stored in semantic memory for later retrieval

### Intelligent Components

The system has specialized agents that handle different aspects:

1. **Main LLM Service** (Gemini 1.5 Pro)
   - Primary AI that generates responses to user queries
   - Integrates all context from memory systems

2. **Temporal Agent** (Gemini 1.5 Flash)
   - Analyzes user questions for time references
   - Generates SQL queries to retrieve time-relevant conversations
   - Handles queries like "What did we talk about yesterday?" or "Show me conversations from May"

3. **Memorize Agent** (Gemini 1.5 Flash)
   - Extracts and evaluates important information from conversations
   - Determines what should be stored in semantic memory
   - Ranks information by importance and relevance

### Memory Filtering

The system intelligently filters memories to provide the most relevant context:

1. **Time-based Filtering**
   - Identifies time references in queries
   - Retrieves conversations from specific time periods
   - Uses customized SQL queries for precise temporal search

2. **Relevance Filtering**
   - Compares semantic similarity between current query and stored information
   - Ranks information by relevance to current conversation
   - Prioritizes information based on contextual importance

3. **Importance Evaluation**
   - Evaluates information longevity and significance
   - Determines how long certain information should be considered relevant
   - Automatically filters out outdated or less important information

This hybrid approach creates an AI that can maintain conversational context over time while efficiently retrieving relevant information from past interactions, similar to human memory processes.

## License

None
## Contact

Vũ Minh Hoàng Tùng
minhhoangtungvu04@gmail.com
