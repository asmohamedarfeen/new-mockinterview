/**
 * UserCamera component - floating Picture-in-Picture webcam preview.
 * PRIVACY: This component only displays the webcam locally. No video is transmitted or stored.
 */
import React, { useEffect } from 'react';
import { useWebcam } from '../hooks/useWebcam';

interface UserCameraProps {
  isEnabled: boolean;
  onError?: (error: Error) => void;
}

export const UserCamera: React.FC<UserCameraProps> = ({
  isEnabled,
  onError,
}) => {
  const { isActive, error, start, stop, videoRef } = useWebcam({ onError });

  useEffect(() => {
    if (isEnabled && !isActive) {
      start();
    } else if (!isEnabled && isActive) {
      stop();
    }
  }, [isEnabled, isActive, start, stop]);

  if (!isEnabled) {
    return null;
  }

  // If camera has an error and it's not critical, show a minimal indicator
  // Camera is optional - interview can proceed without it
  if (error && error.includes('Interview can still proceed')) {
    // Show a small, non-intrusive indicator that camera is unavailable
    return (
      <div className="absolute bottom-4 right-4 w-48 h-36 md:w-64 md:h-48 bg-meet-dark rounded-lg overflow-hidden shadow-2xl border-2 border-meet-gray z-10 opacity-50">
        <div className="w-full h-full flex items-center justify-center bg-meet-gray bg-opacity-80">
          <div className="text-white text-xs text-center px-2">
            <div className="mb-1 text-2xl">📷</div>
            <div className="text-[10px] leading-tight">Camera unavailable</div>
            <div className="text-[9px] mt-1 opacity-75">Interview continues</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="absolute bottom-4 right-4 w-48 h-36 md:w-64 md:h-48 bg-meet-dark rounded-lg overflow-hidden shadow-2xl border-2 border-meet-blue z-10">
      {error ? (
        <div className="w-full h-full flex items-center justify-center bg-meet-gray bg-opacity-80">
          <div className="text-white text-xs text-center px-2">
            <div className="mb-1">📷</div>
            <div className="text-[10px] leading-tight">{error}</div>
          </div>
        </div>
      ) : (
        <>
          {/* PRIVACY: Video element - local display only, not transmitted */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          
          {/* Overlay label */}
          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs px-2 py-1">
            You
          </div>
        </>
      )}
    </div>
  );
};
