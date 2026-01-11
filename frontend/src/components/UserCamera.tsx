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
  const { stream, isActive, error, start, stop, videoRef } = useWebcam({ onError });

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

  return (
    <div className="absolute bottom-4 right-4 w-48 h-36 md:w-64 md:h-48 bg-meet-dark rounded-lg overflow-hidden shadow-2xl border-2 border-meet-blue z-10">
      {error ? (
        <div className="w-full h-full flex items-center justify-center bg-meet-gray">
          <div className="text-white text-xs text-center px-2">
            {error}
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
