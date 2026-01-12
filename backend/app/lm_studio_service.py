"""
LM Studio API integration for AI interviewer.

This module handles all interactions with LM Studio's local LLM API. LM Studio
provides an OpenAI-compatible API endpoint that runs locally, allowing for
privacy-focused AI interviews without external API calls.

This service:
- Initializes conversations with the AI interviewer persona
- Processes user answers and generates follow-up questions
- Maintains conversation context across multiple exchanges
- Detects when interviews should end
- Extracts scores and feedback from AI responses

The service uses HTTP requests to communicate with LM Studio's OpenAI-compatible
API endpoint, typically running on localhost:1234.
"""

import os
import logging
import re
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# System prompt for the AI interviewer
# This defines the AI's personality, role, and behavior
# It's sent to LM Studio at the start of each interview to set the context
# This is the same prompt used for Gemini to ensure consistent behavior
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


class LMStudioService:
    """
    Service for interacting with LM Studio's OpenAI-compatible API.
    
    This class encapsulates all LM Studio API interactions. It manages:
    - HTTP client configuration and connection to LM Studio
    - Model name detection and configuration
    - Conversation sessions (one per interview)
    - Conversation history tracking for context preservation
    
    The service uses OpenAI-compatible API format, which means it sends
    messages in a chat format with role-based messages (system, user, assistant).
    """
    
    def __init__(self):
        """
        Initialize the LM Studio service.
        
        Reads configuration from environment variables:
        - LM_STUDIO_BASE_URL: Base URL for LM Studio API (default: http://localhost:1234)
        - LM_STUDIO_MODEL: Explicit model name (optional, will auto-detect if not set)
        
        Raises:
            ValueError: If LM Studio base URL is invalid
            ConnectionError: If LM Studio is not reachable
        """
        # Get base URL from environment variable
        # Default to localhost:1234 which is LM Studio's default port
        self.base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234").rstrip("/")
        
        # Validate base URL format
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid LM_STUDIO_BASE_URL: {self.base_url}. Must start with http:// or https://")
        
        # Create HTTP session with retry strategy
        # This helps handle temporary connection issues gracefully
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Maximum 2 retries
            backoff_factor=0.5,  # Wait 0.5s, 1s between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["POST", "GET"]  # Only retry POST and GET requests
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set timeout for requests (5 seconds for connection, 30 seconds for response)
        # This prevents hanging if LM Studio is slow or unresponsive
        self.timeout = (5, 30)
        
        # Try to get model name from environment variable
        # If not set, we'll auto-detect it
        self.model_name = os.getenv("LM_STUDIO_MODEL")
        
        # Auto-detect model name if not explicitly set
        if not self.model_name:
            try:
                self.model_name = self._detect_model()
                logger.info(f"Auto-detected LM Studio model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to auto-detect model: {e}. Using default.")
                # Use a default model name (LM Studio typically uses the loaded model name)
                # This might need adjustment based on actual LM Studio behavior
                self.model_name = "local-model"
        
        # Store conversation history for each interview
        # Key: interview_id, Value: List of message dicts with role and content
        # Format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]
        # This maintains context across multiple API calls
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Test connection to LM Studio (non-blocking - will fail gracefully if not available)
        try:
            self._test_connection()
            logger.info(f"LM Studio service initialized successfully at {self.base_url} with model {self.model_name}")
        except Exception as e:
            logger.warning(f"LM Studio connection test failed at {self.base_url}: {e}")
            logger.warning("LM Studio service will be available but may fail on first use. Make sure LM Studio is running.")
            # Don't raise - allow service to be created, but it will fail on first API call
            # This allows the fallback mechanism to work properly
    
    def _detect_model(self) -> str:
        """
        Auto-detect available model from LM Studio.
        
        Queries the /v1/models endpoint to get available models and prioritizes
        instruction-tuned models (especially llama-3-8b-instruct) for better
        interview performance. Falls back to first available model if no
        instruction-tuned model is found.
        
        Returns:
            str: The model name to use
            
        Raises:
            Exception: If model detection fails
        """
        try:
            # Query LM Studio's models endpoint (OpenAI-compatible)
            response = self.session.get(
                f"{self.base_url}/v1/models",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response (OpenAI-compatible format)
            data = response.json()
            models = data.get("data", [])
            
            if not models:
                raise Exception("No models found in LM Studio")
            
            # Log all available models for debugging
            model_ids = [m.get("id") for m in models]
            logger.info(f"Available models in LM Studio: {model_ids}")
            
            # Priority order for model selection:
            # 1. llama-3-8b-instruct (best for interviews)
            # 2. Any other instruction-tuned model (instruct in name)
            # 3. First available model as fallback
            
            # First, try to find llama-3-8b-instruct specifically
            for model in models:
                model_id = model.get("id", "")
                if "llama-3-8b-instruct" in model_id.lower():
                    logger.info(f"Selected model: {model_id} (llama-3-8b-instruct)")
                    return model_id
            
            # If not found, try any instruction-tuned model
            for model in models:
                model_id = model.get("id", "")
                if "instruct" in model_id.lower():
                    logger.info(f"Selected model: {model_id} (instruction-tuned)")
                    return model_id
            
            # Fallback to first available model
            model_id = models[0].get("id", "local-model")
            logger.info(f"Selected model: {model_id} (first available)")
            return model_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query models endpoint: {str(e)}")
    
    def _test_connection(self):
        """
        Test connection to LM Studio by making a simple request.
        
        This verifies that LM Studio is running and accessible before
        attempting to use it for interviews.
        
        Raises:
            ConnectionError: If LM Studio is not reachable
        """
        try:
            # Try to get models list as a connection test
            response = self.session.get(
                f"{self.base_url}/v1/models",
                timeout=(5, 10)  # Shorter timeout for connection test
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to LM Studio at {self.base_url}. Is it running?")
        except requests.exceptions.Timeout:
            raise ConnectionError(f"LM Studio at {self.base_url} did not respond in time.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error connecting to LM Studio: {str(e)}")
    
    def initialize_conversation(self, interview_id: str) -> str:
        """
        Initialize a new interview conversation and get the greeting.
        
        This is called when an interview starts. It:
        1. Sends the system prompt to LM Studio
        2. Gets the initial greeting/question
        3. Stores the conversation history
        
        Args:
            interview_id: Unique identifier for this interview
            
        Returns:
            str: The greeting/question text from LM Studio
            
        Raises:
            Exception: If LM Studio API call fails (e.g., connection error, timeout)
        """
        # Prepare the initial messages
        # OpenAI-compatible format requires messages array with role and content
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Please greet the candidate and ask your first question."}
        ]
        
        try:
            # Make API call to LM Studio
            # Using OpenAI-compatible endpoint format
            # Using max_tokens: -1 for unlimited tokens (LM Studio supports this)
            # This matches the curl command format provided by the user
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.7,  # Moderate creativity
                    "max_tokens": -1,  # Unlimited tokens (LM Studio supports this)
                    "stream": False  # We want complete response, not streaming
                },
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response (OpenAI-compatible format)
            data = response.json()
            
            # Extract the greeting text from the response
            # OpenAI format: choices[0].message.content
            if "choices" not in data or not data["choices"]:
                raise Exception("Invalid response format from LM Studio: no choices")
            
            greeting = data["choices"][0]["message"]["content"].strip()
            
            # Initialize conversation history for this interview
            # This tracks all messages for context in future calls
            self.conversations[interview_id] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Please greet the candidate and ask your first question."},
                {"role": "assistant", "content": greeting}
            ]
            
            return greeting
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Failed to connect to LM Studio: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"LM Studio request timed out: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to initialize LM Studio conversation: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response format from LM Studio: {str(e)}")
    
    def process_answer(self, interview_id: str, user_answer: str) -> Dict:
        """
        Process user's answer and get next question or end signal.
        
        This is called after the user finishes speaking. It:
        1. Adds the user's answer to conversation history
        2. Sends it to LM Studio with full conversation context
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
            Exception: If LM Studio API call fails
        """
        # Verify the interview was initialized
        if interview_id not in self.conversations:
            raise ValueError(f"Interview {interview_id} not initialized")
        
        # Add user's answer to conversation history
        # This maintains context for the next API call
        self.conversations[interview_id].append({
            "role": "user",
            "content": user_answer
        })
        
        try:
            # Prepare messages for API call
            # Include full conversation history for context
            # LM Studio will use this to generate contextually relevant responses
            messages = self.conversations[interview_id].copy()
            
            # Make API call to LM Studio
            # Using max_tokens: -1 for unlimited tokens (LM Studio supports this)
            # This matches the curl command format provided by the user
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": -1,  # Unlimited tokens (LM Studio supports this)
                    "stream": False
                },
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise Exception("Invalid response format from LM Studio: no choices")
            
            # Extract response text
            response_text = data["choices"][0]["message"]["content"].strip()
            
            # Check if interview should end
            # Ends if:
            # 1. LM Studio explicitly says "INTERVIEW_END"
            # 2. Conversation has reached 20 messages (safety limit)
            if "INTERVIEW_END" in response_text.upper() or len(self.conversations[interview_id]) >= 20:
                # Extract feedback text (remove the INTERVIEW_END marker)
                feedback = response_text.replace("INTERVIEW_END", "").strip()
                
                # Try to extract score from feedback
                # LM Studio might say "Score: 85" or "85/100" or similar
                score = None
                summary = None
                
                # Look for score pattern using regex
                # Matches patterns like "Score: 85", "85/100", "85%", etc.
                score_match = re.search(r'(\d+)\s*(?:out of 100|/100|%)', feedback, re.IGNORECASE)
                if score_match:
                    score = float(score_match.group(1))
                
                # If no explicit score found, try to find any number between 0-100
                # This is a fallback in case LM Studio formats the score differently
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
                
                # Add assistant response to history before returning
                self.conversations[interview_id].append({
                    "role": "assistant",
                    "content": response_text
                })
                
                # Return end message with feedback and score
                return {
                    "type": "end",  # Signal that interview is ending
                    "content": feedback,  # The feedback text
                    "score": score,  # Numerical score
                    "summary": feedback  # Summary (same as feedback in this case)
                }
            
            # Interview continues - add assistant response to history
            self.conversations[interview_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            # Return next question
            return {
                "type": "question",  # Signal that interview continues
                "content": response_text  # The next question text
            }
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Failed to connect to LM Studio: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"LM Studio request timed out: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to process answer with LM Studio: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response format from LM Studio: {str(e)}")
    
    def cleanup(self, interview_id: str):
        """
        Clean up conversation history for an interview.
        
        This is called when an interview ends to free up memory.
        Important for preventing memory leaks in long-running servers.
        
        Args:
            interview_id: The interview to clean up
        """
        # Remove conversation history
        if interview_id in self.conversations:
            del self.conversations[interview_id]


# Global LM Studio service instance (lazy initialization)
# We use lazy initialization to avoid errors if LM Studio is not running at import time
# The service is only created when first needed
_lm_studio_service: Optional[LMStudioService] = None

def get_lm_studio_service() -> LMStudioService:
    """
    Get or create the global LM Studio service instance.
    
    This implements the singleton pattern - there's only one LMStudioService
    instance shared across the entire application. This is efficient because:
    - We only configure the HTTP client once
    - We reuse the same connection settings
    - Memory usage is minimized
    
    Returns:
        LMStudioService: The global service instance
        
    Raises:
        ConnectionError: If LM Studio is not reachable (raised by LMStudioService.__init__)
    """
    global _lm_studio_service
    # Create service only if it doesn't exist yet
    if _lm_studio_service is None:
        _lm_studio_service = LMStudioService()
    return _lm_studio_service
