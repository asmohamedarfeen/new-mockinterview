/**
 * WebSocket hook with auto-reconnect logic.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { WebSocketMessage, MessageType } from '../types/interview';
import { useInterviewStore } from '../store/interviewStore';
import { InterviewState } from '../types/interview';

interface UseWebSocketOptions {
  interviewId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Error) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  interviewId,
  onMessage,
  onError,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const shouldReconnectRef = useRef(true);
  const { setState, setError, endInterview } = useInterviewStore();

  const connect = useCallback(() => {
    if (!interviewId) return;

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
    const url = `${wsUrl}/${interviewId}`;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle different message types
          switch (message.type) {
            case MessageType.CONNECTION_ACK:
              console.log('Connection acknowledged:', message);
              break;

            case MessageType.INTERVIEW_STATE:
              setState(message.state);
              break;

            case MessageType.AI_QUESTION:
              setState(InterviewState.AI_SPEAKING);
              useInterviewStore.getState().addTranscriptEntry({
                id: `ai-${Date.now()}`,
                role: 'ai',
                text: message.question,
                timestamp: message.timestamp,
              });
              break;

            case MessageType.INTERVIEW_END:
              endInterview(message.feedback, message.score);
              break;

            case MessageType.ERROR:
              setError(message.error);
              console.error('WebSocket error:', message);
              // Don't break - let the error propagate to the component
              break;
          }

          // Call custom onMessage handler
          if (onMessage) {
            onMessage(message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          if (onError) {
            onError(error as Error);
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
        setIsConnected(false);
        if (onError) {
          onError(new Error('WebSocket connection error'));
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        // Attempt to reconnect if we should
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Failed to reconnect after multiple attempts');
          setError('Connection lost. Please refresh the page.');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setConnectionError('Failed to create WebSocket connection');
      if (onError) {
        onError(error as Error);
      }
    }
  }, [interviewId, onMessage, onError, reconnectInterval, maxReconnectAttempts, setState, setError, endInterview]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
      return false;
    }
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (interviewId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [interviewId, connect, disconnect]);

  return {
    isConnected,
    connectionError,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}
