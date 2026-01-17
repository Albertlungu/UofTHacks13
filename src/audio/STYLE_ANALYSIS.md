# Style Analysis System

This document explains how the Goonvengers system uses HelpingAI-9B to analyze user communication patterns and adapt Gemini's responses.

## Overview

The style analysis system works in two phases:

1. **Initial Analysis (Calibration)**: During the first 45-60 seconds, the system collects everything the user says and uses HelpingAI-9B to create a detailed communication style profile.

2. **Ongoing Refinement**: After calibration, the system continues to refine the profile every 4-8 exchanges based on recent conversations.

## Architecture

```
User Speech (calibration period)
    ↓
Whisper Transcription
    ↓
Calibration Manager (collects transcripts)
    ↓
HelpingAI-9B (background analysis)
    ↓
Style Summary (XML format)
    ↓
User Profile (saved to JSON)
    ↓
Gemini System Instructions (adapted responses)
```

## How It Works

### Phase 1: Calibration (0-60 seconds)

**What happens:**
1. User speaks naturally during calibration
2. All transcripts are collected in `CalibrationManager`
3. When calibration completes (100+ words spoken):
   - Audio patterns (pauses, WPM) are finalized
   - HelpingAI model loads in background
   - Style analysis begins asynchronously

**User experience:**
- System continues responding immediately
- Style analysis happens in background (takes 10-30 seconds)
- Once complete, Gemini receives the style profile

### Phase 2: Background Analysis

**HelpingAI analyzes:**
- **Vocabulary level**: casual, formal, technical, mixed
- **Sentence complexity**: simple, moderate, complex
- **Tone**: analytical, enthusiastic, contemplative, pragmatic
- **Speech patterns**: pace, pauses, directness
- **Personality traits**: evident from speech style
- **Topics of interest**: what user discussed
- **Example phrases**: actual phrases user said

**Output format:**
```xml
<user_communication_profile>
  <communication_style>
    <vocabulary_level>casual with technical terms</vocabulary_level>
    <sentence_complexity>moderate to complex</sentence_complexity>
    <tone>analytical and pragmatic</tone>
  </communication_style>
  
  <speech_patterns>
    <speaking_pace>145 words per minute</speaking_pace>
    <thinking_style>takes thoughtful pauses between ideas</thinking_style>
  </speech_patterns>
  
  <personality_traits>
    Direct communicator, values efficiency, solution-oriented
  </personality_traits>
  
  <topics_of_interest>
    Machine learning, system design, practical applications
  </topics_of_interest>
  
  <example_phrases>
    - "I've been thinking about..."
    - "Something that actually helps people"
    - "Not just another demo"
  </example_phrases>
</user_communication_profile>
```

### Phase 3: Gemini Integration

The style summary is formatted with instructions:

```xml
<user_communication_profile>
[Style analysis XML]
</user_communication_profile>

Instructions: Adapt your communication style to match the user's patterns described above. 
Mirror their vocabulary level, tone, and pacing. Use similar sentence structures and expressions.
```

This is passed to Gemini's `system_instructions` field.

## Ongoing Refinement

After calibration, the system continues learning:

### Exchange-Based Analysis Schedule

- **Exchanges 1-8**: Analyze every 4 exchanges
  - Exchange 4: First refinement
  - Exchange 8: Second refinement
  
- **After Exchange 8**: Progressive intervals
  - Exchange 16: Third refinement
  - Exchange 24: Fourth refinement
  - Exchange 32: Fifth refinement
  - Every 8 exchanges after that

### What Gets Analyzed

For refinements, HelpingAI receives:
- Recent 4 exchanges (user + AI responses)
- Previous style summary for context
- Prompted to identify changes/updates

### Conversation Tracking

All exchanges are stored in:
```
./data/conversations/{user_id}_session_{timestamp}.json
```

Format:
```json
{
  "user_id": "default_user",
  "exchange_count": 15,
  "last_analysis_at": 8,
  "exchanges": [
    {
      "timestamp": "2026-01-17T20:30:45",
      "user_text": "What the user said",
      "ai_response": "What Gemini responded",
      "exchange_number": 1
    }
  ]
}
```

## Implementation Details

### Key Components

1. **`style_analyzer.py`**: HelpingAI-9B wrapper
   - Loads model on M1/M2/M3 Macs (MPS device)
   - Processes analysis in background thread
   - Creates engineered prompts for analysis

2. **`conversation_tracker.py`**: Exchange management
   - Tracks user-AI conversations
   - Determines when to trigger analysis
   - Manages progressive refinement schedule

3. **`calibration_manager.py`**: Coordination layer
   - Collects calibration transcripts
   - Triggers style analysis
   - Formats results for Gemini

4. **`user_profile.py`** (updated): Storage
   - `style_summary`: XML summary from HelpingAI
   - `style_last_updated`: Timestamp of last update

### Model Loading

**HelpingAI-9B** (OEvortex/HelpingAI2-9B):
- 9 billion parameters
- Loaded with `torch.float16` on MPS (Metal)
- Optimized for M1/M2/M3 Macs
- First load takes ~30-60 seconds
- Cached in `~/.cache/huggingface/`

**Memory usage:**
- Model: ~5-6 GB VRAM
- Inference: ~1-2 GB additional
- Total: ~7-8 GB (fits on 16GB unified memory Macs)

### Performance

**Calibration phase:**
- Transcript collection: realtime (no overhead)
- Model loading: 30-60s (first time only)
- Analysis generation: 10-30s

**Per-refinement:**
- Analysis: 5-15s (model already loaded)
- Happens in background, doesn't block conversation

## Configuration

### Calibration Settings (`audio_config.py`)

```python
CALIBRATION_DURATION = 60.0  # Initial analysis window
MIN_CALIBRATION_WORDS = 100  # Minimum words needed
```

### Analysis Settings (`style_analyzer.py`)

```python
max_new_tokens=1024  # Length of analysis
temperature=0.6      # Creativity level
top_p=0.9           # Sampling diversity
```

### Refinement Schedule (`conversation_tracker.py`)

```python
analysis_intervals = [4, 8, 16, 24, 32]  # Exchange numbers
# After 32: every 8 exchanges
```

## Usage Example

```python
from src.audio import AudioStreamManager

def on_transcription(text: str):
    print(f"User: {text}")
    
    # Get style summary for Gemini
    style_instructions = stream.get_style_summary_for_gemini()
    
    if style_instructions:
        # Send to Gemini with style context
        response = gemini.generate(
            text,
            system_instruction=style_instructions
        )
        print(f"AI: {response}")

# Create stream manager
stream = AudioStreamManager(
    on_transcription=on_transcription,
    user_id="albert"
)

stream.setup()
stream.start()

# Style analysis happens automatically:
# 1. During calibration: collects transcripts
# 2. After calibration: runs HelpingAI in background
# 3. Result available via get_style_summary_for_gemini()
```

## File Structure

```
src/
├── ai/
│   ├── __init__.py
│   ├── style_analyzer.py         # HelpingAI wrapper
│   └── conversation_tracker.py   # Exchange tracking
├── audio/
│   ├── calibration_manager.py    # Coordination
│   ├── audio_stream_manager.py   # Integration
│   └── user_profile.py           # Storage (updated)

data/
├── profiles/
│   └── {user_id}.json           # User profiles with style
└── conversations/
    └── {user_id}_session_{time}.json  # Conversation logs
```

## Requirements

```txt
torch>=2.0.0
transformers>=4.35.0
accelerate>=0.25.0
```

Install with:
```bash
pip install torch transformers accelerate
```

## Gemini Integration Best Practices

Based on [Google's Gemini prompting guidelines](https://ai.google.dev/gemini-api/docs/prompting-strategies):

1. **Use system instructions**: Separate field, not in conversation
2. **XML structure**: Clear delimiters for different aspects
3. **Few-shot examples**: Include actual user phrases
4. **Explicit instructions**: Tell Gemini what to do, not what not to do
5. **Clear persona**: Define role and characteristics explicitly

### Example Gemini Call

```python
import google.generativeai as genai

# Get style summary
style_context = stream.get_style_summary_for_gemini()

# Configure model
model = genai.GenerativeModel(
    model_name="gemini-pro",
    system_instruction=style_context  # Style adaptation here
)

# Generate response
response = model.generate_content("User's message")
```

## Troubleshooting

### Model won't load

**Error**: "MPS backend not available"
```bash
# Check PyTorch MPS support
python -c "import torch; print(torch.backends.mps.is_available())"
```

**Solution**: Install PyTorch with MPS support:
```bash
pip install torch torchvision torchaudio
```

### Out of memory

**Error**: Model loading fails with OOM

**Solutions**:
1. Close other applications
2. Use smaller model: Change to "base" or "small" Whisper
3. Reduce `max_new_tokens` to 512

### Slow analysis

**Issue**: Style analysis takes too long

**Solutions**:
1. Use `torch.float16` (already default on MPS)
2. Reduce `max_new_tokens`
3. Increase `temperature` slightly (0.7-0.8) for faster sampling

### Style summary not appearing

**Check**:
```python
# Check if analysis completed
print(stream.user_profile.style_summary)
print(stream.user_profile.style_last_updated)

# Check calibration transcripts
print(stream.calibration_manager.calibration_transcripts)
```

## Future Enhancements

1. **Voice characteristics**: Analyze tone, pitch, energy from audio
2. **Emotion tracking**: Detect emotional state during conversation
3. **Multi-modal analysis**: Include facial expressions from camera
4. **Fine-tuning**: Use collected data to fine-tune Gemini
5. **Style evolution**: Track how user's style changes over time

## Sources

- [Gemini API Prompting Strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [System Instructions Best Practices](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/system-instructions)
- [HelpingAI-9B Model Card](https://huggingface.co/OEvortex/HelpingAI2-9B)

## License

[To be determined]
