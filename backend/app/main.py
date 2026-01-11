"""
FastAPI application with WebSocket support for virtual interview room.

This is the main entry point for the backend server. It sets up:
- FastAPI application with CORS middleware
- WebSocket endpoint for real-time interview communication
- Health check endpoints for monitoring
- Environment variable loading

The server handles WebSocket connections for interview sessions where:
- Clients connect via WebSocket
- AI interviewer questions are sent to clients
- User transcripts are received from clients
- Gemini API processes responses and generates next questions
"""

import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .websocket_manager import handle_websocket
from .models import ErrorMessage
import time

# Load environment variables from .env file
# This allows us to configure the app without hardcoding values
# Required variables: GEMINI_API_KEY, PORT, CORS_ORIGINS
load_dotenv()

# Configure logging for the application
# This helps with debugging and monitoring in production
# Logs will show timestamps, logger name, level, and message
logging.basicConfig(
    level=logging.INFO,  # Log level: INFO shows important events, DEBUG shows everything
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
# FastAPI is a modern Python web framework for building APIs
# It provides automatic API documentation, type validation, and async support
app = FastAPI(
    title="Virtual AI Interview Room API",
    description="Backend API for AI-powered virtual interview room",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the frontend (running on a different port) to make requests to the backend
# Without CORS, browsers block requests from different origins for security
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # List of allowed frontend URLs
    allow_credentials=True,  # Allow cookies/credentials in requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    
    This is a simple GET endpoint that returns API metadata.
    Useful for checking if the server is running.
    
    Returns:
        dict: API name, version, and status
    """
    return {
        "message": "Virtual AI Interview Room API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    This endpoint is used by:
    - Monitoring systems to check if the server is alive
    - Load balancers to determine if the server can handle traffic
    - CI/CD pipelines to verify deployment success
    
    Returns:
        dict: Health status and current timestamp
    """
    return {
        "status": "healthy",
        "timestamp": time.time()  # Unix timestamp for when the check was performed
    }


@app.websocket("/ws/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: str):
    """
    WebSocket endpoint for interview sessions.
    
    This endpoint establishes a persistent, bidirectional connection between
    the client and server. Unlike HTTP requests which are request-response,
    WebSockets allow real-time communication where either side can send messages.
    
    Flow:
    1. Client connects to this endpoint with a unique interview_id
    2. Server accepts the connection and sends acknowledgment
    3. Server initializes Gemini conversation and sends greeting
    4. Client sends user transcripts when they speak
    5. Server processes with Gemini and sends next question
    6. This continues until interview ends
    
    Args:
        websocket: The WebSocket connection object from FastAPI
        interview_id: Unique identifier for this interview session
                     Format: "interview-{timestamp}-{random}"
    
    Note:
        Each interview gets its own WebSocket connection. Multiple interviews
        can run simultaneously with different interview_ids.
    """
    # Delegate WebSocket handling to the websocket_manager module
    # This keeps the main.py file clean and separates concerns
    await handle_websocket(websocket, interview_id)


# This block runs only when the file is executed directly (not imported)
# It allows running the server with: python -m app.main
if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))
    # Start the ASGI server (uvicorn is the ASGI server implementation)
    # host="0.0.0.0" means listen on all network interfaces (accessible from other machines)
    uvicorn.run(app, host="0.0.0.0", port=port)
