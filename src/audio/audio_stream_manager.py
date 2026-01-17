"""
Main audio stream manager that coordinates capture, VAD, transcription, and learning.
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
    CALIBRATION_LEARNING_RATE,
    CHANNELS,
    CHUNK_SIZE,
    CONTINUE_COMMANDS,
    DEFAULT_USER_ID,
    MAX_RECORDING_DURATION,
    NEED_MORE_TIME_COMMANDS,
    POST_CALIBRATION_LEARNING_RATE,
    RECALIBRATE_COMMANDS,
    SAMPLE_RATE,
    THINKING_COMMANDS,
    VAD_FRAME_DURATION_MS,
)
from src.audio.audio_device_manager import AudioDeviceManager
from src.audio.calibration_manager import CalibrationManager
from src.audio.speaking_rate import SpeakingRateCalculator
from src.audio.user_profile import PausePattern, UserProfileManager
from src.audio.vad_detector import VADDetector
from src.audio.whisper_transcriber import WhisperTranscriber


class AudioStreamManager:
    """
    Manages the complete audio pipeline: capture -> VAD -> transcription -> learning.
    """

    def __init__(
        self,
        on_transcription: Optional[Callable[[str], None]] = None,
        user_id: str = DEFAULT_USER_ID,
    ):
        """
        Initialize the audio stream manager.

        Args:
            on_transcription: Callback function called with transcribed text
            user_id: User identifier for profile management
        """
        # Load or create user profile
        self.profile_manager = UserProfileManager()
        self.user_profile = self.profile_manager.load_profile(user_id)

        # Initialize components with user profile
        self.device_manager = AudioDeviceManager()
        self.vad = VADDetector(user_profile=self.user_profile)
        self.transcriber = WhisperTranscriber()
        self.speaking_rate_calc = SpeakingRateCalculator()

        # Calibration manager for style analysis
        self.calibration_manager = CalibrationManager(
            self.profile_manager, self.user_profile
        )

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

        # Track if we've triggered style analysis for this session
        self.style_analysis_started = False

        logger.info(
            f"AudioStreamManager initialized for user '{user_id}' "
            f"(calibrated: {self.user_profile.is_calibrated})"
        )

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

            if self.vad.is_calibrating:
                logger.info("Audio stream started - CALIBRATION MODE (first 45-60s)")
            else:
                logger.info("Audio stream started - now listening")

        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop the audio capture and processing pipeline."""
        logger.info("Stopping audio stream...")
        self.is_running = False

        # Save profile before stopping
        if self.user_profile:
            self.profile_manager.save_profile(self.user_profile)

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

                    # Process with VAD (returns tuple now)
                    vad_result, pause_info = self.vad.process_frame(frame)

                    # Handle pause information
                    if pause_info:
                        pause = PausePattern(
                            duration=pause_info["duration"],
                            location=pause_info["location"],
                            was_thinking_pause=pause_info["was_thinking_pause"],
                        )
                        self.profile_manager.add_pause(self.user_profile, pause)

                    if vad_result == "speech_start":
                        self.is_listening = True
                        self.audio_buffer = [frame]
                        self.speaking_rate_calc.start_speech_segment()
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

                    # Update speaking rate
                    wpm = self.speaking_rate_calc.end_speech_segment(text)
                    if wpm:
                        learning_rate = (
                            CALIBRATION_LEARNING_RATE
                            if self.vad.is_calibrating
                            else POST_CALIBRATION_LEARNING_RATE
                        )
                        self.profile_manager.update_speaking_rate(
                            self.user_profile, wpm, learning_rate
                        )

                    # Update pause statistics
                    learning_rate = (
                        CALIBRATION_LEARNING_RATE
                        if self.vad.is_calibrating
                        else POST_CALIBRATION_LEARNING_RATE
                    )
                    self.profile_manager.update_statistics(
                        self.user_profile, learning_rate
                    )

                    # Update word count for calibration
                    if self.vad.is_calibrating:
                        word_count = len(text.split())
                        self.user_profile.total_words_spoken += word_count
                        self.user_profile.calibration_time = (
                            time.time() - self.vad.calibration_start_time
                        )

                        # Collect transcripts for style analysis
                        self.calibration_manager.add_calibration_transcript(text)

                    # Check if calibration just completed
                    if (
                        not self.vad.is_calibrating
                        and not self.user_profile.is_calibrated
                    ):
                        self.profile_manager.complete_calibration(self.user_profile)

                    # Start style analysis if calibration is done and we haven't started yet
                    if (
                        not self.vad.is_calibrating
                        and self.user_profile.is_calibrated
                        and not self.style_analysis_started
                        and len(self.calibration_manager.calibration_transcripts) > 0
                    ):
                        self.style_analysis_started = True
                        logger.info(
                            "Starting background style analysis with HelpingAI..."
                        )
                        self.calibration_manager.start_style_analysis(
                            callback=self._on_style_analysis_complete
                        )

                    # Check for special commands
                    text_lower = text.lower()

                    if any(cmd in text_lower for cmd in RECALIBRATE_COMMANDS):
                        logger.info("User requested recalibration")
                        self.profile_manager.reset_calibration(self.user_profile)
                        self.vad = VADDetector(user_profile=self.user_profile)
                        self.speaking_rate_calc.reset()

                    elif any(cmd in text_lower for cmd in NEED_MORE_TIME_COMMANDS):
                        logger.info("User needs more time")
                        self.vad.adjust_for_more_time()

                    elif any(cmd in text_lower for cmd in THINKING_COMMANDS):
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

    def _on_style_analysis_complete(self, style_summary: str):
        """
        Called when style analysis completes in background.

        Args:
            style_summary: The generated style summary
        """
        logger.info("Style analysis complete! Summary available for Gemini.")
        logger.debug(f"Style summary preview: {style_summary[:200]}...")

    def get_style_summary_for_gemini(self) -> Optional[str]:
        """
        Get the formatted style summary for Gemini.

        Returns:
            Formatted style summary, or None if not available yet
        """
        return self.calibration_manager.get_style_summary_for_gemini()

    def cleanup(self):
        """Clean up all resources."""
        self.stop()
        self.calibration_manager.cleanup()
        self.device_manager.cleanup()
        self.audio.terminate()
        logger.info("AudioStreamManager cleaned up")
