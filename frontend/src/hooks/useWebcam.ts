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
      // Check if getUserMedia is available
      // First check if navigator.mediaDevices exists (it might be undefined in some contexts)
      if (typeof navigator !== 'undefined' && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
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
        return;
      }
      
      // Fallback for older browsers or when mediaDevices is undefined
      if (typeof navigator === 'undefined') {
        throw new Error('Navigator is not available. Please use a modern browser.');
      }
      
      // Try legacy getUserMedia APIs
      const getUserMedia = 
        (navigator as any).getUserMedia ||
        (navigator as any).webkitGetUserMedia ||
        (navigator as any).mozGetUserMedia ||
        (navigator as any).msGetUserMedia;
      
      if (!getUserMedia) {
        // Check if we're on 0.0.0.0 and suggest localhost
        const currentHost = typeof window !== 'undefined' ? window.location.hostname : '';
        let errorMsg = 'Camera preview unavailable. Interview can still proceed.';
        
        if (currentHost === '0.0.0.0') {
          errorMsg = 'Use localhost:8000 for camera. Interview can still proceed.';
        } else if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
          errorMsg = 'Camera requires localhost or HTTPS. Interview can still proceed.';
        }
        
        console.warn('getUserMedia not available. Camera preview will be disabled. Interview can still proceed.');
        setError(errorMsg);
        return;
      }
      
      // For older browsers, wrap in Promise
      const mediaStream = await new Promise<MediaStream>((resolve, reject) => {
        getUserMedia.call(
          navigator, 
          { video: true, audio: false }, 
          (stream: MediaStream) => resolve(stream), 
          (err: any) => reject(err)
        );
      });
      
      setStream(mediaStream);
      setIsActive(true);
      setError(null);
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: any) {
      let errorMessage = 'Camera preview unavailable';
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera permission denied. Interview can still proceed.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = 'No camera found. Interview can still proceed.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = 'Camera in use. Interview can still proceed.';
      } else if (err.message && err.message.includes('not supported')) {
        // For unsupported contexts (like 0.0.0.0), show helpful message
        const currentHost = typeof window !== 'undefined' ? window.location.hostname : '';
        if (currentHost === '0.0.0.0') {
          errorMessage = 'Use localhost:8000 for camera. Interview can still proceed.';
        } else {
          errorMessage = 'Camera unavailable. Use localhost or HTTPS. Interview can still proceed.';
        }
      } else {
        errorMessage = `Camera preview unavailable. Interview can still proceed.`;
      }

      // Set error but don't block - camera is optional
      setError(errorMessage);
      console.warn('Camera error (non-blocking):', errorMessage);
      
      // Only call onError if provided, but don't throw
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
    }
    
    // Clear video element
    if (videoRef.current) {
      videoRef.current.srcObject = null;
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
