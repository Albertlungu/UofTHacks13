# Audio Pipeline Setup Guide

This guide explains how to set up and test the AirPods -> Whisper audio pipeline for the Goonvengers AI companion.

## Overview

The audio pipeline captures audio from AirPods, uses Voice Activity Detection (VAD) to detect when you're speaking, and transcribes your speech using local Whisper. No audio files are saved - everything is streamed directly.

## Architecture

```
AirPods Microphone 
    ↓
PyAudio Stream (16kHz, mono, int16)
    ↓
VAD Detector (WebRTC VAD)
    ↓
Audio Buffer (accumulated during speech)
    ↓
Whisper Transcriber (faster-whisper, local)
    ↓
Text Output → [Your Callback Function]
```

## Prerequisites

- macOS (tested on Darwin 25.3.0)
- Python 3.9 or higher
- AirPods or other Bluetooth headphones
- Homebrew (for macOS dependencies)

## Installation

### Automated Setup

Run the setup script:

```bash
./setup.sh
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Download the Whisper model
4. Set up logging directories
5. Run basic tests

### Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install portaudio (required for PyAudio on macOS)
brew install portaudio

# Install Python dependencies
pip install -r requirements.txt

# Test installation
python -c "from faster_whisper import WhisperModel; print('OK')"
```

## Configuration

Audio settings can be adjusted in `src/audio/audio_config.py`:

### VAD Settings
- `VAD_MODE`: Aggressiveness (0-3, higher = more aggressive)
- `INITIAL_SILENCE_THRESHOLD`: Seconds of silence before transcription (default: 1.5s)
- `THINKING_PAUSE_THRESHOLD`: Long pause detection (default: 3.0s)
- `MAX_SILENCE_BEFORE_INTERRUPT`: Max silence tolerance (default: 5.0s)

### Whisper Settings
- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)
  - **tiny**: Fastest, least accurate (~1GB RAM)
  - **base**: Good balance (~1GB RAM) ⭐ Recommended
  - **small**: Better accuracy (~2GB RAM)
  - **medium**: High accuracy (~5GB RAM)
  - **large**: Best accuracy (~10GB RAM)

### Audio Quality
- `SAMPLE_RATE`: 16000 Hz (optimal for Whisper)
- `CHANNELS`: 1 (mono)
- `CHUNK_SIZE`: 1024 frames

## Usage

### Running the Demo

1. **Connect your AirPods** to your Mac
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Run the demo:
   ```bash
   python -m src.audio.demo
   ```
4. **Speak into your AirPods** - the system will automatically detect when you start/stop speaking

### Special Commands

The system recognizes special commands:

- **Thinking mode**: Say "wait", "hold on", "let me think"
  - System will wait longer before interrupting
  
- **Resume**: Say "okay", "continue", "go ahead"
  - Return to normal conversation mode

### Output

When you speak, you'll see:
```
>>> USER: [Your transcribed speech here]
```

Logs are written to:
- Console (with colors)
- `logs/goonvengers_[timestamp].log`

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_audio_pipeline.py::TestWhisperTranscriber -v

# With coverage
pytest tests/ --cov=src/audio --cov-report=html
```

## Troubleshooting

### AirPods Not Detected

If AirPods aren't found:

1. Check Bluetooth connection in System Settings
2. Make sure AirPods are selected as input device
3. List available devices:
   ```python
   from src.audio import AudioDeviceManager
   manager = AudioDeviceManager()
   for device in manager.list_all_devices():
       print(f"{device['index']}: {device['name']}")
   ```

### PyAudio Installation Fails

On macOS, install portaudio first:
```bash
brew install portaudio
pip install pyaudio
```

### Whisper Model Download Issues

If the model doesn't download:
```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
```

### Low Transcription Quality

Try these adjustments:

1. **Use a better model**: Change `WHISPER_MODEL` to "small" or "medium"
2. **Adjust VAD sensitivity**: Increase `VAD_MODE` to 3
3. **Check microphone position**: Speak clearly toward AirPods
4. **Reduce background noise**

### High Latency

To reduce latency:

1. **Use smaller model**: Set `WHISPER_MODEL` to "tiny" or "base"
2. **Reduce silence threshold**: Lower `INITIAL_SILENCE_THRESHOLD` to 1.0s
3. **Use GPU** (if available):
   ```python
   transcriber = WhisperTranscriber(device="cuda")
   ```

## Integration with Goonvengers

To integrate with the full Goonvengers system:

```python
from src.audio import AudioStreamManager

def on_transcription(text: str):
    # 1. Send to emotion detection
    emotion = detect_emotion(text)
    
    # 2. Store in Amplitude
    amplitude.track('user_speech', {'text': text, 'emotion': emotion})
    
    # 3. Send to Gemini
    response = gemini.generate(text, emotion=emotion)
    
    # 4. Speak response via ElevenLabs
    elevenlabs.speak(response)

# Create and start stream
stream = AudioStreamManager(on_transcription=on_transcription)
stream.setup()
stream.start()
```

## Performance Metrics

Expected performance with different models on M1/M2 Mac:

| Model  | Latency | Accuracy | RAM Usage |
|--------|---------|----------|-----------|
| tiny   | ~0.5s   | Good     | ~1GB      |
| base   | ~1.0s   | Better   | ~1GB      |
| small  | ~2.0s   | Great    | ~2GB      |
| medium | ~4.0s   | Excellent| ~5GB      |

## Files Structure

```
src/audio/
├── audio_config.py           # Configuration constants
├── audio_device_manager.py   # Device detection and management
├── vad_detector.py           # Voice Activity Detection
├── whisper_transcriber.py    # Whisper integration
├── audio_stream_manager.py   # Main pipeline coordinator
├── error_handler.py          # Error handling and logging
├── demo.py                   # Demo application
└── __init__.py              # Package exports
```

## Next Steps

After the audio pipeline is working:

1. **Emotion Detection**: Integrate emotion model for speech analysis
2. **Gemini Integration**: Connect transcribed text to Gemini API
3. **ElevenLabs**: Add voice response synthesis
4. **Amplitude**: Store conversation history
5. **Camera Integration**: Add facial expression analysis
6. **Full System**: Combine all components

## Support

If you encounter issues:

1. Check logs in `logs/` directory
2. Run with debug logging: Set `logger.level = "DEBUG"`
3. Test individual components with pytest
4. Verify audio devices are properly connected

## License

[To be determined]
