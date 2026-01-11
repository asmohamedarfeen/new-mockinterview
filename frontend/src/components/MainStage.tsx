/**
 * MainStage component - displays the AI interviewer.
 * Google Meet style main video area.
 */
import React from 'react';
import { InterviewState } from '../types/interview';

interface MainStageProps {
  state: InterviewState;
  interviewerName?: string;
}

export const MainStage: React.FC<MainStageProps> = ({
  state,
  interviewerName = 'AI Interviewer',
}) => {
  return (
    <div className="relative w-full h-full bg-meet-dark flex items-center justify-center overflow-hidden">
      {/* AI Interviewer Avatar/Placeholder */}
      <div className="flex flex-col items-center justify-center space-y-4">
        {/* Avatar Circle */}
        <div className="w-32 h-32 md:w-48 md:h-48 rounded-full bg-meet-gray flex items-center justify-center border-4 border-meet-blue">
          <svg
            className="w-16 h-16 md:w-24 md:h-24 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>

        {/* Interviewer Name */}
        <div className="text-white text-xl md:text-2xl font-medium">
          {interviewerName}
        </div>

        {/* Status Indicator */}
        {state === InterviewState.AI_SPEAKING && (
          <div className="flex items-center space-x-2 text-meet-blue">
            <div className="w-2 h-2 bg-meet-blue rounded-full animate-pulse"></div>
            <span className="text-sm">Speaking...</span>
          </div>
        )}

        {state === InterviewState.PROCESSING_WITH_GEMINI && (
          <div className="flex items-center space-x-2 text-yellow-400">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
            <span className="text-sm">Thinking...</span>
          </div>
        )}
      </div>

      {/* Background Pattern (optional) */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
          backgroundSize: '40px 40px',
        }}></div>
      </div>
    </div>
  );
};
