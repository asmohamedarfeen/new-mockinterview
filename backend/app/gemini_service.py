"""
Google Gemini API integration for AI interviewer.

This module handles all interactions with Google's Gemini AI API. It:
- Initializes conversations with the AI interviewer persona
- Processes user answers and generates follow-up questions
- Maintains conversation context across multiple exchanges
- Detects when interviews should end
- Extracts scores and feedback from AI responses

The service uses Gemini's chat API which maintains conversation context
automatically, allowing for natural, context-aware conversations.
"""

import os
import google.generativeai as genai
from typing import List, Dict, Optional


# System prompt for the AI interviewer
# This defines the AI's personality, role, and behavior
# It's sent to Gemini at the start of each interview to set the context
SYSTEM_PROMPT = """You are a senior corporate HR interviewer conducting a structured interview. Your role is to:

1. Ask one question at a time
2. Wait for the candidate's response before asking the next question
3. Adapt your next question based on the candidate's previous answer
4. Be concise, professional, and realistic
5. Ask relevant follow-up questions when appropriate
6. Maintain a professional but friendly tone
7. When you feel the interview is complete (typically after 5-8 questions), provide a comprehensive feedback summary including:
   - Overall assessment
   - Strengths observed
   - Areas for improvement
   - A numerical score out of 100
   - End with "INTERVIEW_END" to signal completion

Start by greeting the candidate warmly and asking the first question."""


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    
    This class encapsulates all Gemini API interactions. It manages:
    - API configuration and authentication
    - Conversation sessions (one per interview)
    - Conversation history tracking
    - Chat session management for context preservation
    
    The service uses lazy initialization - it only creates the Gemini client
    when first needed, not at import time. This prevents errors if the API
    key is missing during module import.
    """
    
    def __init__(self):
        """
        Initialize the Gemini service.
        
        Reads the API key from environment variables and configures
        the Gemini client. Raises an error if the API key is missing.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not set in environment
        """
        # Get API key from environment variable
        # This should be set in the .env file or system environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Configure the Gemini API client with the API key
        genai.configure(api_key=api_key)
        
        # Create a GenerativeModel instance using 'gemini-pro'
        # This is the model that will generate responses
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Store conversation history for each interview
        # Key: interview_id, Value: List of message dicts
        # Used for tracking and debugging
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Store active chat sessions for each interview
        # Key: interview_id, Value: Chat session object
        # Chat sessions maintain context automatically
        self.chat_sessions: Dict[str, any] = {}  # Store chat sessions for context
    
    def initialize_conversation(self, interview_id: str) -> str:
        """
        Initialize a new interview conversation and get the greeting.
        
        This is called when an interview starts. It:
        1. Sends the system prompt to Gemini
        2. Gets the initial greeting/question
        3. Sets up the chat session for context preservation
        4. Stores the conversation history
        
        Args:
            interview_id: Unique identifier for this interview
            
        Returns:
            str: The greeting/question text from Gemini
            
        Raises:
            Exception: If Gemini API call fails (e.g., invalid API key, network error)
        """
        # Combine system prompt with instruction to start the interview
        initial_prompt = SYSTEM_PROMPT + "\n\nPlease greet the candidate and ask your first question."
        
        try:
            # Generate the initial greeting/question using Gemini
            # This is a one-time generation, not a chat session yet
            response = self.model.generate_content(initial_prompt)
            greeting = response.text.strip()  # Remove leading/trailing whitespace
            
            # Initialize conversation history for this interview
            # This tracks all messages for debugging and potential replay
            self.conversations[interview_id] = [
                {"role": "system", "content": SYSTEM_PROMPT},  # System instructions
                {"role": "assistant", "content": greeting}  # First AI message
            ]
            
            # Initialize chat session for context preservation
            # Chat sessions maintain conversation history automatically
            # This allows Gemini to remember previous exchanges
            chat = self.model.start_chat(history=[])
            
            # Send the initial prompt to the chat session
            # This sets up the context for future messages
            chat.send_message(SYSTEM_PROMPT + "\n\nPlease greet the candidate and ask your first question.")
            
            # Store the chat session so we can continue the conversation
            self.chat_sessions[interview_id] = chat
            
            return greeting
        except Exception as e:
            # Wrap the error with more context
            raise Exception(f"Failed to initialize Gemini conversation: {str(e)}")
    
    def process_answer(self, interview_id: str, user_answer: str) -> Dict:
        """
        Process user's answer and get next question or end signal.
        
        This is called after the user finishes speaking. It:
        1. Adds the user's answer to conversation history
        2. Sends it to Gemini with full conversation context
        3. Gets the next question or end signal
        4. Extracts score if interview is ending
        5. Updates conversation history
        
        Args:
            interview_id: Which interview this answer belongs to
            user_answer: The text transcript of what the user said
            
        Returns:
            Dict with keys:
            - 'type': 'question' (continue) or 'end' (interview complete)
            - 'content': Question text or feedback text
            - 'score': Optional numerical score (0-100) if ending
            - 'summary': Optional summary if ending
            
        Raises:
            ValueError: If interview_id doesn't exist
            Exception: If Gemini API call fails
        """
        # Verify the interview was initialized
        if interview_id not in self.conversations:
            raise ValueError(f"Interview {interview_id} not initialized")
        
        # Add user's answer to conversation history
        # This is for tracking purposes
        self.conversations[interview_id].append({
            "role": "user",  # Message from the user
            "content": user_answer  # What they said
        })
        
        try:
            # Get or create chat session for this interview
            # Chat sessions maintain context automatically
            if interview_id not in self.chat_sessions:
                # This shouldn't happen, but create if needed as fallback
                chat = self.model.start_chat(history=[])
                self.chat_sessions[interview_id] = chat
            
            # Get the chat session for this interview
            chat = self.chat_sessions[interview_id]
            
            # Send user's answer to the chat session
            # The chat session automatically includes previous conversation context
            # This allows Gemini to ask relevant follow-up questions
            response = chat.send_message(user_answer)
            
            # Extract the response text
            response_text = response.text.strip()
            
            # Check if interview should end
            # Ends if:
            # 1. Gemini explicitly says "INTERVIEW_END"
            # 2. Conversation has reached 20 messages (safety limit)
            if "INTERVIEW_END" in response_text.upper() or len(self.conversations[interview_id]) >= 20:
                # Extract feedback text (remove the INTERVIEW_END marker)
                feedback = response_text.replace("INTERVIEW_END", "").strip()
                
                # Try to extract score from feedback
                # Gemini might say "Score: 85" or "85/100" or similar
                score = None
                summary = None
                
                # Look for score pattern using regex
                # Matches patterns like "Score: 85", "85/100", "85%", etc.
                import re
                score_match = re.search(r'(\d+)\s*(?:out of 100|/100|%)', feedback, re.IGNORECASE)
                if score_match:
                    score = float(score_match.group(1))
                
                # If no explicit score found, try to find any number between 0-100
                # This is a fallback in case Gemini formats the score differently
                if score is None:
                    score_match = re.search(r'\b([0-9]|[1-9][0-9]|100)\b', feedback)
                    if score_match:
                        potential_score = float(score_match.group(1))
                        if 0 <= potential_score <= 100:  # Validate it's in valid range
                            score = potential_score
                
                # If still no score found, generate a default based on conversation length
                # Longer conversations (more questions answered) get higher scores
                # This is a fallback to ensure we always have a score
                if score is None:
                    score = min(70 + len(self.conversations[interview_id]) * 2, 95)
                
                # Return end message with feedback and score
                return {
                    "type": "end",  # Signal that interview is ending
                    "content": feedback,  # The feedback text
                    "score": score,  # Numerical score
                    "summary": feedback  # Summary (same as feedback in this case)
                }
            
            # Interview continues - add assistant response to history
            self.conversations[interview_id].append({
                "role": "assistant",  # Message from AI
                "content": response_text  # The next question
            })
            
            # Return next question
            return {
                "type": "question",  # Signal that interview continues
                "content": response_text  # The next question text
            }
            
        except Exception as e:
            # Wrap error with context
            raise Exception(f"Failed to process answer with Gemini: {str(e)}")
    
    def cleanup(self, interview_id: str):
        """
        Clean up conversation history and chat session for an interview.
        
        This is called when an interview ends to free up memory.
        Important for preventing memory leaks in long-running servers.
        
        Args:
            interview_id: The interview to clean up
        """
        # Remove conversation history
        if interview_id in self.conversations:
            del self.conversations[interview_id]
        
        # Remove chat session
        if interview_id in self.chat_sessions:
            del self.chat_sessions[interview_id]


# Global Gemini service instance (lazy initialization)
# We use lazy initialization to avoid errors if API key is missing at import time
# The service is only created when first needed
_gemini_service: Optional[GeminiService] = None

def get_gemini_service() -> GeminiService:
    """
    Get or create the global Gemini service instance.
    
    This implements the singleton pattern - there's only one GeminiService
    instance shared across the entire application. This is efficient because:
    - We only configure the API once
    - We reuse the same model instance
    - Memory usage is minimized
    
    Returns:
        GeminiService: The global service instance
        
    Raises:
        ValueError: If GEMINI_API_KEY is not set (raised by GeminiService.__init__)
    """
    global _gemini_service
    # Create service only if it doesn't exist yet
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
