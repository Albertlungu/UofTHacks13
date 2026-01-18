"""
Error handling with audio feedback through AirPods.
"""

import math
import sys
from typing import Optional

import numpy as np
import pyaudio
from loguru import logger


class AudioErrorHandler:
    """Handles errors and reports them through audio feedback."""

    def __init__(self, output_device_index: Optional[int] = None):
        """
        Initialize the error handler.

        Args:
            output_device_index: Audio output device index (e.g., AirPods)
        """
        self.output_device_index = output_device_index
        self.audio = pyaudio.PyAudio()

        # Error message templates
        self.error_messages = {
            "airpods_disconnected": "AirPods disconnected. Please reconnect your AirPods.",
            "whisper_failed": "Speech recognition failed. Please try speaking again.",
            "audio_stream_error": "Audio stream error detected. Attempting to restart.",
            "device_not_found": "Audio device not found. Please check your connections.",
            "transcription_timeout": "Transcription is taking longer than expected.",
            "unknown_error": "An unexpected error occurred. Check the console for details.",
        }

        logger.info("AudioErrorHandler initialized")

    def handle_error(
        self, error_type: str, exception: Optional[Exception] = None, speak: bool = True
    ):
        """
        Handle an error by logging and optionally speaking it.

        Args:
            error_type: Type of error (key in error_messages)
            exception: Optional exception object
            speak: Whether to speak the error message
        """
        # Get error message
        message = self.error_messages.get(
            error_type, self.error_messages["unknown_error"]
        )

        # Log to console
        if exception:
            logger.error(f"[{error_type}] {message} | Exception: {exception}")
        else:
            logger.error(f"[{error_type}] {message}")

        # Speak error if requested
        if speak:
            self._speak_error(message)

    def _speak_error(self, message: str):
        """
        Speak an error message through the audio output.
        Note: This is a placeholder. For actual TTS, integrate with ElevenLabs.

        Args:
            message: Error message to speak
        """
        try:
            # For now, just play a notification tone
            # In production, you'd use ElevenLabs TTS here
            logger.info(f'Would speak: "{message}"')
            self._play_notification_tone()

        except Exception as e:
            logger.error(f"Failed to speak error message: {e}")

    def _play_notification_tone(self, frequency: int = 440, duration_ms: int = 200):
        """
        Play a simple notification tone.

        Args:
            frequency: Tone frequency in Hz
            duration_ms: Duration in milliseconds
        """
        try:
            # Generate a simple sine wave using numpy
            sample_rate = 44100
            duration_sec = duration_ms / 1000.0
            num_samples = int(sample_rate * duration_sec)

            # Create sine wave
            t = np.linspace(0, duration_sec, num_samples, False)
            tone = np.sin(2 * np.pi * frequency * t)

            # Convert to int16 format
            tone_int16 = (tone * 32767).astype(np.int16)

            # Play through PyAudio
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=self.output_device_index,
            )

            stream.write(tone_int16.tobytes())
            stream.stop_stream()
            stream.close()

        except Exception as e:
            logger.error(f"Failed to play notification tone: {e}")

    def log_info(self, message: str):
        """Log an info message."""
        logger.info(message)

    def log_warning(self, message: str):
        """Log a warning message."""
        logger.warning(message)

    def log_debug(self, message: str):
        """Log a debug message."""
        logger.debug(message)

    def cleanup(self):
        """Clean up resources."""
        if self.audio:
            self.audio.terminate()
            logger.info("AudioErrorHandler cleaned up")


def setup_logging(level: str = "INFO"):
    """
    Set up logging configuration for the entire application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=level,
    )

    # Add file handler (always DEBUG for file)
    logger.add(
        "logs/shadow_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    )

    logger.info(f"Logging configured (console level: {level}, file level: DEBUG)")
