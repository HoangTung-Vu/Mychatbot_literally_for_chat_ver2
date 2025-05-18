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
   cd my_ai2
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

4. Create a `.env` file with the following content:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ENVIRONMENT=development
   ```

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

### Testing

Currently, there is no test suite. This is an area for future development.

## License

[Choose an appropriate license for your project]

## Contact

[Your contact information]