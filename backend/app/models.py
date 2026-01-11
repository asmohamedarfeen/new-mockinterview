"""
Pydantic models for WebSocket messages and API responses.

This module defines all the data structures used for communication between
the frontend and backend via WebSocket. Pydantic provides:
- Automatic data validation
- Type checking
- JSON serialization/deserialization
- Clear error messages for invalid data

All messages follow a consistent structure with:
- type: Identifies the message type
- interview_id: Links message to specific interview session
- timestamp: When the message was created
- Additional fields specific to each message type
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class InterviewState(str, Enum):
    """
    Interview state machine states.
    
    The interview follows a finite state machine pattern where each state
    represents a specific phase of the interview process. This ensures
    the interview flows in a predictable, controlled manner.
    
    State Flow:
    AI_ASKING -> AI_SPEAKING -> WAITING_FOR_USER -> USER_SPEAKING ->
    SILENCE_DETECTED -> PROCESSING_WITH_GEMINI -> NEXT_QUESTION -> (loop)
    OR -> INTERVIEW_ENDED
    
    States:
        AI_ASKING: Initial state, preparing to ask a question
        AI_SPEAKING: AI is currently speaking the question (TTS in progress)
        WAITING_FOR_USER: Waiting for user to start speaking
        USER_SPEAKING: User is currently speaking (STT active)
        SILENCE_DETECTED: User stopped speaking, processing transcript
        PROCESSING_WITH_GEMINI: Backend is processing answer with Gemini API
        NEXT_QUESTION: Ready to ask next question
        INTERVIEW_ENDED: Interview is complete, showing feedback
    """
    AI_ASKING = "AI_ASKING"
    AI_SPEAKING = "AI_SPEAKING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    USER_SPEAKING = "USER_SPEAKING"
    SILENCE_DETECTED = "SILENCE_DETECTED"
    PROCESSING_WITH_GEMINI = "PROCESSING_WITH_GEMINI"
    NEXT_QUESTION = "NEXT_QUESTION"
    INTERVIEW_ENDED = "INTERVIEW_ENDED"


class MessageType(str, Enum):
    """
    WebSocket message types.
    
    Each message sent over WebSocket has a type field that identifies
    what kind of message it is. This allows the receiver to know how
    to process the message.
    
    Types:
        USER_TRANSCRIPT: User's speech converted to text
        AI_QUESTION: AI interviewer's question
        INTERVIEW_STATE: State change notification
        INTERVIEW_END: Interview completion with feedback
        ERROR: Error occurred, contains error details
        CONNECTION_ACK: WebSocket connection established
    """
    USER_TRANSCRIPT = "USER_TRANSCRIPT"
    AI_QUESTION = "AI_QUESTION"
    INTERVIEW_STATE = "INTERVIEW_STATE"
    INTERVIEW_END = "INTERVIEW_END"
    ERROR = "ERROR"
    CONNECTION_ACK = "CONNECTION_ACK"


class UserTranscriptMessage(BaseModel):
    """
    Message sent from client when user finishes speaking.
    
    This message is sent after:
    1. User speaks into microphone
    2. Speech recognition converts speech to text
    3. Silence is detected (user stopped speaking)
    4. Final transcript is extracted
    
    The transcript is then sent to the backend for processing by Gemini.
    
    Fields:
        type: Always USER_TRANSCRIPT
        interview_id: Which interview session this belongs to
        transcript: The actual text of what the user said
        timestamp: When the message was created (Unix timestamp)
    """
    type: MessageType = MessageType.USER_TRANSCRIPT
    interview_id: str  # Unique identifier for the interview session
    transcript: str = Field(..., min_length=1, description="User's speech transcript")  # Must not be empty
    timestamp: float  # Unix timestamp (seconds since epoch)


class AIQuestionMessage(BaseModel):
    """
    Message sent from server with AI interviewer's question.
    
    This message is sent when:
    1. Interview starts (greeting/first question)
    2. After processing user's answer (next question)
    
    The frontend receives this and uses text-to-speech to speak it aloud.
    
    Fields:
        type: Always AI_QUESTION
        interview_id: Which interview session this belongs to
        question: The question text from Gemini
        timestamp: When the question was generated
    """
    type: MessageType = MessageType.AI_QUESTION
    interview_id: str
    question: str  # The actual question text from Gemini AI
    timestamp: float


class InterviewStateMessage(BaseModel):
    """
    Message sent from server to update client about interview state.
    
    This keeps the frontend synchronized with the backend's state machine.
    The frontend uses this to:
    - Show appropriate UI indicators (e.g., "AI Speaking...", "Listening...")
    - Enable/disable controls based on current state
    - Trigger state-specific actions (e.g., start mic when WAITING_FOR_USER)
    
    Fields:
        type: Always INTERVIEW_STATE
        interview_id: Which interview session this belongs to
        state: The new state from InterviewState enum
        timestamp: When the state change occurred
    """
    type: MessageType = MessageType.INTERVIEW_STATE
    interview_id: str
    state: InterviewState  # One of the states from InterviewState enum
    timestamp: float


class InterviewEndMessage(BaseModel):
    """
    Message sent when interview is completed.
    
    This is sent when:
    1. Gemini determines the interview should end (after sufficient questions)
    2. User manually ends the interview
    3. An error occurs that prevents continuation
    
    Contains the final feedback and score for the candidate.
    
    Fields:
        type: Always INTERVIEW_END
        interview_id: Which interview session this belongs to
        feedback: Comprehensive feedback text from Gemini
        score: Numerical score from 0-100 (optional)
        summary: Summary of the interview (optional)
        timestamp: When the interview ended
    """
    type: MessageType = MessageType.INTERVIEW_END
    interview_id: str
    feedback: str  # Detailed feedback from the AI interviewer
    score: Optional[float] = Field(None, ge=0, le=100, description="Interview score out of 100")  # 0-100 range
    summary: Optional[str] = None  # Optional summary of the interview
    timestamp: float


class ErrorMessage(BaseModel):
    """
    Error message sent from server.
    
    This is sent when an error occurs during the interview process.
    Common errors:
    - Invalid API key
    - Gemini API failure
    - Network issues
    - Invalid message format
    
    The frontend displays this error to the user.
    
    Fields:
        type: Always ERROR
        interview_id: Which interview session (optional, may be None for connection errors)
        error: Human-readable error message
        code: Machine-readable error code (optional, for programmatic handling)
        timestamp: When the error occurred
    """
    type: MessageType = MessageType.ERROR
    interview_id: Optional[str] = None  # May be None if error occurs before session creation
    error: str  # Human-readable error description
    code: Optional[str] = None  # Error code like "INIT_ERROR", "PROCESSING_ERROR", etc.
    timestamp: float


class ConnectionAckMessage(BaseModel):
    """
    Connection acknowledgment message.
    
    This is the first message sent after a WebSocket connection is established.
    It confirms to the client that:
    1. The connection was successful
    2. The server received the interview_id
    3. The server is ready to proceed
    
    Fields:
        type: Always CONNECTION_ACK
        interview_id: The interview ID that was connected
        message: Confirmation message (default: "Connected successfully")
        timestamp: When the connection was acknowledged
    """
    type: MessageType = MessageType.CONNECTION_ACK
    interview_id: str
    message: str = "Connected successfully"  # Default confirmation message
    timestamp: float
