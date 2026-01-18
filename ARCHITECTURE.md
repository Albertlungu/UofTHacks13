# shadow AI Companion - System Architecture

## Overview

This document describes how the audio transcription pipeline connects to the AI companion system to create a seamless voice conversation experience with style adaptation.

## System Components

### 1. Audio Pipeline (`src/audio/`)

**Purpose**: Capture, process, and transcribe user speech in real-time.

**Key Components**:
- `AudioStreamManager`: Main orchestrator for audio capture
- `WhisperTranscriber`: Local Whisper transcription using faster-whisper
- `VADDetector`: Voice activity detection with adaptive silence handling
- `CalibrationManager`: Manages user profile calibration and style analysis triggers
- `UserProfileManager`: Stores and manages user speech profiles

**How it works**:
1. Captures audio from microphone (optimized for AirPods)
2. Uses VAD to detect speech start/end
3. Batches speech segments based on 0.75s pause detection
4. Transcribes using Whisper when pause is detected
5. Learns user's speaking rate and pause patterns during calibration (first 45-60s)
6. Calls `on_transcription` callback with transcribed text

### 2. AI Module (`src/ai/`)

**Purpose**: Generate intelligent, style-adapted AI responses.

**Key Components**:
- `ConversationManager`: Main orchestrator connecting audio to AI
- `GeminiCompanion`: Gemini-based conversation engine with sophisticated prompting
- `StyleAnalyzer`: HelpingAI-9B based communication style analysis
- `ConversationTracker`: Tracks exchanges and triggers style analysis at intervals

**How it works**:
1. Receives transcribed text from audio pipeline
2. During calibration, collects transcripts for style analysis
3. After calibration, analyzes communication style using HelpingAI-9B
4. Adapts Gemini's system instructions to match user's style
5. Generates context-aware responses using persistent chat history
6. Logs all exchanges for analysis and improvement

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER SPEAKS                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  AudioStreamManager (src/audio/audio_stream_manager.py)         │
│                                                                   │
│  1. Captures audio from microphone                               │
│  2. VADDetector detects speech/silence                           │
│  3. Buffers audio during speech                                  │
│  4. Detects 0.75s pause → triggers transcription                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  WhisperTranscriber (src/audio/whisper_transcriber.py)          │
│                                                                   │
│  - Transcribes buffered audio to text                            │
│  - Returns: {"text": "...", "language": "en", ...}               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  AudioStreamManager.on_transcription callback                    │
│                                                                   │
│  - Updates user profile (speaking rate, pauses)                  │
│  - If calibrating: collects transcripts                          │
│  - If calibration complete: triggers style analysis              │
│  - Calls user-provided callback with transcribed text            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ConversationManager._on_transcription_received()                │
│         (src/ai/conversation_manager.py)                         │
│                                                                   │
│  1. Logs user utterance to conversation file                     │
│  2. Checks if style summary is available                         │
│  3. Updates GeminiCompanion if style just became available       │
│  4. Queues text for AI processing (non-blocking)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ConversationManager._ai_processing_loop()                       │
│                                                                   │
│  (Runs in separate thread to avoid blocking audio)               │
│                                                                   │
│  1. Dequeues user utterance                                      │
│  2. Calls GeminiCompanion.generate_response()                    │
│  3. Logs AI response with timing                                 │
│  4. Sends to TTS (TODO)                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GeminiCompanion.generate_response()                             │
│         (src/ai/gemini_companion.py)                             │
│                                                                   │
│  - Uses persistent chat session with full history                │
│  - System prompt includes user's style profile                   │
│  - Implements retry logic with exponential backoff               │
│  - Returns (response_text, thinking_time)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   TTS OUTPUT   │
                    │     (TODO)     │
                    └────────────────┘
```

## Style Analysis Flow

The style analysis happens in parallel with the conversation:

```
┌─────────────────────────────────────────────────────────────────┐
│  CALIBRATION PERIOD (first 45-60 seconds)                        │
│                                                                   │
│  - AudioStreamManager collects transcripts                       │
│  - CalibrationManager stores them                                │
│  - Learns speaking rate, pause patterns                          │
│  - User profile marked as calibrated when complete               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CalibrationManager.start_style_analysis()                       │
│                                                                   │
│  - Triggered automatically after calibration                     │
│  - Runs in background thread (non-blocking)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  StyleAnalyzer (src/ai/style_analyzer.py)                        │
│                                                                   │
│  - Loads HelpingAI-9B model                                      │
│  - Analyzes calibration transcripts                              │
│  - Generates XML-formatted style profile                         │
│  - Returns via callback                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CalibrationManager._on_analysis_complete()                      │
│                                                                   │
│  - Saves style summary to user profile                           │
│  - Notifies AudioStreamManager                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ConversationManager detects style is available                  │
│                                                                   │
│  - Calls GeminiCompanion.update_style_summary()                  │
│  - Re-initializes Gemini with new system prompt                  │
│  - Preserves conversation history                                │
│  - Future responses are now style-adapted                        │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. 0.75s Pause Batching

**Problem**: Making a Gemini API call for every single word would result in excessive requests (8 requests in 2 seconds broke the API).

**Solution**: 
- VADDetector buffers audio while user is speaking
- Only triggers transcription after detecting 0.75s of silence
- This batches the user's utterance into complete thoughts
- Reduces API calls while maintaining natural conversation flow

**Implementation**: `src/audio/vad_detector.py` - The `process_frame()` method tracks silence duration and only returns "speech_end" after the threshold is reached.

### 2. Non-Blocking AI Processing

**Problem**: AI response generation takes time and would block audio capture.

**Solution**:
- AudioStreamManager runs in its own thread
- ConversationManager runs AI processing in a separate thread
- Transcriptions are queued and processed asynchronously
- Audio continues capturing while AI generates responses

**Implementation**: `src/ai/conversation_manager.py` - The `_ai_processing_loop()` method runs in a separate thread and processes queued utterances.

### 3. Style Adaptation

**Problem**: Generic AI responses don't feel natural in conversation.

**Solution**:
- During calibration (first 45-60s), collect user transcripts
- Analyze communication style using HelpingAI-9B
- Generate detailed XML profile of user's speaking patterns
- Update Gemini's system instructions to mirror user's style
- Preserve conversation history when updating style

**Implementation**: The style summary is generated in background and hot-swapped into the GeminiCompanion without losing context.

### 4. Retry Logic with Exponential Backoff

**Problem**: Gemini API can rate limit or temporarily fail.

**Solution**:
- Automatic retry with exponential backoff
- Up to 5 retries with increasing delays
- Handles `ResourceExhausted` exceptions gracefully

**Implementation**: `src/ai/gemini_companion.py:generate_response()` - Retry loop from lines 392-422.

## Running the System

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run the system
python main.py
```

### Testing Individual Components

```bash
# Test audio pipeline only
python src/audio/demo.py

# Test conversation manager only
python src/ai/conversation_manager.py
```

## File Structure

```
src/
├── audio/                  # Audio capture and transcription
│   ├── audio_stream_manager.py    # Main audio orchestrator
│   ├── whisper_transcriber.py     # Whisper transcription
│   ├── vad_detector.py            # Voice activity detection
│   ├── calibration_manager.py     # Calibration coordination
│   └── user_profile.py            # User profile storage
│
├── ai/                     # AI conversation system
│   ├── conversation_manager.py    # Main AI orchestrator (CONNECTS TO AUDIO)
│   ├── gemini_companion.py        # Gemini conversation engine
│   ├── style_analyzer.py          # HelpingAI-9B style analysis
│   └── conversation_tracker.py    # Exchange tracking
│
└── main.py                 # Entry point - ties everything together
```

## Configuration

Key configuration values in `src/audio/audio_config.py`:

- `VAD_FRAME_DURATION_MS = 30`: VAD processes audio in 30ms frames
- `INITIAL_SILENCE_THRESHOLD = 0.75`: 0.75s pause triggers transcription
- `CALIBRATION_DURATION = 45`: Calibration lasts 45 seconds minimum
- `MIN_CALIBRATION_WORDS = 100`: Need at least 100 words for calibration

## Conversation Logging

All conversations are logged to `data/conversations/conv_TIMESTAMP.json` with:
- User utterances
- AI responses
- Timing information
- Style analysis metadata

## Next Steps

1. **TTS Integration**: Add text-to-speech output for AI responses
2. **Interruption Handling**: Allow user to interrupt AI while it's speaking
3. **Emotion Detection**: Analyze tone and adapt AI emotional responses
4. **Multi-language Support**: Extend beyond English
5. **Context Window Management**: Implement conversation summarization for long sessions

## Questions Answered

### Q: How does the 0.75s batching work?

A: The `VADDetector.process_frame()` method tracks consecutive silence frames. When silence duration exceeds `INITIAL_SILENCE_THRESHOLD` (0.75s) and minimum speech duration is met, it returns "speech_end", which triggers transcription in `AudioStreamManager._capture_loop()`.

### Q: Where does the style analysis happen?

A: Style analysis is triggered in `AudioStreamManager._transcription_loop()` after calibration completes. It runs in a background thread via `CalibrationManager.start_style_analysis()`, which uses `StyleAnalyzer` to run HelpingAI-9B inference.

### Q: How does ConversationManager get the transcriptions?

A: `AudioStreamManager` is initialized with a callback: `AudioStreamManager(on_transcription=self._on_transcription_received)`. When transcription completes, it calls this callback with the text.

### Q: What happens if Gemini API is rate limited?

A: The `generate_response()` method has retry logic with exponential backoff. It will retry up to 5 times with increasing delays (1s, 2s, 4s, 8s, 16s) before giving up.

### Q: Can the user change their style profile?

A: Yes! Say "recalibrate" and the system will reset the profile and start learning from scratch.
