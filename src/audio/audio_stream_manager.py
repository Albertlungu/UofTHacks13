"""
Main audio stream manager that coordinates capture, VAD, and transcription.
"""

import queue
import threading
import time
from typing import Callable, Optional

import numpy as np
import pyaudio
from loguru import logger

from src.audio.audio_config import (
    BUFFER_PADDING_MS,
    CHANNELS,
    CHUNK_SIZE,
    CONTINUE_COMMANDS,
    MAX_RECORDING_DURATION,
    SAMPLE_RATE,
    THINKING_COMMANDS,
    VAD_FRAME_DURATION_MS,
)
from src.audio.audio_device_manager import AudioDeviceManager
from src.audio.vad_detector import VADDetector
from src.audio.whisper_transcriber import WhisperTranscriber


class AudioStreamManager:
    """
    Manages the complete audio pipeline: capture -> VAD -> transcription.
    """

    def __init__(self, on_transcription: Optional[Callable[[str], None]] = None):
        """
        Initialize the audio stream manager.

        Args:
            on_transcription: Callback function called with transcribed text
        """
        self.device_manager = AudioDeviceManager()
        self.vad = VADDetector()
        self.transcriber = WhisperTranscriber()

        self.on_transcription = on_transcription

        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.input_device_index: Optional[int] = None

        # State management
        self.is_running = False
        self.is_listening = False
        self.audio_buffer = []
        self.frame_size = int(SAMPLE_RATE * VAD_FRAME_DURATION_MS / 1000)

        # Threading
        self.capture_thread: Optional[threading.Thread] = None
        self.transcription_queue = queue.Queue()
        self.transcription_thread: Optional[threading.Thread] = None

        logger.info("AudioStreamManager initialized")

    def setup(self) -> bool:
        """
        Set up audio devices and verify everything is ready.

        Returns:
            True if setup successful, False otherwise
        """
        logger.info("Setting up audio stream...")

        # Find AirPods
        airpods = self.device_manager.find_airpods()

        if airpods:
            self.input_device_index = airpods["input"]
            logger.info(f"Using AirPods input device: {self.input_device_index}")
        else:
            # Fall back to default
            logger.warning("AirPods not found, using default input device")
            self.input_device_index = self.device_manager.get_default_input_device()

        # Verify transcriber is ready
        if not self.transcriber.is_model_loaded():
            logger.error("Whisper model not loaded")
            return False

        logger.info("Audio setup complete")
        return True

    def start(self):
        """Start the audio capture and processing pipeline."""
        if self.is_running:
            logger.warning("Audio stream already running")
            return

        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=None,  # We'll use blocking read
            )

            self.is_running = True

            # Start capture thread
            self.capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True
            )
            self.capture_thread.start()

            # Start transcription thread
            self.transcription_thread = threading.Thread(
                target=self._transcription_loop, daemon=True
            )
            self.transcription_thread.start()

            logger.info("Audio stream started - now listening")

        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop the audio capture and processing pipeline."""
        logger.info("Stopping audio stream...")
        self.is_running = False

        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.transcription_thread:
            self.transcription_thread.join(timeout=2.0)

        # Close stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        logger.info("Audio stream stopped")

    def _capture_loop(self):
        """Main audio capture loop running in separate thread."""
        logger.info("Capture loop started")

        vad_frame_bytes = self.frame_size * 2  # int16 = 2 bytes per sample
        temp_buffer = b""

        while self.is_running:
            try:
                # Read audio chunk
                audio_data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                temp_buffer += audio_data

                # Process in VAD-sized frames
                while len(temp_buffer) >= vad_frame_bytes:
                    frame = temp_buffer[:vad_frame_bytes]
                    temp_buffer = temp_buffer[vad_frame_bytes:]

                    # Process with VAD
                    vad_result = self.vad.process_frame(frame)

                    if vad_result == "speech_start":
                        self.is_listening = True
                        self.audio_buffer = [frame]
                        logger.debug("Started recording")

                    elif vad_result == "speech_continue":
                        if self.is_listening:
                            self.audio_buffer.append(frame)

                            # Safety check: prevent buffer overflow
                            buffer_duration = (
                                len(self.audio_buffer) * VAD_FRAME_DURATION_MS / 1000.0
                            )
                            if buffer_duration > MAX_RECORDING_DURATION:
                                logger.warning(
                                    "Max recording duration reached, forcing transcription"
                                )
                                self._finalize_recording()

                    elif vad_result == "speech_end":
                        if self.is_listening and len(self.audio_buffer) > 0:
                            self._finalize_recording()

                    elif vad_result == "silence":
                        if self.is_listening:
                            self.audio_buffer.append(frame)

            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)

        logger.info("Capture loop ended")

    def _finalize_recording(self):
        """Finalize the current recording and queue for transcription."""
        if not self.audio_buffer:
            return

        # Combine all frames
        audio_bytes = b"".join(self.audio_buffer)

        logger.debug(f"Finalizing recording: {len(audio_bytes)} bytes")

        # Queue for transcription
        self.transcription_queue.put(audio_bytes)

        # Reset state
        self.audio_buffer = []
        self.is_listening = False
        self.vad.reset()

    def _transcription_loop(self):
        """Transcription processing loop running in separate thread."""
        logger.info("Transcription loop started")

        while self.is_running:
            try:
                # Wait for audio to transcribe (with timeout)
                try:
                    audio_bytes = self.transcription_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Transcribe
                logger.debug("Starting transcription...")
                result = self.transcriber.transcribe_bytes(audio_bytes)

                if result and result.get("text"):
                    text = result["text"].strip()
                    logger.info(f'Transcribed: "{text}"')

                    # Check for thinking commands
                    text_lower = text.lower()
                    if any(cmd in text_lower for cmd in THINKING_COMMANDS):
                        logger.info("User requested thinking time")
                        self.vad.enter_thinking_mode()
                    elif any(cmd in text_lower for cmd in CONTINUE_COMMANDS):
                        logger.info("User ready to continue")
                        self.vad.exit_thinking_mode()

                    # Call callback
                    if self.on_transcription:
                        try:
                            self.on_transcription(text)
                        except Exception as e:
                            logger.error(f"Error in transcription callback: {e}")
                else:
                    logger.warning("Transcription returned no text")

            except Exception as e:
                logger.error(f"Error in transcription loop: {e}")
                time.sleep(0.1)

        logger.info("Transcription loop ended")

    def cleanup(self):
        """Clean up all resources."""
        self.stop()
        self.device_manager.cleanup()
        self.audio.terminate()
        logger.info("AudioStreamManager cleaned up")
