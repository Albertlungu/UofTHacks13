# Backboard.io Technical Challenge Compliance

## Project: GOONVENGERS AI Companion

This document demonstrates how our project meets all requirements for the Backboard.io "Memory Lane: Adaptive AI Journeys" technical challenge.

---

## Challenge Requirements

### 1. Adaptive Memory ✅

**Requirement**: Effectively utilize past interactions to personalize the current experience.

**Our Implementation**:
- **Identity Manager** (`src/identity/identity_manager.py`): Progressively learns about the user across conversations
- **User Profile Storage** (`data/profiles/`): Persistent storage of user identity, preferences, and communication style
- **Conversation History**: All exchanges tracked in `data/conversations/` with timestamps
- **Context-Aware Responses**: AI companion uses historical context to personalize responses

**Key Features**:
- User identity profile updated every 10 exchanges
- Conversation style adaptation based on past interactions
- Persistent memory across sessions via file storage and Backboard.io API

**Files**:
- `src/identity/identity_manager.py`
- `src/ai/conversation_tracker.py`
- `data/profiles/default_user_identity.json`

---

### 2. Model Switching ✅

**Requirement**: Demonstrate intelligent switching between different LLMs to handle diverse aspects of the user's journey. Must use minimum of 2 different models from specified providers.

**Our Implementation**:

#### Models Used (3 providers):
1. **Google Gemini 2.0 Flash** (`google/gemini-2.0-flash-exp`)
   - Use case: Conversational responses, casual chat
   - Reason: Fast, natural dialogue, low latency

2. **Anthropic Claude 3.5 Sonnet** (`anthropic/claude-3-5-sonnet-20241022`)
   - Use case: Analytical tasks, technical questions, problem-solving
   - Reason: Superior reasoning and analytical capabilities

3. **OpenAI GPT-4o** (`openai/gpt-4o`)
   - Use case: Creative content generation, storytelling
   - Reason: Best-in-class creative writing

#### Intelligent Routing Logic:

**Task Classification** (`src/ai/backboard_client.py:classify_task_type()`):
```
User Input → Keyword Analysis → Task Type → Model Selection

Examples:
- "Hey, how are you?" → CONVERSATIONAL → Gemini
- "Explain how neural networks work" → ANALYTICAL → Claude
- "Write me a story about a robot" → CREATIVE → ChatGPT
- "How do I debug this Python error?" → TECHNICAL → Claude
```

**Model Switching is Logged**:
```
[MODEL SWITCH] google/gemini-2.0-flash-exp -> anthropic/claude-3-5-sonnet-20241022
[TASK TYPE] conversational -> analytical
[MODEL INFO] Provider: anthropic, Model: claude-3-5-sonnet-20241022, Task: analytical
```

**Files**:
- `src/ai/backboard_client.py` - Multi-model client with routing
- `src/ai/backboard_companion.py` - Companion using Backboard.io
- `src/ai/conversation_manager.py` - Integration point

---

### 3. Framework ✅

**Requirement**: Must utilize Backboard.io, LangGraph, AutoGen, or CrewAI.

**Our Implementation**: Uses **Backboard.io** directly via OpenAI-compatible API.

**Integration Details**:
- Backboard.io client initialized in `src/ai/backboard_client.py`
- OpenAI SDK configured to use Backboard.io endpoint: `https://api.backboard.io/v1`
- API key loaded from `.env` file: `BACKBOARD_API_KEY`
- User ID passed for memory/personalization: `user=self.user_id`

**Code Example**:
```python
self.client = OpenAI(
    api_key=api_key,
    base_url="https://api.backboard.io/v1"
)

response = self.client.chat.completions.create(
    model=model,  # Routes to Gemini/Claude/GPT
    messages=messages,
    user=self.user_id  # Backboard.io memory
)
```

---

### 4. User Experience ✅

**Requirement**: Overall intuitiveness and engagement of the application.

**Our Implementation**:

#### Multimodal Interaction:
- **Voice Conversation**: Real-time speech with Whisper transcription
- **Camera Tracking**: Face detection and tracking (Center Stage)
- **3D Hand Gestures**: Hand tracking for 3D block building
- **Text-to-Speech**: Natural voice responses via ElevenLabs

#### Natural Conversation Flow:
- 0.75s pause detection for natural speech batching
- Smart interruption detection (AI can interrupt unproductive rambling)
- Conversational tone (no "AI-speak" or formal language)
- Context-aware responses based on conversation history

#### Personalization:
- AI adapts to user's communication style
- Learns preferences and interests over time
- Maintains consistent personality across sessions

**User Journey**:
1. User speaks into microphone
2. System transcribes speech (Whisper)
3. AI classifies task type and routes to best model
4. Response generated with user's identity context
5. Voice response played back (ElevenLabs TTS)
6. Model switching logged for transparency

---

### 5. Technical Implementation ✅

**Requirement**: Clean code, efficient use of Backboard.io features, innovative problem-solving.

**Our Implementation**:

#### Clean Architecture:
```
src/
├── ai/
│   ├── backboard_client.py        # Multi-model routing
│   ├── backboard_companion.py      # Backboard-powered companion
│   ├── conversation_manager.py     # Orchestration layer
│   ├── conversation_tracker.py     # History tracking
│   └── gemini_companion.py         # Fallback to Gemini
├── audio/
│   ├── audio_stream_manager.py     # Voice input
│   └── tts_elevenlabs.py           # Voice output
├── identity/
│   └── identity_manager.py         # User profile learning
├── camera/
│   └── center_stage.py             # Face tracking
└── hand_tracking/
    └── server.py                   # 3D gesture control
```

#### Efficient Backboard.io Usage:
- Single API key for all models (no managing multiple providers)
- Automatic conversation history via `user` parameter
- Rate limiting to respect API constraints
- Intelligent caching and batching

#### Innovative Features:
1. **Progressive Identity Learning**: AI learns user's identity incrementally (every 10 exchanges)
2. **Context-Aware Model Routing**: Automatically switches models based on conversation content
3. **Multimodal Integration**: Voice + Camera + Hand tracking in unified experience
4. **Smart Batching**: Reduces API calls while maintaining conversational feel

---

## How to Run

### 1. Setup
```bash
# Install dependencies
./run_all.sh

# Or manually:
pip install -r requirements.txt
cd src/frontend/src && npm install
```

### 2. Configure API Keys
Create `.env` file:
```
BACKBOARD_API_KEY=your_backboard_key_here
GEMINI_API_KEY=your_gemini_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### 3. Launch Services
```bash
# Automated launch (opens all services in iTerm tabs)
./run_all.sh

# Or manually:
# Terminal 1: Camera system
python src/camera/center_stage.py

# Terminal 2: Voice conversation (MAIN - shows model switching)
python main.py

# Terminal 3: Hand tracker
python run_hand_tracker.py 1

# Terminal 4: Frontend
cd src/frontend/src && npm start
```

### 4. Test Model Switching

Open `python main.py` and speak different types of queries:

**Conversational** (uses Gemini):
- "Hey, how are you doing?"
- "What do you think about AI?"

**Analytical** (switches to Claude):
- "Can you explain how transformers work?"
- "Why is my code not working?"

**Creative** (switches to GPT-4o):
- "Write me a short story about a robot"
- "Tell me a creative metaphor for machine learning"

**Technical** (switches to Claude):
- "How do I implement a binary search tree?"
- "Debug this Python error for me"

**Watch the Console**: You'll see logs like:
```
[MODEL SWITCH] google/gemini-2.0-flash-exp -> anthropic/claude-3-5-sonnet-20241022
[TASK TYPE] conversational -> analytical
[MODEL INFO] Provider: anthropic, Model: claude-3-5-sonnet-20241022, Task: analytical
```

---

## Demo Script

### Recommended Demo Flow:

1. **Start with Casual Chat** (Gemini)
   - "Hey, what's up?"
   - "How's it going?"

2. **Ask Analytical Question** (Switch to Claude)
   - "Can you explain how neural networks actually learn?"
   - Watch console for model switch log

3. **Request Creative Content** (Switch to GPT-4o)
   - "Write me a haiku about artificial intelligence"
   - Watch console for model switch log

4. **Technical Query** (Claude)
   - "How would I implement a REST API in Python?"
   - Watch console for model staying on Claude

5. **Return to Casual** (Back to Gemini)
   - "Thanks, that was really helpful!"
   - Watch console for model switch back

---

## Key Differentiators

### What Makes Our Project Stand Out:

1. **Multimodal Experience**: Not just text chat - voice, vision, and gesture control
2. **Real-World Application**: Actual hardware integration (camera tracking, Arduino motors)
3. **Progressive Learning**: AI gets smarter about you over time
4. **Transparent Model Switching**: Clear logging shows which model handles each query
5. **Natural Voice Interaction**: Feels like talking to a human, not a chatbot

### Technical Highlights:

- **3 AI Providers**: Google, Anthropic, OpenAI
- **Smart Task Classification**: Keyword-based routing (fast, no extra API call)
- **Memory Across Sessions**: Identity profile persists and evolves
- **Production-Ready**: Error handling, rate limiting, logging, fallbacks

---

## Files Modified for Challenge

### Core Backboard.io Integration:
- `src/ai/backboard_client.py` - NEW: Multi-model client
- `src/ai/backboard_companion.py` - NEW: Backboard-powered AI companion
- `src/ai/conversation_manager.py` - MODIFIED: Uses Backboard.io
- `requirements.txt` - MODIFIED: Added openai and anthropic SDKs

### Documentation:
- `BACKBOARD_CHALLENGE.md` - NEW: This file

---

## Challenge Criteria Met

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Adaptive Memory | ✅ | Identity manager, conversation history, user profiles |
| Model Switching (2+ providers) | ✅ | Gemini, Claude, GPT-4o with intelligent routing |
| Framework (Backboard.io) | ✅ | Direct API integration via OpenAI SDK |
| User Experience | ✅ | Voice + camera + hand tracking, natural dialogue |
| Technical Implementation | ✅ | Clean architecture, efficient API usage, innovation |

---

## Contact

- **Project**: GOONVENGERS AI Companion
- **Hackathon**: UofTHacks 2026
- **Promo Code**: UOFTHACKS26

---

## License

MIT License
