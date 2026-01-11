/**
 * StatusOverlay component - displays status indicators.
 */
import React from 'react';
import { InterviewState } from '../types/interview';

interface StatusOverlayProps {
  state: InterviewState;
}

export const StatusOverlay: React.FC<StatusOverlayProps> = ({ state }) => {
  const getStatusMessage = () => {
    switch (state) {
      case InterviewState.AI_SPEAKING:
        return {
          message: 'AI Speaking...',
          color: 'text-meet-blue',
          bgColor: 'bg-meet-blue',
        };
      case InterviewState.WAITING_FOR_USER:
        return {
          message: 'Listening...',
          color: 'text-green-400',
          bgColor: 'bg-green-400',
        };
      case InterviewState.USER_SPEAKING:
        return {
          message: 'You are speaking...',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-400',
        };
      case InterviewState.PROCESSING_WITH_GEMINI:
        return {
          message: 'Processing your answer...',
          color: 'text-purple-400',
          bgColor: 'bg-purple-400',
        };
      case InterviewState.INTERVIEW_ENDED:
        return {
          message: 'Interview Ended',
          color: 'text-gray-400',
          bgColor: 'bg-gray-400',
        };
      default:
        return null;
    }
  };

  const status = getStatusMessage();

  if (!status) {
    return null;
  }

  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20">
      <div
        className={`
          px-4 py-2 rounded-full
          bg-black bg-opacity-70
          flex items-center space-x-2
          ${status.color}
        `}
      >
        <div
          className={`w-2 h-2 rounded-full ${status.bgColor} animate-pulse`}
        ></div>
        <span className="text-sm font-medium">{status.message}</span>
      </div>
    </div>
  );
};
