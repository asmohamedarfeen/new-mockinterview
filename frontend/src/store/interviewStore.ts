/**
 * Zustand store for interview state management.
 */
import { create } from 'zustand';
import { InterviewState, TranscriptEntry, InterviewSession } from '../types/interview';

interface InterviewStore extends InterviewSession {
  // Actions
  setState: (state: InterviewState) => void;
  addTranscriptEntry: (entry: TranscriptEntry) => void;
  startInterview: (interviewId: string) => void;
  endInterview: (feedback?: string, score?: number) => void;
  setError: (error: string | undefined) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState: InterviewSession = {
  interviewId: '',
  state: InterviewState.AI_ASKING,
  transcript: [],
  isActive: false,
};

export const useInterviewStore = create<InterviewStore>((set) => ({
  ...initialState,

  setState: (state) => set({ state }),

  addTranscriptEntry: (entry) =>
    set((state) => ({
      transcript: [...state.transcript, entry],
    })),

  startInterview: (interviewId) =>
    set({
      interviewId,
      state: InterviewState.AI_ASKING,
      transcript: [],
      isActive: true,
      error: undefined,
      feedback: undefined,
      score: undefined,
    }),

  endInterview: (feedback, score) =>
    set({
      state: InterviewState.INTERVIEW_ENDED,
      isActive: false,
      feedback,
      score,
    }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: undefined }),

  reset: () => set(initialState),
}));
