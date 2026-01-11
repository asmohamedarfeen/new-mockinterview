/**
 * InterviewRoom component - main container that orchestrates all sub-components.
 * Manages interview lifecycle and voice interaction flow.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useInterviewStore } from '../store/interviewStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { InterviewState, MessageType, AIQuestionMessage } from '../types/interview';
import { MainStage } from './MainStage';
import { UserCamera } from './UserCamera';
import { ControlBar } from './ControlBar';
import { TranscriptPanel } from './TranscriptPanel';
import { StatusOverlay } from './StatusOverlay';

interface InterviewRoomProps {
  interviewId: string;
  onEnd?: () => void;
}

export const InterviewRoom: React.FC<InterviewRoomProps> = ({
  interviewId,
  onEnd,
}) => {
  const {
    state,
    transcript,
    isActive,
    feedback,
    score,
    error,
    setState,
    startInterview,
    endInterview,
    addTranscriptEntry,
    setError,
  } = useInterviewStore();

  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const [isCameraEnabled, setIsCameraEnabled] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');

  // WebSocket connection
  const { isConnected, sendMessage, connectionError } = useWebSocket({
    interviewId,
    onMessage: (message) => {
      if (message.type === MessageType.AI_QUESTION) {
        const aiMsg = message as AIQuestionMessage;
        setCurrentQuestion(aiMsg.question);
      } else if (message.type === MessageType.ERROR) {
        const errorMsg = message as any;
        setError(errorMsg.error || 'An error occurred');
        // End interview on error
        endInterview(errorMsg.error || 'An error occurred');
      }
    },
    onError: (error) => {
      setError(`Connection error: ${error.message}`);
    },
  });

  // Speech Synthesis - TTS for AI questions
  const { isSpeaking, speak, cancel: cancelTTS } = useSpeechSynthesis({
    onEnd: () => {
      // When AI finishes speaking, transition to waiting and auto-start mic
      if (state === InterviewState.AI_SPEAKING) {
        setState(InterviewState.WAITING_FOR_USER);
      }
    },
    onError: (error) => {
      console.error('TTS error:', error);
      // Fallback: if TTS fails, still transition to waiting
      if (state === InterviewState.AI_SPEAKING) {
        setState(InterviewState.WAITING_FOR_USER);
      }
    },
  });

  // Speech Recognition - STT for user answers
  const { isListening, transcript: speechTranscript, start: startSTT, stop: stopSTT } = useSpeechRecognition({
    onTranscript: (finalTranscript) => {
      if (finalTranscript.trim()) {
        // Send transcript to backend
        sendMessage({
          type: MessageType.USER_TRANSCRIPT,
          interview_id: interviewId,
          transcript: finalTranscript,
          timestamp: Date.now() / 1000,
        });

        // Add to local transcript
        addTranscriptEntry({
          id: `user-${Date.now()}`,
          role: 'user',
          text: finalTranscript,
          timestamp: Date.now(),
        });

        setState(InterviewState.PROCESSING_WITH_GEMINI);
      }
    },
    onError: (error) => {
      console.error('STT error:', error);
      setError(`Speech recognition error: ${error.message}`);
    },
    autoStart: false,
  });

  // Initialize interview
  useEffect(() => {
    if (interviewId) {
      startInterview(interviewId);
    }
  }, [interviewId, startInterview]);

  // Handle AI questions - speak them when received
  useEffect(() => {
    if (currentQuestion && state === InterviewState.AI_SPEAKING && !isSpeaking) {
      speak(currentQuestion);
    }
  }, [currentQuestion, state, isSpeaking, speak]);

  // Auto-start speech recognition when AI finishes speaking
  useEffect(() => {
    if (
      state === InterviewState.WAITING_FOR_USER &&
      isMicEnabled &&
      !isListening &&
      isConnected
    ) {
      // Small delay to ensure TTS has fully ended
      const timer = setTimeout(() => {
        startSTT();
        setState(InterviewState.USER_SPEAKING);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [state, isMicEnabled, isListening, isConnected, startSTT, setState]);

  // Handle interview end
  useEffect(() => {
    if (state === InterviewState.INTERVIEW_ENDED && feedback) {
      stopSTT();
      cancelTTS();
      if (onEnd) {
        onEnd();
      }
    }
  }, [state, feedback, stopSTT, cancelTTS, onEnd]);

  const handleMicToggle = useCallback(() => {
    setIsMicEnabled((prev) => {
      if (prev) {
        stopSTT();
      } else if (state === InterviewState.WAITING_FOR_USER || state === InterviewState.USER_SPEAKING) {
        startSTT();
        setState(InterviewState.USER_SPEAKING);
      }
      return !prev;
    });
  }, [stopSTT, startSTT, state, setState]);

  const handleCameraToggle = useCallback(() => {
    setIsCameraEnabled((prev) => !prev);
  }, []);

  const handleEndInterview = useCallback(() => {
    if (window.confirm('Are you sure you want to end the interview?')) {
      stopSTT();
      cancelTTS();
      endInterview('Interview ended by user');
      if (onEnd) {
        onEnd();
      }
    }
  }, [stopSTT, cancelTTS, endInterview, onEnd]);

  // Show feedback screen if interview ended
  if (state === InterviewState.INTERVIEW_ENDED && feedback) {
    return (
      <div className="w-full h-screen bg-meet-dark flex items-center justify-center">
        <div className="max-w-2xl w-full mx-4 bg-meet-gray rounded-lg p-8 text-white">
          <h2 className="text-2xl font-bold mb-4">Interview Complete</h2>
          {score !== undefined && (
            <div className="mb-4">
              <div className="text-3xl font-bold text-meet-blue">Score: {score}/100</div>
            </div>
          )}
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">Feedback:</h3>
            <div className="whitespace-pre-wrap text-gray-200">{feedback}</div>
          </div>
          <button
            onClick={() => {
              if (onEnd) onEnd();
            }}
            className="px-6 py-2 bg-meet-blue hover:bg-blue-600 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-meet-dark flex flex-col overflow-hidden">
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Stage */}
        <div className="flex-1 relative">
          <MainStage state={state} />
          <StatusOverlay state={state} />
          <UserCamera isEnabled={isCameraEnabled} />
        </div>

        {/* Transcript Panel */}
        <div className="w-80 border-l border-meet-gray">
          <TranscriptPanel transcript={transcript} />
        </div>
      </div>

      {/* Control Bar */}
      <ControlBar
        isMicEnabled={isMicEnabled}
        isCameraEnabled={isCameraEnabled}
        onMicToggle={handleMicToggle}
        onCameraToggle={handleCameraToggle}
        onEndInterview={handleEndInterview}
        disabled={!isConnected || state === InterviewState.INTERVIEW_ENDED}
      />

      {/* Connection Status */}
      {!isConnected && !error && (
        <div className="absolute top-4 right-4 bg-yellow-600 text-white px-4 py-2 rounded-lg">
          Connecting...
        </div>
      )}
      
      {/* Error Display */}
      {error && (
        <div className="absolute top-4 left-4 right-4 bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg z-30 max-w-2xl">
          <div className="flex items-start space-x-3">
            <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Error</h3>
              <p className="text-sm">{error}</p>
              {error.includes('API key') && (
                <p className="text-xs mt-2 opacity-90">
                  Please add a valid Gemini API key to <code className="bg-black bg-opacity-30 px-1 rounded">backend/.env</code>
                </p>
              )}
            </div>
            <button
              onClick={() => {
                setError(undefined);
                if (onEnd) onEnd();
              }}
              className="text-white hover:text-gray-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
