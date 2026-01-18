# Audio Pipeline Setup Guide

This guide explains how to set up and test the AirPods -> Whisper audio pipeline with **adaptive learning** for the shadow AI companion.

## Overview

The audio pipeline captures audio from AirPods, uses Voice Activity Detection (VAD) to detect when you're speaking, and transcribes your speech using local Whisper. The system **learns your speech patterns** during the first 45-60 seconds and adapts to your natural speaking style.

### Key Features

- **Adaptive Silence Detection**: Learns your natural pause patterns
- **Speaking Rate Tracking**: Measures and adapts to your words-per-minute
- **Pause Pattern Learning**: Tracks where you pause (within/between sentences)
- **Thinking Pause Detection**: Distinguishes between "done speaking" and "still thinking"
- **User Profiles**: Saves learned patterns for future sessions
- **Continuous Learning**: Keeps updating (slowly) after initial calibration

## Architecture

```
AirPods Microphone 
    ↓
PyAudio Stream (16kHz, mono, int16)
    ↓
VAD Detector (WebRTC VAD + Adaptive Learning)
    ↓
Pause Pattern Tracking
    ↓
Audio Buffer (accumulated during speech)
    ↓
Whisper Transcriber (faster-whisper, local)
    ↓
Speaking Rate Calculator (WPM)
    ↓
User Profile Update (learning)
    ↓
Text Output → [Your Callback Function]
```

## Prerequisites

- macOS (tested on Darwin 25.3.0)
- **Python 3.11, 3.12, or 3.13** (NOT 3.14 - onnxruntime not supported yet)
- AirPods or other Bluetooth headphones
- Homebrew (for macOS dependencies)

## Installation

### Step 1: Install System Dependencies

```bash
# Install FFmpeg and portaudio
brew install ffmpeg pkg-config portaudio
```

### Step 2: Set Up Python Environment

```bash
# Use Python 3.12 (recommended)
brew install python@3.12

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install setuptools (required)
pip install setuptools

# Install project dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python verify_installation.py
```

You should see green checkmarks for all components.

## How Adaptive Learning Works

### Phase 1: Calibration (First 45-60 seconds)

During the first minute, the system:

1. **Uses lenient thresholds** (+2 seconds buffer) to avoid cutting you off
2. **Tracks all pauses**:
   - Duration of each pause
   - Location (within/between sentences)
   - Whether you resumed speaking (= thinking pause)
3. **Measures speaking rate** (words per minute)
4. **Collects at least 100 words** before completing calibration
5. **Extends calibration** if not enough data collected

After calibration, the system calculates:
- Average within-sentence pause duration
- Average between-sentence pause duration
- Average thinking pause duration
- Your typical speaking rate (WPM)

### Phase 2: Adapted Behavior (After Calibration)

The system applies learned thresholds:
- `silence_threshold` = avg_between_sentence_pause + 0.5s
- `thinking_pause_threshold` = avg_thinking_pause * 0.8
- `max_silence_before_interrupt` = avg_thinking_pause * 1.5

### Phase 3: Continuous Learning (Ongoing)

After calibration, the system continues learning at 10% learning rate:
- Slowly adapts to changes in your speech
- Updates saved profile periodically
- Maintains stability while still being responsive

## Configuration

### Calibration Settings (`src/audio/audio_config.py`)

```python
CALIBRATION_DURATION = 60.0  # 45-60 seconds
CALIBRATION_SILENCE_BUFFER = 2.0  # Extra patience during calibration
MIN_CALIBRATION_SENTENCES = 3  # Minimum data needed
CALIBRATION_LEARNING_RATE = 1.0  # Full learning during calibration
POST_CALIBRATION_LEARNING_RATE = 0.1  # Slower learning after
```

### VAD Settings

- `VAD_MODE`: Aggressiveness (0-3, higher = more aggressive)
- Thresholds are now **adaptive** and loaded from user profile

### Whisper Settings

- `WHISPER_MODEL`: "base" (recommended)
  - **tiny**: Fastest (~0.5s latency)
  - **base**: Best balance (~1s latency) ⭐
  - **small**: Better accuracy (~2s latency)

## Usage

### Running the Demo

1. **Connect your AirPods** to your Mac
2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```
3. **Run the demo**:
   ```bash
   python -m src.audio.demo
   ```

### First Time Use

On your first run, you'll see:
```
READY TO LISTEN (Calibration Mode)
========================================

First 45-60 seconds: Learning your speech patterns...
Please speak naturally - the system is adapting to you!
```

**During calibration:**
- Speak naturally about anything
- Take pauses as you normally would
- If you resume speaking after a pause, it's marked as a "thinking pause"
- System is extra patient - won't cut you off

**After calibration:**
```
Calibration complete! Applied thresholds:
  silence=1.8s, thinking=2.5s, max=4.0s
```

### Special Commands

The system recognizes these voice commands:

- **"wait", "hold on", "let me think"**
  - Enters thinking mode (extra patience)
  
- **"okay", "continue", "go ahead"**
  - Exits thinking mode (back to normal)

- **"need more time", "slower today"**
  - Temporarily increases all thresholds by 1.5x
  - Use when you're tired or need extra thinking time

- **"recalibrate", "reset calibration"**
  - Clears learned profile and starts fresh calibration
  - Use if system isn't adapting well

### User Profiles

Profiles are automatically saved to `./data/profiles/default_user.json`

Example profile:
```json
{
  "user_id": "default_user",
  "avg_within_sentence_pause": 0.6,
  "avg_between_sentence_pause": 1.2,
  "avg_thinking_pause": 2.8,
  "words_per_minute": 145.3,
  "silence_threshold": 1.7,
  "thinking_pause_threshold": 2.24,
  "max_silence_before_interrupt": 4.2,
  "is_calibrated": true,
  "total_words_spoken": 147
}
```

### Viewing Your Profile

After running once, your profile stats are shown:
```
READY TO LISTEN (Calibrated Profile)
========================================

Your speech profile:
  - Speaking rate: 145.3 WPM
  - Silence threshold: 1.70s
  - Thinking pause: 2.24s
```

## Testing

### System Test

```bash
python test_system.py
```

This tests all components including the new adaptive learning system.

### Unit Tests

```bash
pytest tests/ -v
```

## Troubleshooting

### Python 3.14 Issues

If you get "No matching distribution found for onnxruntime":
```bash
# Use Python 3.12 instead
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg Missing

If you get "Package 'libavformat' not found":
```bash
brew install ffmpeg pkg-config
```

### Calibration Not Completing

If calibration extends beyond 60 seconds:
- System needs at least 100 words spoken
- Keep speaking naturally
- System will complete when it has enough data

### System Too Sensitive / Not Sensitive Enough

1. **Recalibrate**: Say "recalibrate" while using the system
2. **Manual adjustment**: Edit thresholds in `./data/profiles/default_user.json`
3. **Delete profile**: Remove JSON file to start fresh

### Profile Not Saving

Check:
- `./data/profiles/` directory exists
- You have write permissions
- Check logs for save errors

## Integration Example

```python
from src.audio import AudioStreamManager

# Create stream manager with user ID
stream = AudioStreamManager(
    on_transcription=on_transcription,
    user_id="albert"  # Multi-user ready
)

# Setup and start
stream.setup()
stream.start()

# Profile automatically loads and saves
# System adapts to this specific user's speech patterns
```

## Architecture Details

### Files Structure

```
src/audio/
├── audio_config.py           # Configuration constants
├── audio_device_manager.py   # Device detection
├── vad_detector.py           # VAD with calibration
├── whisper_transcriber.py    # Whisper integration
├── user_profile.py          # Profile management (NEW)
├── speaking_rate.py         # WPM calculation (NEW)
├── audio_stream_manager.py   # Main coordinator (UPDATED)
├── error_handler.py          # Error handling
├── demo.py                   # Demo application
└── __init__.py              # Package exports

data/profiles/
└── default_user.json        # Saved user profile
```

### Learning Algorithm

**Pause Classification:**
1. When silence starts → record timestamp and location
2. If user resumes speaking → mark as "thinking pause"
3. If user says continue command → mark as "not thinking"
4. If transcription completes → mark as "end of thought"

**Threshold Calculation:**
```python
silence_threshold = max(avg_between_sentence + 0.5, 1.0)
thinking_threshold = max(avg_thinking * 0.8, silence_threshold + 0.5)
max_silence = max(avg_thinking * 1.5, thinking_threshold + 1.0)
```

**Exponential Moving Average:**
```python
new_value = learning_rate * measured_value + (1 - learning_rate) * old_value
```
- Calibration: learning_rate = 1.0 (full weight on new data)
- Post-calibration: learning_rate = 0.1 (slow adaptation)

## Performance

Expected performance on M1/M2 Mac:

| Phase        | Action         | Time    |
|--------------|----------------|---------|
| Startup      | Load model     | 2-3s    |
| Calibration  | Learning       | 45-60s  |
| Transcription| Per utterance  | 1-2s    |
| Profile save | Periodic       | <0.1s   |

## Next Steps

After the audio pipeline is working:

1. **Emotion Detection**: Analyze tone and emotion from audio/text
2. **Gemini Integration**: Generate responses based on personality
3. **ElevenLabs**: Synthesize voice responses
4. **Camera Tracking**: Follow user with cameras
5. **Amplitude**: Store conversation history and patterns
6. **Multi-user**: Support multiple user profiles with voice recognition

## Support

If you encounter issues:

1. Check logs: `logs/shadow_*.log`
2. Run system test: `python test_system.py`
3. Check profile: `cat data/profiles/default_user.json`
4. Enable debug logging in code: `logger.level = "DEBUG"`

## License

[To be determined]
