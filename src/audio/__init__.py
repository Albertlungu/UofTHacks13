"""
Audio processing package for Goonvengers.

This package handles:
- Audio capture from AirPods
- Voice Activity Detection (VAD)
- Speech-to-text transcription using Whisper
- Error handling with audio feedback
"""

from src.audio.audio_device_manager import AudioDeviceManager
from src.audio.audio_stream_manager import AudioStreamManager
from src.audio.error_handler import AudioErrorHandler, setup_logging
from src.audio.vad_detector import VADDetector
from src.audio.whisper_transcriber import WhisperTranscriber

__all__ = [
    "AudioStreamManager",
    "AudioDeviceManager",
    "WhisperTranscriber",
    "VADDetector",
    "AudioErrorHandler",
    "setup_logging",
]
