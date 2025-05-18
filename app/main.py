import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.chat_router import router as chat_router
from app.services.init_db import init_all_databases

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Conversational AI with Hybrid Memory",
    description="A conversational AI system leveraging both temporal and semantic memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    """
    Serve the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    """
    Initialize resources when the application starts.
    """
    logger.info("Starting up the application")
    
    # Ensure data directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/vector_store", exist_ok=True)
    
    # Initialize databases
    if init_all_databases():
        logger.info("Databases initialized successfully")
    else:
        logger.error("Failed to initialize databases")
    
    # Log environment configuration
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Check if API key is configured
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY environment variable is not set!")
        
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources when the application shuts down.
    """
    logger.info("Shutting down the application")
    # Any cleanup code would go here