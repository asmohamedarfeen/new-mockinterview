/**
 * TranscriptPanel component - displays interview transcript.
 * Google Meet style right-side panel.
 */
import React, { useEffect, useRef } from 'react';
import { TranscriptEntry } from '../types/interview';

interface TranscriptPanelProps {
  transcript: TranscriptEntry[];
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  transcript,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="w-full h-full bg-meet-dark border-l border-meet-gray flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-meet-gray">
        <h2 className="text-white font-semibold text-lg">Transcript</h2>
      </div>

      {/* Transcript Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
      >
        {transcript.length === 0 ? (
          <div className="text-gray-400 text-sm text-center py-8">
            Transcript will appear here...
          </div>
        ) : (
          transcript.map((entry) => (
            <div
              key={entry.id}
              className={`flex flex-col space-y-1 ${
                entry.role === 'ai' ? 'items-start' : 'items-end'
              }`}
            >
              <div
                className={`
                  max-w-[80%] rounded-lg px-4 py-2
                  ${
                    entry.role === 'ai'
                      ? 'bg-meet-gray text-white'
                      : 'bg-meet-blue text-white'
                  }
                `}
              >
                <div className="text-sm font-medium mb-1">
                  {entry.role === 'ai' ? 'AI Interviewer' : 'You'}
                </div>
                <div className="text-sm whitespace-pre-wrap">{entry.text}</div>
              </div>
              <div className="text-xs text-gray-400 px-2">
                {formatTime(entry.timestamp)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
