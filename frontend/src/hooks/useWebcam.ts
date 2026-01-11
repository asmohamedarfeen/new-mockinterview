/**
 * Webcam hook for local-only video preview.
 * PRIVACY: This hook only displays the webcam locally. No video is transmitted or stored.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebcamOptions {
  onError?: (error: Error) => void;
}

export function useWebcam({ onError }: UseWebcamOptions = {}) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const start = useCallback(async () => {
    try {
      // PRIVACY: getUserMedia is used only for local display
      // No MediaRecorder is used, and no video data is transmitted
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false, // We only need video for preview
      });

      setStream(mediaStream);
      setIsActive(true);
      setError(null);

      // Attach stream to video element if available
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: any) {
      let errorMessage = 'Failed to access webcam';
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera permission denied. Please allow camera access.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = 'No camera found. Please connect a camera.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = 'Camera is already in use by another application.';
      } else {
        errorMessage = `Camera error: ${err.message || err.name}`;
      }

      setError(errorMessage);
      if (onError) {
        onError(new Error(errorMessage));
      }
    }
  }, [onError]);

  const stop = useCallback(() => {
    if (stream) {
      // Stop all tracks to release the camera
      stream.getTracks().forEach((track) => {
        track.stop();
      });
      setStream(null);
      setIsActive(false);

      // Clear video element
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
  }, [stream]);

  const toggle = useCallback(() => {
    if (isActive) {
      stop();
    } else {
      start();
    }
  }, [isActive, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    stream,
    isActive,
    error,
    start,
    stop,
    toggle,
    videoRef,
  };
}
