#!/usr/bin/env python3
"""
Run script for the Conversational AI with Hybrid Memory System.
This script starts the FastAPI application with Uvicorn.
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get host and port from environment variables or use defaults
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 8000))
reload_enabled = os.getenv("ENVIRONMENT", "development").lower() == "development"

if __name__ == "__main__":
    print(f"Starting Hybrid Memory AI server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host, 
        port=port, 
        reload=reload_enabled,
        log_level="info"
    )