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
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const shouldReconnectRef = useRef(true);
  const { setState, setError, endInterview } = useInterviewStore();

  const connect = useCallback(() => {
    if (!interviewId) return;

    // Use environment variable or auto-detect based on current location
    let wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      // Auto-detect WebSocket URL based on current window location
      // If running on same port as backend, use relative path
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      let host = window.location.host; // Includes port if present
      
      // Replace 0.0.0.0 with localhost for better compatibility
      if (host.startsWith('0.0.0.0:')) {
        host = host.replace('0.0.0.0', 'localhost');
        console.warn('Replaced 0.0.0.0 with localhost for WebSocket connection');
      }
      
      wsUrl = `${protocol}//${host}/ws`;
    }
    const url = `${wsUrl}/${interviewId}`;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
        // Reset shouldReconnect in case it was set to false previously
        shouldReconnectRef.current = true;
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
        // Don't set error immediately - wait for onclose to get more details
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', { code: event.code, reason: event.reason, wasClean: event.wasClean });
        setIsConnected(false);

        // If connection was closed unexpectedly (not clean), set error
        if (!event.wasClean && event.code !== 1000) {
          let errorMsg = 'WebSocket connection error';
          
          // Provide more specific error messages based on close code
          if (event.code === 1006) {
            errorMsg = 'Connection closed unexpectedly. Please ensure the backend server is running.';
          } else if (event.code === 1001) {
            errorMsg = 'Server is going away. Please check backend logs.';
          } else if (event.reason) {
            errorMsg = `Connection error: ${event.reason}`;
          }
          
          setConnectionError(errorMsg);
          if (onError) {
            onError(new Error(errorMsg));
          }
        }

        // Attempt to reconnect if we should
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          const finalError = 'Failed to reconnect after multiple attempts. Please refresh the page.';
          setConnectionError(finalError);
          setError(finalError);
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
