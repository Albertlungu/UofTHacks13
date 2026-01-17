from dotenv import load_dotenv
from pathlib import Path
import os
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

# To run (from your project root): python src/voice/example.py

env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(dotenv_path=env_path)

#print("ELEVENLABS_API_KEY =", os.getenv("ELEVENLABS_API_KEY"))

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

audio = client.text_to_speech.convert(
    text="If this speaks, your identity layer has a voice.",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model_id="eleven_turbo_v2_5"
)

play(audio)
