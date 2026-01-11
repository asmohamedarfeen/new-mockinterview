/**
 * Speech Recognition hook with auto-start and silence detection.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { SilenceDetector } from '../utils/silenceDetection';

interface UseSpeechRecognitionOptions {
  onTranscript: (transcript: string) => void;
  onError?: (error: Error) => void;
  autoStart?: boolean;
  silenceTimeout?: number;
  language?: string;
}

// Type declaration for Web Speech API
declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
}

export function useSpeechRecognition({
  onTranscript,
  onError,
  autoStart = false,
  silenceTimeout = 2500,
  language = 'en-US',
}: UseSpeechRecognitionOptions) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const silenceDetectorRef = useRef<SilenceDetector | null>(null);
  const finalTranscriptRef = useRef('');

  const handleSilence = useCallback(() => {
    if (recognitionRef.current && isListening) {
      const finalTranscript = finalTranscriptRef.current.trim();
      if (finalTranscript) {
        onTranscript(finalTranscript);
      }
      stop();
    }
  }, [isListening, onTranscript]);

  const start = useCallback(() => {
    // Check browser support
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      const errorMsg = 'Speech recognition is not supported in this browser';
      setError(errorMsg);
      if (onError) {
        onError(new Error(errorMsg));
      }
      return;
    }

    try {
      // Initialize recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language;

      // Initialize silence detector
      silenceDetectorRef.current = new SilenceDetector(handleSilence, {
        silenceTimeout,
      });

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
        setError(null);
        finalTranscriptRef.current = '';
        setTranscript('');
        silenceDetectorRef.current?.start();
      };

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          finalTranscriptRef.current += finalTranscript;
          setTranscript(finalTranscriptRef.current);
          // Reset silence timer on speech
          silenceDetectorRef.current?.onSpeech();
        } else {
          setTranscript(finalTranscriptRef.current + interimTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        let errorMessage = 'Speech recognition error';
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'audio-capture':
            errorMessage = 'No microphone found. Please check your microphone.';
            break;
          case 'not-allowed':
            errorMessage = 'Microphone permission denied. Please allow microphone access.';
            break;
          case 'network':
            errorMessage = 'Network error. Please check your connection.';
            break;
          default:
            errorMessage = `Speech recognition error: ${event.error}`;
        }

        setError(errorMessage);
        if (onError) {
          onError(new Error(errorMessage));
        }
        stop();
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
        silenceDetectorRef.current?.stop();
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      const errorMsg = `Failed to start speech recognition: ${err}`;
      setError(errorMsg);
      if (onError) {
        onError(err as Error);
      }
    }
  }, [language, silenceTimeout, handleSilence, onError]);

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    silenceDetectorRef.current?.stop();
    setIsListening(false);
  }, []);

  useEffect(() => {
    if (autoStart) {
      start();
    }

    return () => {
      stop();
    };
  }, [autoStart, start, stop]);

  return {
    isListening,
    transcript,
    error,
    start,
    stop,
  };
}
