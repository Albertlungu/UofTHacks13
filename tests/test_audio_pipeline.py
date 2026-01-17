"""
Tests for the audio pipeline components.
"""

import numpy as np
import pytest

from src.audio.audio_device_manager import AudioDeviceManager
from src.audio.vad_detector import VADDetector
from src.audio.whisper_transcriber import WhisperTranscriber


class TestAudioDeviceManager:
    """Tests for AudioDeviceManager."""

    def test_list_devices(self):
        """Test listing audio devices."""
        manager = AudioDeviceManager()
        devices = manager.list_all_devices()

        assert isinstance(devices, list)
        assert len(devices) > 0

        # Check device structure
        for device in devices:
            assert "index" in device
            assert "name" in device
            assert "max_input_channels" in device
            assert "max_output_channels" in device

        manager.cleanup()

    def test_find_default_devices(self):
        """Test finding default devices."""
        manager = AudioDeviceManager()

        input_device = manager.get_default_input_device()
        output_device = manager.get_default_output_device()

        assert isinstance(input_device, int)
        assert isinstance(output_device, int)
        assert input_device >= 0
        assert output_device >= 0

        manager.cleanup()


class TestVADDetector:
    """Tests for VADDetector."""

    def test_vad_initialization(self):
        """Test VAD initialization."""
        vad = VADDetector()

        assert vad.sample_rate == 16000
        assert not vad.is_speaking
        assert vad.speech_frames == 0
        assert vad.silence_frames == 0

    def test_vad_reset(self):
        """Test VAD reset."""
        vad = VADDetector()

        # Simulate some state
        vad.is_speaking = True
        vad.speech_frames = 100
        vad.total_speech_duration = 5.0

        # Reset
        vad.reset()

        assert not vad.is_speaking
        assert vad.speech_frames == 0
        assert vad.total_speech_duration == 0.0

    def test_thinking_mode(self):
        """Test thinking mode."""
        vad = VADDetector()

        assert not vad.in_thinking_mode

        vad.enter_thinking_mode()
        assert vad.in_thinking_mode

        vad.exit_thinking_mode()
        assert not vad.in_thinking_mode


class TestWhisperTranscriber:
    """Tests for WhisperTranscriber."""

    def test_transcriber_initialization(self):
        """Test transcriber initialization."""
        transcriber = WhisperTranscriber(model_size="tiny")

        assert transcriber.model_size == "tiny"
        assert transcriber.is_model_loaded()

    def test_transcribe_empty_audio(self):
        """Test transcribing empty audio."""
        transcriber = WhisperTranscriber(model_size="tiny")

        empty_audio = np.array([], dtype=np.float32)
        result = transcriber.transcribe(empty_audio)

        assert result is None

    def test_transcribe_silence(self):
        """Test transcribing silence."""
        transcriber = WhisperTranscriber(model_size="tiny")

        # Generate 1 second of silence
        silence = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(silence)

        # Silence might return None or empty text
        if result:
            assert result.get("text") == "" or result is None

    def test_audio_normalization(self):
        """Test audio normalization."""
        transcriber = WhisperTranscriber(model_size="tiny")

        # Create audio that needs normalization
        audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
        audio_float = audio.astype(np.float32)

        # This shouldn't crash
        result = transcriber.transcribe(audio_float)

        # Result might be None (noise) but shouldn't crash
        assert result is None or isinstance(result, dict)


@pytest.fixture
def audio_device_manager():
    """Fixture for AudioDeviceManager."""
    manager = AudioDeviceManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def vad_detector():
    """Fixture for VADDetector."""
    return VADDetector()


@pytest.fixture
def whisper_transcriber():
    """Fixture for WhisperTranscriber."""
    return WhisperTranscriber(model_size="tiny")
