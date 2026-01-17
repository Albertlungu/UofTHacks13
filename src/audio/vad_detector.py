"""
Voice Activity Detection with adaptive silence handling and calibration.
"""

import collections
import time
from typing import Optional, Tuple

import numpy as np
import webrtcvad
from loguru import logger

from src.audio.audio_config import (
    CALIBRATION_DURATION,
    CALIBRATION_SILENCE_BUFFER,
    INITIAL_SILENCE_THRESHOLD,
    MAX_SILENCE_BEFORE_INTERRUPT,
    MIN_CALIBRATION_WORDS,
    MIN_SPEECH_DURATION,
    SAMPLE_RATE,
    THINKING_PAUSE_THRESHOLD,
    VAD_FRAME_DURATION_MS,
    VAD_MODE,
)


class VADDetector:
    """
    Adaptive Voice Activity Detector that handles thinking pauses,
    natural conversation flow, and learns user speech patterns.
    """

    def __init__(self, user_profile=None):
        self.vad = webrtcvad.Vad(VAD_MODE)
        self.sample_rate = SAMPLE_RATE
        self.frame_duration_ms = VAD_FRAME_DURATION_MS
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

        # CALIBRATION CODE - COMMENTED OUT
        # # User profile for adaptive behavior
        # self.user_profile = user_profile

        # State tracking
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.total_speech_duration = 0.0
        self.total_silence_duration = 0.0
        self.last_speech_end_time = 0.0

        # Use fixed thresholds (no adaptive behavior)
        self.current_silence_threshold = INITIAL_SILENCE_THRESHOLD
        self.current_thinking_threshold = THINKING_PAUSE_THRESHOLD
        self.current_max_silence = MAX_SILENCE_BEFORE_INTERRUPT

        # CALIBRATION CODE - COMMENTED OUT
        # # Load thresholds from profile if calibrated
        # if user_profile and user_profile.is_calibrated:
        #     self.current_silence_threshold = user_profile.silence_threshold
        #     self.current_thinking_threshold = user_profile.thinking_pause_threshold
        #     self.current_max_silence = user_profile.max_silence_before_interrupt
        #     logger.info(
        #         f"Loaded calibrated thresholds: "
        #         f"silence={self.current_silence_threshold:.2f}s, "
        #         f"thinking={self.current_thinking_threshold:.2f}s"
        #     )

        # # Calibration state
        # self.is_calibrating = user_profile and not user_profile.is_calibrated
        # self.calibration_start_time = time.time() if self.is_calibrating else None

        # # During calibration, add buffer time
        # if self.is_calibrating:
        #     self.current_silence_threshold += CALIBRATION_SILENCE_BUFFER
        #     self.current_thinking_threshold += CALIBRATION_SILENCE_BUFFER
        #     logger.info(f"Calibration mode active - using lenient thresholds")

        # Thinking mode
        self.in_thinking_mode = False

        # CALIBRATION CODE - COMMENTED OUT
        # # Pause tracking for learning
        # self.current_pause_start = None
        # self.pause_location = "unknown"
        # self.resumed_after_pause = False

        # Ring buffer for smoothing
        self.ring_buffer = collections.deque(maxlen=10)

        logger.info(
            f"VAD initialized (mode: {VAD_MODE}, frame: {VAD_FRAME_DURATION_MS}ms)"
        )

    def process_frame(self, frame: bytes) -> Optional[Tuple[str, Optional[dict]]]:
        """
        Process an audio frame and return the current state.

        Args:
            frame: Audio frame bytes (must match frame_size)

        Returns:
            Tuple of (state, pause_info) where:
            - state: 'speech_start', 'speech_continue', 'silence', 'speech_end', or None
            - pause_info: Dict with pause details if a pause was detected, None otherwise
        """
        # CALIBRATION CODE - COMMENTED OUT
        # # Check if calibration should end
        # if self.is_calibrating and self.calibration_start_time:
        #     elapsed = time.time() - self.calibration_start_time
        #     if elapsed >= CALIBRATION_DURATION:
        #         if self.user_profile.total_words_spoken >= MIN_CALIBRATION_WORDS:
        #             self._end_calibration()
        #         else:
        #             logger.info(
        #                 f"Extending calibration (only {self.user_profile.total_words_spoken} words)"
        #             )

        # Ensure frame is correct size
        if len(frame) != self.frame_size * 2:  # *2 because int16 is 2 bytes
            return None, None

        # Calculate audio energy to filter out distant/quiet sounds
        audio_array = np.frombuffer(frame, dtype=np.int16)
        energy = np.abs(audio_array).mean()

        # Energy threshold - distant voices typically have lower energy
        # Adjust this value: higher = more sensitive (requires louder speech)
        ENERGY_THRESHOLD = 100  # Typical close-mic speech is 500-3000

        if energy < ENERGY_THRESHOLD:
            # Too quiet, likely background noise or distant voice
            is_speech = False
        else:
            try:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
            except Exception as e:
                logger.warning(f"VAD error: {e}")
                return None, None

        # Add to ring buffer for smoothing
        self.ring_buffer.append(is_speech)

        # Use majority vote from ring buffer
        speech_count = sum(self.ring_buffer)
        smoothed_is_speech = speech_count > len(self.ring_buffer) / 2

        frame_duration = self.frame_duration_ms / 1000.0

        pause_info = None

        if smoothed_is_speech:
            self.silence_frames = 0
            self.speech_frames += 1
            self.total_speech_duration += frame_duration

            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.in_thinking_mode = False

                # CALIBRATION CODE - COMMENTED OUT
                # # Check if this is resuming after a pause
                # if self.current_pause_start is not None:
                #     pause_duration = time.time() - self.current_pause_start
                #     self.resumed_after_pause = True

                #     # This was a thinking pause!
                #     pause_info = {
                #         "duration": pause_duration,
                #         "location": self.pause_location,
                #         "was_thinking_pause": True,
                #     }
                #     logger.debug(
                #         f"User resumed after {pause_duration:.2f}s pause - marked as thinking"
                #     )
                #     self.current_pause_start = None

                logger.debug("Speech detected - START")
                return "speech_start", None  # No pause_info
            else:
                return "speech_continue", None
        else:
            # Silence detected
            self.speech_frames = 0
            self.silence_frames += 1
            self.total_silence_duration += frame_duration

            if self.is_speaking:
                # CALIBRATION CODE - COMMENTED OUT
                # # Mark pause start if not already marked
                # if self.current_pause_start is None:
                #     self.current_pause_start = time.time()
                #     # Determine pause location based on speech duration
                #     if self.total_speech_duration < 3.0:
                #         self.pause_location = "within_sentence"
                #     else:
                #         self.pause_location = "between_sentences"

                # Determine what kind of silence this is
                silence_duration = self.silence_frames * frame_duration

                if self.in_thinking_mode:
                    # User explicitly asked to wait
                    if silence_duration > self.current_max_silence:
                        logger.info("Thinking pause exceeded max duration")
                        return self._end_speech(), None  # No pause_info
                    return "silence", None

                elif silence_duration > self.current_thinking_threshold:
                    # Long pause - might be thinking or done speaking
                    if self.total_speech_duration < MIN_SPEECH_DURATION:
                        # Too short to be meaningful
                        return "silence", None
                    logger.debug(f"Long pause detected: {silence_duration:.2f}s")
                    return self._end_speech(), None  # No pause_info

                elif silence_duration > self.current_silence_threshold:
                    # Standard silence threshold reached
                    if self.total_speech_duration >= MIN_SPEECH_DURATION:
                        logger.debug(
                            f"Silence threshold reached: {silence_duration:.2f}s"
                        )
                        return self._end_speech(), None  # No pause_info
                    else:
                        logger.debug("Speech too short, waiting for more")
                        return "silence", None

                return "silence", None

            return None, None

    # CALIBRATION CODE - COMMENTED OUT
    # def _create_pause_info(self, duration: float, was_thinking: bool) -> dict:
    #     """Create pause info dictionary."""
    #     return {
    #         "duration": duration,
    #         "location": self.pause_location,
    #         "was_thinking_pause": was_thinking,
    #     }

    def _end_speech(self) -> str:
        """Handle speech ending."""
        self.is_speaking = False
        self.last_speech_end_time = time.time()
        logger.info(f"Speech ended (duration: {self.total_speech_duration:.2f}s)")
        return "speech_end"

    # CALIBRATION CODE - COMMENTED OUT
    # def _end_calibration(self):
    #     """End calibration phase and apply learned thresholds."""
    #     self.is_calibrating = False

    #     # Remove calibration buffer
    #     self.current_silence_threshold = self.user_profile.silence_threshold
    #     self.current_thinking_threshold = self.user_profile.thinking_pause_threshold
    #     self.current_max_silence = self.user_profile.max_silence_before_interrupt

    #     logger.info(
    #         f"Calibration complete! Applied thresholds: "
    #         f"silence={self.current_silence_threshold:.2f}s, "
    #         f"thinking={self.current_thinking_threshold:.2f}s, "
    #         f"max={self.current_max_silence:.2f}s"
    #     )

    def enter_thinking_mode(self):
        """Enter thinking mode - more tolerant of silence."""
        self.in_thinking_mode = True
        logger.info("Entered thinking mode - will wait longer for user")

    def exit_thinking_mode(self):
        """Exit thinking mode - return to normal conversation."""
        self.in_thinking_mode = False
        logger.info("Exited thinking mode")

    def adjust_for_more_time(self):
        """Temporarily adjust thresholds when user needs more time."""
        self.current_silence_threshold *= 1.5
        self.current_thinking_threshold *= 1.5
        self.current_max_silence *= 1.5
        logger.info(
            f"Adjusted thresholds for more thinking time: "
            f"silence={self.current_silence_threshold:.2f}s"
        )

    def reset(self):
        """Reset all state counters."""
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.total_speech_duration = 0.0
        self.total_silence_duration = 0.0
        self.ring_buffer.clear()
        self.in_thinking_mode = False
        # CALIBRATION CODE - COMMENTED OUT
        # self.current_pause_start = None
        # self.resumed_after_pause = False
        logger.debug("VAD state reset")

    def get_speech_duration(self) -> float:
        """Get total speech duration in seconds."""
        return self.total_speech_duration

    def get_silence_duration(self) -> float:
        """Get current silence duration in seconds."""
        return self.silence_frames * (self.frame_duration_ms / 1000.0)
