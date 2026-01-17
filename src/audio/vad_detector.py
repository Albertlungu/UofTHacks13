"""
Voice Activity Detection with adaptive silence handling.
"""

import collections
from typing import Optional

import numpy as np
import webrtcvad
from loguru import logger

from src.audio.audio_config import (
    INITIAL_SILENCE_THRESHOLD,
    MAX_SILENCE_BEFORE_INTERRUPT,
    MIN_SPEECH_DURATION,
    SAMPLE_RATE,
    THINKING_PAUSE_THRESHOLD,
    VAD_FRAME_DURATION_MS,
    VAD_MODE,
)


class VADDetector:
    """
    Adaptive Voice Activity Detector that handles thinking pauses
    and natural conversation flow.
    """

    def __init__(self):
        self.vad = webrtcvad.Vad(VAD_MODE)
        self.sample_rate = SAMPLE_RATE
        self.frame_duration_ms = VAD_FRAME_DURATION_MS
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

        # State tracking
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.total_speech_duration = 0.0
        self.total_silence_duration = 0.0

        # Adaptive thresholds
        self.current_silence_threshold = INITIAL_SILENCE_THRESHOLD
        self.in_thinking_mode = False

        # Ring buffer for smoothing
        self.ring_buffer = collections.deque(maxlen=10)

        logger.info(
            f"VAD initialized (mode: {VAD_MODE}, frame: {VAD_FRAME_DURATION_MS}ms)"
        )

    def process_frame(self, frame: bytes) -> Optional[str]:
        """
        Process an audio frame and return the current state.

        Args:
            frame: Audio frame bytes (must match frame_size)

        Returns:
            'speech_start', 'speech_continue', 'silence', 'speech_end', or None
        """
        # Ensure frame is correct size
        if len(frame) != self.frame_size * 2:  # *2 because int16 is 2 bytes
            return None

        try:
            is_speech = self.vad.is_speech(frame, self.sample_rate)
        except Exception as e:
            logger.warning(f"VAD error: {e}")
            return None

        # Add to ring buffer for smoothing
        self.ring_buffer.append(is_speech)

        # Use majority vote from ring buffer
        speech_count = sum(self.ring_buffer)
        smoothed_is_speech = speech_count > len(self.ring_buffer) / 2

        frame_duration = self.frame_duration_ms / 1000.0

        if smoothed_is_speech:
            self.silence_frames = 0
            self.speech_frames += 1
            self.total_speech_duration += frame_duration

            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.in_thinking_mode = False
                logger.debug("Speech detected - START")
                return "speech_start"
            else:
                return "speech_continue"
        else:
            # Silence detected
            self.speech_frames = 0
            self.silence_frames += 1
            self.total_silence_duration += frame_duration

            if self.is_speaking:
                # Determine what kind of silence this is
                silence_duration = self.silence_frames * frame_duration

                if self.in_thinking_mode:
                    # User explicitly asked to wait
                    if silence_duration > MAX_SILENCE_BEFORE_INTERRUPT:
                        logger.info("Thinking pause exceeded max duration")
                        return self._end_speech()
                    return "silence"

                elif silence_duration > THINKING_PAUSE_THRESHOLD:
                    # Long pause - might be thinking or done speaking
                    if self.total_speech_duration < MIN_SPEECH_DURATION:
                        # Too short to be meaningful
                        return "silence"
                    logger.debug(f"Long pause detected: {silence_duration:.2f}s")
                    return self._end_speech()

                elif silence_duration > self.current_silence_threshold:
                    # Standard silence threshold reached
                    if self.total_speech_duration >= MIN_SPEECH_DURATION:
                        logger.debug(
                            f"Silence threshold reached: {silence_duration:.2f}s"
                        )
                        return self._end_speech()
                    else:
                        logger.debug("Speech too short, waiting for more")
                        return "silence"

                return "silence"

            return None

    def _end_speech(self) -> str:
        """Handle speech ending."""
        self.is_speaking = False
        logger.info(f"Speech ended (duration: {self.total_speech_duration:.2f}s)")
        return "speech_end"

    def enter_thinking_mode(self):
        """Enter thinking mode - more tolerant of silence."""
        self.in_thinking_mode = True
        logger.info("Entered thinking mode - will wait longer for user")

    def exit_thinking_mode(self):
        """Exit thinking mode - return to normal conversation."""
        self.in_thinking_mode = False
        logger.info("Exited thinking mode")

    def reset(self):
        """Reset all state counters."""
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.total_speech_duration = 0.0
        self.total_silence_duration = 0.0
        self.ring_buffer.clear()
        self.in_thinking_mode = False
        logger.debug("VAD state reset")

    def get_speech_duration(self) -> float:
        """Get total speech duration in seconds."""
        return self.total_speech_duration

    def get_silence_duration(self) -> float:
        """Get current silence duration in seconds."""
        return self.silence_frames * (self.frame_duration_ms / 1000.0)
