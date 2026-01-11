/**
 * Speech Synthesis hook with queue management and completion detection.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

interface UseSpeechSynthesisOptions {
  onEnd?: () => void;
  onError?: (error: Error) => void;
  voice?: SpeechSynthesisVoice | null;
  rate?: number;
  pitch?: number;
  volume?: number;
}

export function useSpeechSynthesis({
  onEnd,
  onError,
  voice = null,
  rate = 1.0,
  pitch = 1.0,
  volume = 1.0,
}: UseSpeechSynthesisOptions = {}) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const queueRef = useRef<string[]>([]);
  const isProcessingRef = useRef(false);

  const speak = useCallback(
    (text: string) => {
      if (!text.trim()) {
        return;
      }

      // Check browser support
      if (!('speechSynthesis' in window)) {
        const errorMsg = 'Speech synthesis is not supported in this browser';
        setError(errorMsg);
        if (onError) {
          onError(new Error(errorMsg));
        }
        return;
      }

      // Cancel any ongoing speech
      if (isProcessingRef.current) {
        window.speechSynthesis.cancel();
      }

      try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = rate;
        utterance.pitch = pitch;
        utterance.volume = volume;

        if (voice) {
          utterance.voice = voice;
        }

        utterance.onstart = () => {
          console.log('Speech synthesis started');
          setIsSpeaking(true);
          setError(null);
          isProcessingRef.current = true;
        };

        utterance.onend = () => {
          console.log('Speech synthesis ended');
          setIsSpeaking(false);
          isProcessingRef.current = false;
          if (onEnd) {
            onEnd();
          }
        };

        utterance.onerror = (event) => {
          console.error('Speech synthesis error:', event);
          const errorMsg = `Speech synthesis error: ${event.error}`;
          setError(errorMsg);
          setIsSpeaking(false);
          isProcessingRef.current = false;
          if (onError) {
            onError(new Error(errorMsg));
          }
          if (onEnd) {
            onEnd();
          }
        };

        utteranceRef.current = utterance;
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        const errorMsg = `Failed to speak: ${err}`;
        setError(errorMsg);
        if (onError) {
          onError(err as Error);
        }
      }
    },
    [rate, pitch, volume, voice, onEnd, onError]
  );

  const cancel = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      isProcessingRef.current = false;
      queueRef.current = [];
    }
  }, []);

  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return {
    isSpeaking,
    error,
    speak,
    cancel,
  };
}
