# Quick Start Guide

Get the audio pipeline running in 5 minutes.

## Step 1: Install Dependencies

```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all Python packages
- Download the Whisper model
- Run verification tests

## Step 2: Verify Installation

```bash
source venv/bin/activate
python verify_installation.py
```

You should see green checkmarks for all components.

## Step 3: Connect AirPods

1. Open System Settings → Bluetooth
2. Connect your AirPods
3. Verify they're connected and selected as input device

## Step 4: Run the Demo

```bash
python -m src.audio.demo
```

You should see:
```
READY TO LISTEN
========================================

Speak naturally into your AirPods.
The system will detect when you start and stop speaking.
```

## Step 5: Test It

1. **Speak normally** into your AirPods
2. The system will automatically detect speech
3. When you pause, it will transcribe what you said
4. You'll see: `>>> USER: [your text here]`

### Try Special Commands

- Say **"wait, I'm thinking"** - system enters thinking mode
- Say **"okay, continue"** - returns to normal mode

## What's Happening?

```
Your Voice → AirPods → PyAudio → VAD → Buffer → Whisper → Text
```

1. **PyAudio** captures audio from AirPods (16kHz, mono)
2. **VAD** (Voice Activity Detection) detects when you speak
3. Audio is **buffered** while you're speaking
4. When silence detected, **Whisper** transcribes the buffer
5. **Text** is output and passed to callback function

## Troubleshooting

### AirPods not detected
```bash
# List all audio devices
python -c "from src.audio import AudioDeviceManager; m = AudioDeviceManager(); [print(d) for d in m.list_all_devices()]"
```

### PyAudio errors
```bash
# On macOS
brew install portaudio
pip install pyaudio
```

### Whisper model not found
```bash
# Manually download
python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
```

## Configuration

Edit `src/audio/audio_config.py` to adjust:

- **Silence threshold**: How long to wait before transcription
- **Whisper model**: tiny/base/small/medium (base recommended)
- **VAD sensitivity**: How aggressive speech detection is

## Next Steps

Now that audio is working, integrate with:

1. **Emotion detection model** - analyze user's tone
2. **Gemini API** - generate responses
3. **ElevenLabs** - speak responses
4. **Camera tracking** - follow user with cameras
5. **Amplitude** - store conversation history

## Support

- Check logs: `logs/shadow_*.log`
- Run tests: `pytest tests/ -v`
- See full docs: `AUDIO_SETUP.md`
