"""
Audio processing package for Goonvengers.

This package handles:
- Audio capture from AirPods
- Voice Activity Detection (VAD) with adaptive learning
- Speech-to-text transcription using Whisper
- User profile management and calibration
- Speaking rate (WPM) tracking
- Error handling with audio feedback
"""

from src.audio.audio_device_manager import AudioDeviceManager
from src.audio.audio_stream_manager import AudioStreamManager
from src.audio.error_handler import AudioErrorHandler, setup_logging
from src.audio.speaking_rate import SpeakingRateCalculator
from src.audio.user_profile import PausePattern, UserProfileManager, UserSpeechProfile
from src.audio.vad_detector import VADDetector
from src.audio.whisper_transcriber import WhisperTranscriber

__all__ = [
    "AudioStreamManager",
    "AudioDeviceManager",
    "WhisperTranscriber",
    "VADDetector",
    "AudioErrorHandler",
    "setup_logging",
    "UserProfileManager",
    "UserSpeechProfile",
    "PausePattern",
    "SpeakingRateCalculator",
]
