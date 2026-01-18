"""
Audio configuration constants for the shadow system.
"""

# Audio capture settings
SAMPLE_RATE = 16000  # Whisper's optimal sample rate
CHANNELS = 1  # Mono
CHUNK_SIZE = 1024  # Frames per buffer
FORMAT = "int16"  # 16-bit audio

# VAD settings
VAD_MODE = 2  # WebRTC VAD aggressiveness (0-3, where 3 is most aggressive)
VAD_FRAME_DURATION_MS = 30  # Must be 10, 20, or 30ms

# Silence detection settings
INITIAL_SILENCE_THRESHOLD = 1.5  # Seconds of silence before transcription (gives leeway for pauses mid-sentence)
THINKING_PAUSE_THRESHOLD = 2.0  # Seconds before considering it a "thinking pause"
MAX_SILENCE_BEFORE_INTERRUPT = 4.0  # Seconds before companion can interrupt
MIN_SPEECH_DURATION = (
    1.0  # Minimum seconds of speech to process (increased to reduce false positives)
)

# Audio buffering
MAX_RECORDING_DURATION = 120  # Maximum seconds per recording chunk (2 minutes)
BUFFER_PADDING_MS = 300  # Padding before/after speech for context

# Whisper settings
WHISPER_MODEL = "small"  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = "en"
WHISPER_TASK = "transcribe"

# Command detection
THINKING_COMMANDS = ["wait", "hold on", "give me a second", "let me think", "thinking"]
CONTINUE_COMMANDS = ["okay", "continue", "go ahead", "keep going"]
RECALIBRATE_COMMANDS = ["recalibrate", "reset calibration", "start over"]
NEED_MORE_TIME_COMMANDS = ["need more time", "slower today", "give me more time"]

# Calibration settings
CALIBRATION_DURATION = 60.0  # Seconds to calibrate (45-60s)
CALIBRATION_SILENCE_BUFFER = 2.0  # Extra seconds during calibration
MIN_CALIBRATION_WORDS = 70  # Minimum words needed for calibration
CALIBRATION_LEARNING_RATE = 1.0  # Full learning during calibration
POST_CALIBRATION_LEARNING_RATE = 0.1  # Slower learning after calibration

# Speaking rate settings
MIN_WORDS_PER_MINUTE = 80  # Very slow speech
NORMAL_WORDS_PER_MINUTE = 150  # Average speech rate
MAX_WORDS_PER_MINUTE = 200  # Fast speech

# User profile settings
USER_PROFILE_DIR = "./data/profiles"
DEFAULT_USER_ID = "default_user"
