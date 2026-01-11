"""
Interview state machine for managing interview flow.

This module implements a finite state machine (FSM) to manage the interview
lifecycle. A state machine ensures that interviews follow a predictable,
controlled flow and prevents invalid state transitions.

Key Concepts:
- Each interview session has a current state
- States can only transition to specific other states (enforced)
- State transitions are validated before being applied
- Multiple interview sessions can run simultaneously

The state machine prevents issues like:
- Starting speech recognition while AI is still speaking
- Processing answers before user has finished speaking
- Sending questions before previous question is complete
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime
from .models import InterviewState


class InterviewSession:
    """
    Manages state and context for a single interview session.
    
    Each interview gets its own InterviewSession instance that tracks:
    - Current state in the interview flow
    - Conversation history (for context)
    - Question count (for interview length tracking)
    - Creation timestamp
    
    This class enforces valid state transitions to ensure the interview
    flows correctly from start to finish.
    """
    
    def __init__(self, interview_id: str):
        """
        Initialize a new interview session.
        
        Args:
            interview_id: Unique identifier for this interview session
        """
        self.interview_id = interview_id  # Unique ID for this interview
        self.state = InterviewState.AI_ASKING  # Start in initial state
        self.created_at = datetime.now()  # When this session was created
        self.conversation_history: list = []  # Store all messages for context
        self.question_count = 0  # Track how many questions have been asked
        
    def transition_to(self, new_state: InterviewState) -> bool:
        """
        Transition to a new state if the transition is valid.
        
        This method enforces the state machine rules. Not all state transitions
        are allowed. For example, you can't go from USER_SPEAKING directly to
        AI_SPEAKING - you must go through SILENCE_DETECTED and PROCESSING first.
        
        Valid transitions:
        - AI_ASKING -> AI_SPEAKING or PROCESSING_WITH_GEMINI
        - AI_SPEAKING -> WAITING_FOR_USER
        - WAITING_FOR_USER -> USER_SPEAKING
        - USER_SPEAKING -> SILENCE_DETECTED
        - SILENCE_DETECTED -> PROCESSING_WITH_GEMINI
        - PROCESSING_WITH_GEMINI -> NEXT_QUESTION or INTERVIEW_ENDED
        - NEXT_QUESTION -> AI_SPEAKING (loops back)
        - Any state -> INTERVIEW_ENDED (can end from anywhere)
        
        Args:
            new_state: The state to transition to
            
        Returns:
            bool: True if transition was successful, False if invalid
        """
        # Define valid transitions from each state
        # This dictionary maps each state to a list of states it can transition to
        valid_transitions = {
            InterviewState.AI_ASKING: [
                InterviewState.AI_SPEAKING,  # Can start speaking
                InterviewState.PROCESSING_WITH_GEMINI  # Or process if question already exists
            ],
            InterviewState.AI_SPEAKING: [InterviewState.WAITING_FOR_USER],  # After speaking, wait for user
            InterviewState.WAITING_FOR_USER: [InterviewState.USER_SPEAKING],  # User starts speaking
            InterviewState.USER_SPEAKING: [InterviewState.SILENCE_DETECTED],  # User stops speaking
            InterviewState.SILENCE_DETECTED: [InterviewState.PROCESSING_WITH_GEMINI],  # Process the answer
            InterviewState.PROCESSING_WITH_GEMINI: [
                InterviewState.NEXT_QUESTION,  # Continue with next question
                InterviewState.INTERVIEW_ENDED  # Or end the interview
            ],
            InterviewState.NEXT_QUESTION: [InterviewState.AI_SPEAKING],  # Loop back to speaking
        }
        
        # INTERVIEW_ENDED is a special state - can be reached from any state
        # This allows graceful termination even if something goes wrong
        if new_state == InterviewState.INTERVIEW_ENDED:
            self.state = new_state
            return True
            
        # Check if the requested transition is valid
        allowed = valid_transitions.get(self.state, [])
        if new_state in allowed:
            self.state = new_state
            return True
        # Invalid transition - return False and don't change state
        return False
    
    def add_to_history(self, role: str, content: str):
        """
        Add a message to the conversation history.
        
        This maintains a record of all messages in the interview for:
        - Context when generating next questions
        - Debugging and logging
        - Potential replay/analysis
        
        Args:
            role: "user" or "assistant" (AI)
            content: The message text
        """
        self.conversation_history.append({
            "role": role,  # "user" or "assistant"
            "content": content,  # The actual message text
            "timestamp": datetime.now().isoformat()  # ISO format timestamp
        })
    
    def increment_question_count(self):
        """
        Increment the question counter.
        
        This tracks how many questions have been asked. Can be used to:
        - Limit interview length
        - Provide progress indicators
        - Generate statistics
        """
        self.question_count += 1


class InterviewStateManager:
    """
    Manages multiple interview sessions.
    
    This is a singleton-like manager that keeps track of all active
    interview sessions. Since multiple users can have interviews running
    simultaneously, we need to manage multiple sessions.
    
    Each session is identified by its interview_id, which is unique.
    """
    
    def __init__(self):
        """
        Initialize the state manager.
        
        Creates an empty dictionary to store interview sessions.
        Sessions are stored in memory (not persisted to database).
        """
        self.sessions: Dict[str, InterviewSession] = {}  # Map interview_id -> InterviewSession
    
    def create_session(self, interview_id: str) -> InterviewSession:
        """
        Create a new interview session.
        
        Args:
            interview_id: Unique identifier for the new session
            
        Returns:
            InterviewSession: The newly created session instance
        """
        session = InterviewSession(interview_id)
        self.sessions[interview_id] = session  # Store in dictionary
        return session
    
    def get_session(self, interview_id: str) -> Optional[InterviewSession]:
        """
        Get an existing interview session.
        
        Args:
            interview_id: The ID of the session to retrieve
            
        Returns:
            InterviewSession if found, None otherwise
        """
        return self.sessions.get(interview_id)
    
    def remove_session(self, interview_id: str):
        """
        Remove an interview session.
        
        This is called when an interview ends to clean up memory.
        Important for preventing memory leaks in long-running servers.
        
        Args:
            interview_id: The ID of the session to remove
        """
        if interview_id in self.sessions:
            del self.sessions[interview_id]  # Remove from dictionary


# Global state manager instance
# This is a singleton pattern - one instance shared across the entire application
# All WebSocket handlers use this same instance to manage sessions
state_manager = InterviewStateManager()
