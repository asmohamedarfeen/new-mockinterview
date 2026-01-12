"""
WebSocket connection manager for interview sessions.
"""
import json
import logging
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .models import (
    MessageType,
    UserTranscriptMessage,
    AIQuestionMessage,
    InterviewStateMessage,
    InterviewEndMessage,
    ErrorMessage,
    ConnectionAckMessage,
    InterviewState
)
from .interview_state import state_manager
from .ai_service import get_ai_service
import time

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for interview sessions."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, interview_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[interview_id] = websocket
        logger.info(f"WebSocket connected for interview: {interview_id}")
    
    def disconnect(self, interview_id: str):
        """Remove a WebSocket connection."""
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]
            logger.info(f"WebSocket disconnected for interview: {interview_id}")
    
    async def send_message(self, interview_id: str, message: dict):
        """Send a message to a specific interview session."""
        if interview_id in self.active_connections:
            try:
                websocket = self.active_connections[interview_id]
                # Check if connection is still open before sending
                if websocket.client_state.name != "CONNECTED":
                    logger.warning(f"WebSocket for {interview_id} is not connected (state: {websocket.client_state.name})")
                    self.disconnect(interview_id)
                    return
                await websocket.send_json(message)
            except Exception as e:
                # Don't log as error if connection is already closed - this is expected
                if "no close frame" not in str(e).lower() and "connection closed" not in str(e).lower():
                    logger.error(f"Error sending message to {interview_id}: {e}")
                self.disconnect(interview_id)
                # Don't raise - just log and disconnect gracefully
    
    async def send_error(self, interview_id: str, error: str, code: Optional[str] = None):
        """Send an error message."""
        error_msg = ErrorMessage(
            interview_id=interview_id,
            error=error,
            code=code,
            timestamp=time.time()
        )
        await self.send_message(interview_id, error_msg.model_dump())


# Global connection manager
connection_manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, interview_id: str):
    """
    Handle WebSocket connection for an interview session.
    
    Flow:
    1. Accept connection and send ACK
    2. Initialize interview session
    3. Get AI greeting from AI service (LM Studio or Gemini)
    4. Send greeting to client
    5. Wait for user transcripts
    6. Process with AI service
    7. Send next question or end signal
    """
    await connection_manager.connect(websocket, interview_id)
    
    try:
        # Send connection acknowledgment immediately and directly
        # This ensures the client knows the connection is established
        ack = ConnectionAckMessage(
            interview_id=interview_id,
            timestamp=time.time()
        )
        try:
            await websocket.send_json(ack.model_dump())
            logger.info(f"Connection ACK sent for interview {interview_id}")
        except Exception as e:
            logger.warning(f"Failed to send ACK to {interview_id}: {e}")
            # If we can't send ACK, the connection is likely broken
            return
        
        # Create or get interview session
        session = state_manager.get_session(interview_id)
        if not session:
            session = state_manager.create_session(interview_id)
            # Initialize AI conversation (tries LM Studio first, falls back to Gemini)
            try:
                ai_service = get_ai_service()
                greeting = ai_service.initialize_conversation(interview_id)
                
                # Transition to AI_SPEAKING state
                session.transition_to(InterviewState.AI_SPEAKING)
                
                # Send state update
                state_msg = InterviewStateMessage(
                    interview_id=interview_id,
                    state=InterviewState.AI_SPEAKING,
                    timestamp=time.time()
                )
                await connection_manager.send_message(interview_id, state_msg.model_dump())
                
                # Send greeting question
                question_msg = AIQuestionMessage(
                    interview_id=interview_id,
                    question=greeting,
                    timestamp=time.time()
                )
                await connection_manager.send_message(interview_id, question_msg.model_dump())
                
                # Transition to WAITING_FOR_USER
                session.transition_to(InterviewState.WAITING_FOR_USER)
                state_msg = InterviewStateMessage(
                    interview_id=interview_id,
                    state=InterviewState.WAITING_FOR_USER,
                    timestamp=time.time()
                )
                await connection_manager.send_message(interview_id, state_msg.model_dump())
                
            except Exception as e:
                logger.error(f"Error initializing interview {interview_id}: {e}", exc_info=True)
                error_msg = str(e)
                # Check if it's an API key issue or service unavailable
                if "API_KEY" in error_msg or "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                    error_msg = "Invalid or missing API key. Please check your backend .env file."
                elif "not available" in error_msg.lower() or "not reachable" in error_msg.lower():
                    error_msg = "AI service is not available. Please ensure LM Studio is running or Gemini API key is configured."
                
                # Send error message first
                await connection_manager.send_error(
                    interview_id,
                    error_msg,
                    "INIT_ERROR"
                )
                # Set session to ended state
                session.transition_to(InterviewState.INTERVIEW_ENDED)
                
                # Send state update
                state_msg = InterviewStateMessage(
                    interview_id=interview_id,
                    state=InterviewState.INTERVIEW_ENDED,
                    timestamp=time.time()
                )
                await connection_manager.send_message(interview_id, state_msg.model_dump())
                
                end_msg = InterviewEndMessage(
                    interview_id=interview_id,
                    feedback=f"Interview could not be started: {error_msg}",
                    score=None,
                    summary=None,
                    timestamp=time.time()
                )
                await connection_manager.send_message(interview_id, end_msg.model_dump())
                
                # Wait longer to ensure messages are sent before closing
                await asyncio.sleep(1.0)
                
                # Keep connection open briefly to allow frontend to receive messages
                # The connection will close naturally when the function returns
                return
        
        # Main message loop - only enters if initialization was successful
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == MessageType.USER_TRANSCRIPT:
                    # Handle user transcript
                    transcript_msg = UserTranscriptMessage(**data)
                    session = state_manager.get_session(interview_id)
                    
                    if not session:
                        await connection_manager.send_error(
                            interview_id,
                            "Interview session not found",
                            "SESSION_NOT_FOUND"
                        )
                        continue
                    
                    # Update state
                    session.transition_to(InterviewState.PROCESSING_WITH_GEMINI)
                    state_msg = InterviewStateMessage(
                        interview_id=interview_id,
                        state=InterviewState.PROCESSING_WITH_GEMINI,
                        timestamp=time.time()
                    )
                    await connection_manager.send_message(interview_id, state_msg.model_dump())
                    
                    # Process with AI service (LM Studio or Gemini)
                    try:
                        ai_service = get_ai_service()
                        result = ai_service.process_answer(
                            interview_id,
                            transcript_msg.transcript
                        )
                        
                        if result["type"] == "end":
                            # Interview ended
                            session.transition_to(InterviewState.INTERVIEW_ENDED)
                            
                            end_msg = InterviewEndMessage(
                                interview_id=interview_id,
                                feedback=result["content"],
                                score=result.get("score"),
                                summary=result.get("summary"),
                                timestamp=time.time()
                            )
                            await connection_manager.send_message(interview_id, end_msg.model_dump())
                            
                            # Cleanup
                            state_manager.remove_session(interview_id)
                            ai_service.cleanup(interview_id)
                            break
                        else:
                            # Next question
                            session.increment_question_count()
                            session.transition_to(InterviewState.AI_SPEAKING)
                            
                            state_msg = InterviewStateMessage(
                                interview_id=interview_id,
                                state=InterviewState.AI_SPEAKING,
                                timestamp=time.time()
                            )
                            await connection_manager.send_message(interview_id, state_msg.model_dump())
                            
                            question_msg = AIQuestionMessage(
                                interview_id=interview_id,
                                question=result["content"],
                                timestamp=time.time()
                            )
                            await connection_manager.send_message(interview_id, question_msg.model_dump())
                            
                            # Transition to WAITING_FOR_USER
                            session.transition_to(InterviewState.WAITING_FOR_USER)
                            state_msg = InterviewStateMessage(
                                interview_id=interview_id,
                                state=InterviewState.WAITING_FOR_USER,
                                timestamp=time.time()
                            )
                            await connection_manager.send_message(interview_id, state_msg.model_dump())
                            
                    except Exception as e:
                        logger.error(f"Error processing answer for {interview_id}: {e}")
                        await connection_manager.send_error(
                            interview_id,
                            f"Failed to process answer: {str(e)}",
                            "PROCESSING_ERROR"
                        )
                        # Reset to waiting state
                        session.transition_to(InterviewState.WAITING_FOR_USER)
                        state_msg = InterviewStateMessage(
                            interview_id=interview_id,
                            state=InterviewState.WAITING_FOR_USER,
                            timestamp=time.time()
                        )
                        await connection_manager.send_message(interview_id, state_msg.model_dump())
                
                else:
                    await connection_manager.send_error(
                        interview_id,
                        f"Unknown message type: {message_type}",
                        "UNKNOWN_MESSAGE_TYPE"
                    )
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for interview: {interview_id}")
                break
            except Exception as e:
                logger.error(f"Error handling message for {interview_id}: {e}")
                await connection_manager.send_error(
                    interview_id,
                    f"Error processing message: {str(e)}",
                    "MESSAGE_ERROR"
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for interview: {interview_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {interview_id}: {e}")
    finally:
        # Cleanup
        connection_manager.disconnect(interview_id)
        state_manager.remove_session(interview_id)
        try:
            ai_service = get_ai_service()
            ai_service.cleanup(interview_id)
        except:
            pass  # Ignore cleanup errors
