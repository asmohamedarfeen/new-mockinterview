/**
 * ControlBar component - mic, camera, and end interview controls.
 */
import React from 'react';

interface ControlBarProps {
  isMicEnabled: boolean;
  isCameraEnabled: boolean;
  onMicToggle: () => void;
  onCameraToggle: () => void;
  onEndInterview: () => void;
  disabled?: boolean;
}

export const ControlBar: React.FC<ControlBarProps> = ({
  isMicEnabled,
  isCameraEnabled,
  onMicToggle,
  onCameraToggle,
  onEndInterview,
  disabled = false,
}) => {
  return (
    <div className="flex items-center justify-center space-x-4 py-4 bg-meet-dark border-t border-meet-gray">
      {/* Microphone Toggle */}
      <button
        onClick={onMicToggle}
        disabled={disabled}
        className={`
          w-12 h-12 rounded-full flex items-center justify-center
          transition-all duration-200
          ${isMicEnabled
            ? 'bg-white hover:bg-gray-200'
            : 'bg-red-600 hover:bg-red-700'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        title={isMicEnabled ? 'Mute microphone' : 'Unmute microphone'}
      >
        {isMicEnabled ? (
          <svg
            className="w-6 h-6 text-meet-dark"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        ) : (
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
            />
          </svg>
        )}
      </button>

      {/* Camera Toggle */}
      <button
        onClick={onCameraToggle}
        disabled={disabled}
        className={`
          w-12 h-12 rounded-full flex items-center justify-center
          transition-all duration-200
          ${isCameraEnabled
            ? 'bg-white hover:bg-gray-200'
            : 'bg-meet-gray hover:bg-gray-600'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        title={isCameraEnabled ? 'Turn off camera' : 'Turn on camera'}
      >
        {isCameraEnabled ? (
          <svg
            className="w-6 h-6 text-meet-dark"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
        ) : (
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
            />
          </svg>
        )}
      </button>

      {/* End Interview Button */}
      <button
        onClick={onEndInterview}
        disabled={disabled}
        className={`
          w-12 h-12 rounded-full flex items-center justify-center
          bg-red-600 hover:bg-red-700
          transition-all duration-200
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        title="End interview"
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};
