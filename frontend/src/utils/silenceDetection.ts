/**
 * Silence detection utility for speech recognition.
 */
export interface SilenceDetectionOptions {
  silenceTimeout?: number; // milliseconds to wait before considering it silence
  minSpeechDuration?: number; // minimum duration of speech before silence is valid
}

const DEFAULT_OPTIONS: Required<SilenceDetectionOptions> = {
  silenceTimeout: 2500, // 2.5 seconds
  minSpeechDuration: 500, // 0.5 seconds
};

export class SilenceDetector {
  private silenceTimeout: number;
  private minSpeechDuration: number;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private speechStartTime: number | null = null;
  private onSilenceDetected: () => void;
  private isActive: boolean = false;

  constructor(
    onSilenceDetected: () => void,
    options: SilenceDetectionOptions = {}
  ) {
    this.onSilenceDetected = onSilenceDetected;
    const opts = { ...DEFAULT_OPTIONS, ...options };
    this.silenceTimeout = opts.silenceTimeout;
    this.minSpeechDuration = opts.minSpeechDuration;
  }

  start(): void {
    this.isActive = true;
    this.speechStartTime = Date.now();
    this.resetSilenceTimer();
  }

  onSpeech(): void {
    if (!this.isActive) return;
    this.resetSilenceTimer();
  }

  stop(): void {
    this.isActive = false;
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }

  private resetSilenceTimer(): void {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
    }

    this.silenceTimer = setTimeout(() => {
      if (!this.isActive) return;

      // Check if minimum speech duration has been met
      if (this.speechStartTime) {
        const speechDuration = Date.now() - this.speechStartTime;
        if (speechDuration >= this.minSpeechDuration) {
          this.onSilenceDetected();
        }
      }
    }, this.silenceTimeout);
  }

  reset(): void {
    this.stop();
    this.speechStartTime = null;
  }
}
