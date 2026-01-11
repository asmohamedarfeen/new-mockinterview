import React, { useState } from 'react';
import { InterviewRoom } from './components/InterviewRoom';
import './App.css';

function App() {
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const handleStartInterview = () => {
    // Generate a unique interview ID
    const newInterviewId = `interview-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setIsStarting(true);
    setInterviewId(newInterviewId);
  };

  const handleEndInterview = () => {
    setInterviewId(null);
    setIsStarting(false);
  };

  if (interviewId) {
    return <InterviewRoom interviewId={interviewId} onEnd={handleEndInterview} />;
  }

  return (
    <div className="min-h-screen bg-meet-dark flex items-center justify-center">
      <div className="max-w-md w-full mx-4 bg-meet-gray rounded-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2 text-center">Virtual AI Interview Room</h1>
        <p className="text-gray-300 text-center mb-8">
          Practice your interview skills with an AI-powered interviewer
        </p>

        <div className="space-y-4 mb-6">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-meet-blue mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="font-semibold">AI-Powered Interviewer</div>
              <div className="text-sm text-gray-400">Get realistic interview questions and feedback</div>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-meet-blue mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="font-semibold">Voice Interaction</div>
              <div className="text-sm text-gray-400">Natural conversation with speech recognition</div>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-meet-blue mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="font-semibold">Privacy First</div>
              <div className="text-sm text-gray-400">Your video stays local, only transcripts are sent</div>
            </div>
          </div>
        </div>

        <button
          onClick={handleStartInterview}
          disabled={isStarting}
          className="w-full py-3 bg-meet-blue hover:bg-blue-600 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStarting ? 'Starting...' : 'Start Interview'}
        </button>

        <p className="text-xs text-gray-400 text-center mt-4">
          Make sure your microphone is enabled and you're in a quiet environment
        </p>
      </div>
    </div>
  );
}

export default App;
