"""
Unified AI service with automatic fallback between LM Studio and Gemini.

This module provides a unified interface for AI services, automatically trying
LM Studio first (local LLM) and falling back to Gemini if LM Studio is unavailable.
This allows the application to work with local LLMs for privacy while maintaining
Gemini as a reliable fallback option.

The service maintains the same interface as both LMStudioService and GeminiService,
making it a drop-in replacement in the websocket_manager.
"""

import os
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import both services
# If imports fail, we'll handle it gracefully
try:
    from .lm_studio_service import get_lm_studio_service, LMStudioService
    LM_STUDIO_AVAILABLE = True
except Exception as e:
    logger.warning(f"LM Studio service not available: {e}")
    LM_STUDIO_AVAILABLE = False
    LMStudioService = None

try:
    from .gemini_service import get_gemini_service, GeminiService
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Gemini service not available: {e}")
    GEMINI_AVAILABLE = False
    GeminiService = None


class UnifiedAIService:
    """
    Unified AI service that automatically falls back between LM Studio and Gemini.
    
    This class provides a single interface for AI services while automatically
    handling fallback logic. It:
    1. Tries LM Studio first (if enabled and available)
    2. Falls back to Gemini if LM Studio fails
    3. Provides consistent error messages
    4. Logs all fallback events for debugging
    
    The service maintains conversation state and delegates to the appropriate
    underlying service (LM Studio or Gemini) based on availability and success.
    """
    
    def __init__(self):
        """
        Initialize the unified AI service.
        
        Determines which services are available and configures fallback behavior.
        The service will prefer LM Studio if available, otherwise use Gemini.
        """
        # Check if we should prefer LM Studio
        # Default to True (prefer local LLM for privacy)
        self.prefer_lm_studio = os.getenv("USE_LM_STUDIO", "true").lower() == "true"
        
        # Track which service is currently being used
        # This helps with logging and debugging
        self.current_service: Optional[str] = None  # "lm_studio" or "gemini"
        
        # Track service instances (lazy initialization)
        self._lm_studio_service: Optional[LMStudioService] = None
        self._gemini_service: Optional[GeminiService] = None
        
        # Track which service to use for each interview
        # Once we've successfully used a service for an interview, stick with it
        # This prevents switching mid-interview which could break context
        self.interview_service_map: Dict[str, str] = {}  # interview_id -> "lm_studio" or "gemini"
        
        logger.info(f"Unified AI Service initialized. LM Studio: {LM_STUDIO_AVAILABLE}, Gemini: {GEMINI_AVAILABLE}, Prefer LM Studio: {self.prefer_lm_studio}")
    
    def _get_lm_studio_service(self) -> Optional[LMStudioService]:
        """
        Get or create LM Studio service instance.
        
        Returns:
            LMStudioService if available, None otherwise
        """
        if not LM_STUDIO_AVAILABLE:
            return None
        
        if self._lm_studio_service is None:
            try:
                self._lm_studio_service = get_lm_studio_service()
                # Test if it's actually working by checking if we can get models
                # This is a lightweight check that doesn't require a full conversation
                try:
                    # Just verify the service was created - actual connection test happens in __init__
                    logger.info("LM Studio service instance created")
                except Exception as e:
                    logger.warning(f"LM Studio service created but may not be fully functional: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize LM Studio service: {e}")
                return None
        
        return self._lm_studio_service
    
    def _get_gemini_service(self) -> Optional[GeminiService]:
        """
        Get or create Gemini service instance.
        
        Returns:
            GeminiService if available, None otherwise
        """
        if not GEMINI_AVAILABLE:
            return None
        
        if self._gemini_service is None:
            try:
                self._gemini_service = get_gemini_service()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini service: {e}")
                return None
        
        return self._gemini_service
    
    def _select_service_for_interview(self, interview_id: str) -> Tuple[Optional[object], str]:
        """
        Select which service to use for an interview.
        
        If the interview already has a service assigned (from a previous call),
        use that service to maintain context. Otherwise, try LM Studio first
        if preferred, then fall back to Gemini.
        
        Args:
            interview_id: The interview to select a service for
            
        Returns:
            Tuple of (service_instance, service_name)
            service_instance can be None if no service is available
            service_name is "lm_studio" or "gemini" or None
        """
        # If interview already has a service assigned, use it
        # This maintains context throughout the interview
        if interview_id in self.interview_service_map:
            service_name = self.interview_service_map[interview_id]
            if service_name == "lm_studio":
                service = self._get_lm_studio_service()
                if service:
                    return service, "lm_studio"
            elif service_name == "gemini":
                service = self._get_gemini_service()
                if service:
                    return service, "gemini"
            # If assigned service is no longer available, clear assignment and try again
            logger.warning(f"Previously assigned service '{service_name}' for interview {interview_id} is no longer available. Trying fallback.")
            del self.interview_service_map[interview_id]
        
        # Try LM Studio first if preferred and available
        if self.prefer_lm_studio:
            lm_studio = self._get_lm_studio_service()
            if lm_studio:
                self.interview_service_map[interview_id] = "lm_studio"
                logger.info(f"Using LM Studio for interview {interview_id}")
                return lm_studio, "lm_studio"
        
        # Fallback to Gemini
        gemini = self._get_gemini_service()
        if gemini:
            self.interview_service_map[interview_id] = "gemini"
            logger.info(f"Using Gemini for interview {interview_id}")
            return gemini, "gemini"
        
        # No service available
        logger.error("No AI service available (neither LM Studio nor Gemini)")
        return None, None
    
    def initialize_conversation(self, interview_id: str) -> str:
        """
        Initialize a new interview conversation and get the greeting.
        
        Tries LM Studio first (if preferred), then falls back to Gemini if needed.
        Once a service is selected for an interview, it will be used for the
        entire interview to maintain context.
        
        Args:
            interview_id: Unique identifier for this interview
            
        Returns:
            str: The greeting/question text from the AI service
            
        Raises:
            Exception: If both services fail or are unavailable
        """
        # Select service for this interview
        service, service_name = self._select_service_for_interview(interview_id)
        
        if service is None:
            raise Exception("No AI service available. Please ensure either LM Studio is running or Gemini API key is configured.")
        
        self.current_service = service_name
        
        try:
            # Try to initialize conversation with selected service
            greeting = service.initialize_conversation(interview_id)
            logger.info(f"Successfully initialized conversation with {service_name} for interview {interview_id}")
            return greeting
            
        except Exception as e:
            logger.warning(f"Failed to initialize conversation with {service_name} for interview {interview_id}: {e}")
            
            # If LM Studio failed and we haven't tried Gemini yet, try Gemini
            if service_name == "lm_studio" and self.prefer_lm_studio:
                logger.info(f"Falling back to Gemini for interview {interview_id}")
                # Clear the assignment so we can try Gemini
                if interview_id in self.interview_service_map:
                    del self.interview_service_map[interview_id]
                
                gemini = self._get_gemini_service()
                if gemini:
                    try:
                        greeting = gemini.initialize_conversation(interview_id)
                        self.interview_service_map[interview_id] = "gemini"
                        self.current_service = "gemini"
                        logger.info(f"Successfully initialized conversation with Gemini (fallback) for interview {interview_id}")
                        return greeting
                    except Exception as gemini_error:
                        logger.error(f"Gemini fallback also failed: {gemini_error}")
                        raise Exception(f"Both LM Studio and Gemini failed. LM Studio error: {str(e)}, Gemini error: {str(gemini_error)}")
                else:
                    raise Exception(f"LM Studio failed and Gemini is not available. LM Studio error: {str(e)}")
            
            # If Gemini failed or we're already using Gemini, re-raise the error
            raise Exception(f"Failed to initialize conversation with {service_name}: {str(e)}")
    
    def process_answer(self, interview_id: str, user_answer: str) -> Dict:
        """
        Process user's answer and get next question or end signal.
        
        Uses the service that was selected during initialization to maintain
        conversation context. If the service fails, attempts fallback (if available).
        
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
            Exception: If AI service call fails
        """
        # Get the service assigned to this interview
        # If no service is assigned, this shouldn't happen (initialize_conversation should be called first)
        if interview_id not in self.interview_service_map:
            raise ValueError(f"Interview {interview_id} not initialized. Call initialize_conversation first.")
        
        service_name = self.interview_service_map[interview_id]
        
        # Get the appropriate service instance
        if service_name == "lm_studio":
            service = self._get_lm_studio_service()
            if not service:
                # LM Studio became unavailable, try Gemini fallback
                logger.warning(f"LM Studio unavailable for interview {interview_id}, trying Gemini fallback")
                service = self._get_gemini_service()
                if service:
                    service_name = "gemini"
                    self.interview_service_map[interview_id] = "gemini"
                    logger.info(f"Switched to Gemini for interview {interview_id}")
                else:
                    raise Exception("LM Studio unavailable and Gemini is not available")
        else:  # gemini
            service = self._get_gemini_service()
            if not service:
                raise Exception("Gemini service is not available")
        
        self.current_service = service_name
        
        try:
            # Process answer with the selected service
            result = service.process_answer(interview_id, user_answer)
            return result
            
        except Exception as e:
            logger.warning(f"Failed to process answer with {service_name} for interview {interview_id}: {e}")
            
            # If LM Studio failed and we haven't tried Gemini yet, try Gemini
            if service_name == "lm_studio":
                gemini = self._get_gemini_service()
                if gemini:
                    try:
                        logger.info(f"Falling back to Gemini for processing answer in interview {interview_id}")
                        # Note: This might lose some context since we're switching services mid-interview
                        # But it's better than failing completely
                        result = gemini.process_answer(interview_id, user_answer)
                        self.interview_service_map[interview_id] = "gemini"
                        self.current_service = "gemini"
                        logger.info(f"Successfully processed answer with Gemini (fallback) for interview {interview_id}")
                        return result
                    except Exception as gemini_error:
                        logger.error(f"Gemini fallback also failed: {gemini_error}")
                        raise Exception(f"Both LM Studio and Gemini failed. LM Studio error: {str(e)}, Gemini error: {str(gemini_error)}")
            
            # Re-raise the error if no fallback is available
            raise Exception(f"Failed to process answer with {service_name}: {str(e)}")
    
    def cleanup(self, interview_id: str):
        """
        Clean up conversation history for an interview.
        
        Cleans up both services (if they have state for this interview)
        and removes the interview from the service map.
        
        Args:
            interview_id: The interview to clean up
        """
        # Clean up the service that was used for this interview
        if interview_id in self.interview_service_map:
            service_name = self.interview_service_map[interview_id]
            
            if service_name == "lm_studio":
                service = self._get_lm_studio_service()
                if service:
                    try:
                        service.cleanup(interview_id)
                    except:
                        pass  # Ignore cleanup errors
            
            elif service_name == "gemini":
                service = self._get_gemini_service()
                if service:
                    try:
                        service.cleanup(interview_id)
                    except:
                        pass  # Ignore cleanup errors
            
            # Remove from service map
            del self.interview_service_map[interview_id]
        
        # Also try to clean up in the other service (in case of mid-interview switch)
        # This is safe even if the service doesn't have state for this interview
        lm_studio = self._get_lm_studio_service()
        if lm_studio:
            try:
                lm_studio.cleanup(interview_id)
            except:
                pass
        
        gemini = self._get_gemini_service()
        if gemini:
            try:
                gemini.cleanup(interview_id)
            except:
                pass


# Global unified AI service instance (lazy initialization)
_unified_ai_service: Optional[UnifiedAIService] = None

def get_ai_service() -> UnifiedAIService:
    """
    Get or create the global unified AI service instance.
    
    This implements the singleton pattern - there's only one UnifiedAIService
    instance shared across the entire application. This ensures:
    - Consistent service selection across all interviews
    - Efficient resource usage
    - Proper fallback behavior
    
    Returns:
        UnifiedAIService: The global service instance
    """
    global _unified_ai_service
    if _unified_ai_service is None:
        _unified_ai_service = UnifiedAIService()
    return _unified_ai_service
