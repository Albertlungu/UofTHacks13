"""
Local Whisper transcription with faster-whisper for optimal performance.
"""

from typing import Any, Dict, Optional

import numpy as np
from faster_whisper import WhisperModel
from loguru import logger

from src.audio.audio_config import SAMPLE_RATE, WHISPER_LANGUAGE, WHISPER_MODEL


class WhisperTranscriber:
    """Handles local Whisper transcription using faster-whisper."""

    def __init__(
        self,
        model_size: str = WHISPER_MODEL,
        device: str = "cpu",
        custom_vocabulary: Optional[str] = None,
    ):
        """
        Initialize the Whisper transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on ('cpu', 'cuda', or 'auto')
            custom_vocabulary: Optional custom vocabulary/slang to help Whisper recognize specific words
        """
        self.model_size = model_size
        self.device = device
        self.custom_vocabulary = custom_vocabulary
        self.model: Optional[WhisperModel] = None

        logger.info(f"Initializing Whisper model: {model_size} on {device}")
        if custom_vocabulary:
            logger.info(f"Custom vocabulary: {custom_vocabulary}")
        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            # Use compute_type="int8" for faster CPU inference
            # Use "float16" if you have a GPU
            compute_type = "int8" if self.device == "cpu" else "float16"

            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type,
                download_root=None,  # Uses default cache directory
            )
            logger.info(
                f"Whisper model loaded successfully (compute_type: {compute_type})"
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Numpy array of audio samples (float32, normalized to [-1, 1])

        Returns:
            Dictionary with 'text', 'language', and 'segments' keys, or None on failure
        """
        if self.model is None:
            logger.error("Whisper model not loaded")
            return None

        if audio_data is None or len(audio_data) == 0:
            logger.warning("Empty audio data provided")
            return None

        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize if not already
            max_val = np.abs(audio_data).max()
            if max_val > 1.0:
                audio_data = audio_data / max_val

            logger.debug(
                f"Transcribing audio (length: {len(audio_data) / SAMPLE_RATE:.2f}s)"
            )

            # Transcribe
            transcribe_params = {
                "audio": audio_data,
                "language": WHISPER_LANGUAGE,
                "task": "transcribe",
                "vad_filter": True,  # Additional VAD filtering
                "vad_parameters": {
                    "threshold": 0.5,
                    "min_speech_duration_ms": 250,
                    "max_speech_duration_s": 30,
                    "min_silence_duration_ms": 500,
                },
            }

            # Add custom vocabulary if provided
            if self.custom_vocabulary:
                transcribe_params["initial_prompt"] = self.custom_vocabulary

            segments, info = self.model.transcribe(**transcribe_params)

            # Collect all segments
            segment_list = []
            full_text = ""

            for segment in segments:
                segment_list.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                    }
                )
                full_text += segment.text.strip() + " "

            full_text = full_text.strip()

            if not full_text:
                logger.warning("Transcription resulted in empty text")
                return None

            result = {
                "text": full_text,
                "language": info.language,
                "language_probability": info.language_probability,
                "segments": segment_list,
            }

            logger.info(
                f'Transcription complete: "{full_text}" (lang: {info.language})'
            )
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def transcribe_bytes(
        self, audio_bytes: bytes, sample_width: int = 2
    ) -> Optional[Dict[str, any]]:
        """
        Transcribe audio from raw bytes.

        Args:
            audio_bytes: Raw audio bytes (int16 PCM)
            sample_width: Bytes per sample (default: 2 for int16)

        Returns:
            Transcription result dictionary or None
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

            # Convert to float32 and normalize to [-1, 1]
            audio_float = audio_array.astype(np.float32) / 32768.0

            return self.transcribe(audio_float)

        except Exception as e:
            logger.error(f"Failed to process audio bytes: {e}")
            return None

    def update_custom_vocabulary(self, vocabulary: Optional[str]):
        """
        Update the custom vocabulary for transcription.

        Args:
            vocabulary: New custom vocabulary string, or None to disable
        """
        self.custom_vocabulary = vocabulary
        if vocabulary:
            logger.info(f"Updated custom vocabulary: {vocabulary}")
        else:
            logger.info("Custom vocabulary disabled")

    def is_model_loaded(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.model is not None

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            self.model = None
            logger.info("Whisper model unloaded")
