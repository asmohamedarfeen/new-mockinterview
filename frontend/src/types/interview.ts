/**
 * TypeScript types for interview state, messages, and WebSocket events.
 */

export enum InterviewState {
  AI_ASKING = "AI_ASKING",
  AI_SPEAKING = "AI_SPEAKING",
  WAITING_FOR_USER = "WAITING_FOR_USER",
  USER_SPEAKING = "USER_SPEAKING",
  SILENCE_DETECTED = "SILENCE_DETECTED",
  PROCESSING_WITH_GEMINI = "PROCESSING_WITH_GEMINI",
  NEXT_QUESTION = "NEXT_QUESTION",
  INTERVIEW_ENDED = "INTERVIEW_ENDED",
}

export enum MessageType {
  USER_TRANSCRIPT = "USER_TRANSCRIPT",
  AI_QUESTION = "AI_QUESTION",
  INTERVIEW_STATE = "INTERVIEW_STATE",
  INTERVIEW_END = "INTERVIEW_END",
  ERROR = "ERROR",
  CONNECTION_ACK = "CONNECTION_ACK",
}

export interface UserTranscriptMessage {
  type: MessageType.USER_TRANSCRIPT;
  interview_id: string;
  transcript: string;
  timestamp: number;
}

export interface AIQuestionMessage {
  type: MessageType.AI_QUESTION;
  interview_id: string;
  question: string;
  timestamp: number;
}

export interface InterviewStateMessage {
  type: MessageType.INTERVIEW_STATE;
  interview_id: string;
  state: InterviewState;
  timestamp: number;
}

export interface InterviewEndMessage {
  type: MessageType.INTERVIEW_END;
  interview_id: string;
  feedback: string;
  score?: number;
  summary?: string;
  timestamp: number;
}

export interface ErrorMessage {
  type: MessageType.ERROR;
  interview_id?: string;
  error: string;
  code?: string;
  timestamp: number;
}

export interface ConnectionAckMessage {
  type: MessageType.CONNECTION_ACK;
  interview_id: string;
  message: string;
  timestamp: number;
}

export type WebSocketMessage =
  | UserTranscriptMessage
  | AIQuestionMessage
  | InterviewStateMessage
  | InterviewEndMessage
  | ErrorMessage
  | ConnectionAckMessage;

export interface TranscriptEntry {
  id: string;
  role: "ai" | "user";
  text: string;
  timestamp: number;
}

export interface InterviewSession {
  interviewId: string;
  state: InterviewState;
  transcript: TranscriptEntry[];
  isActive: boolean;
  error?: string;
  feedback?: string;
  score?: number;
}
