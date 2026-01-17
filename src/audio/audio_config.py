"""
Audio configuration constants for the Goonvengers system.
"""

# Audio capture settings
SAMPLE_RATE = 16000  # Whisper's optimal sample rate
CHANNELS = 1  # Mono
CHUNK_SIZE = 1024  # Frames per buffer
FORMAT = 'int16'  # 16-bit audio

# VAD settings
VAD_MODE = 2  # WebRTC VAD aggressiveness (0-3, where 3 is most aggressive)
VAD_FRAME_DURATION_MS = 30  # Must be 10, 20, or 30ms

# Silence detection settings
INITIAL_SILENCE_THRESHOLD = 1.5  # Seconds of silence before transcription
THINKING_PAUSE_THRESHOLD = 3.0  # Seconds before considering it a "thinking pause"
MAX_SILENCE_BEFORE_INTERRUPT = 5.0  # Seconds before companion can interrupt
MIN_SPEECH_DURATION = 0.5  # Minimum seconds of speech to process

# Audio buffering
MAX_RECORDING_DURATION = 30  # Maximum seconds per recording chunk
BUFFER_PADDING_MS = 300  # Padding before/after speech for context

# Whisper settings
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = "en"
WHISPER_TASK = "transcribe"

# Command detection
THINKING_COMMANDS = ["wait", "hold on", "give me a second", "let me think", "thinking"]
CONTINUE_COMMANDS = ["okay", "continue", "go ahead", "keep going"]
