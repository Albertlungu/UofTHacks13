from dotenv import load_dotenv
from pathlib import Path
import os

import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

# RUN FROM PROJECT ROOT: python src/voice/speech_to_speech.py
# Dependancies: python -m pip install SpeechRecognition pyaudio python-dotenv elevenlabs

# -------------------------------
# ENV SETUP (same as your TTS)
# -------------------------------

env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(dotenv_path=env_path)

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# -------------------------------
# SPEECH TO TEXT
# -------------------------------

def listen_once():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Listening... (stop speaking to finish)")
        r.adjust_for_ambient_noise(source, duration=0.5)

        # Automatically stops when silence is detected
        audio = r.listen(
            source,
            timeout=None,
            phrase_time_limit=8  # max speaking time (seconds)
        )

    try:
        text = r.recognize_google(audio)
        print("🧠 You said:", text)
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return None
    except sr.RequestError as e:
        print("❌ STT service error:", e)
        return None

# -------------------------------
# TEMPORARY "AI BRAIN" (NO API)
# -------------------------------

def simple_identity_ai(user_text):
    user_text = user_text.lower()

    if "idea" in user_text:
        return (
            "I like the direction, but I would challenge the assumption behind it "
            "instead of accepting it outright."
        )

    if "good" in user_text or "bad" in user_text:
        return (
            "I don't think it's purely good or bad. "
            "I think it depends on context and intent."
        )

    if "hello" in user_text or "hi" in user_text:
        return "Hello. I'm here with you. What are you thinking about?"

    return (
        "That's interesting. If I were you, I would pause and reflect on why that idea matters."
    )

# -------------------------------
# TEXT TO SPEECH (YOUR CODE)
# -------------------------------

def speak(text):
    print("🤖 Speaking:", text)

    audio = client.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_turbo_v2_5"
    )

    play(audio)

# -------------------------------
# MAIN FLOW
# -------------------------------

def main():
    user_text = listen_once()

    if not user_text:
        print("No input detected. Exiting.")
        return
    
    response = simple_identity_ai(user_text)
    print("Response: ", response)
    speak(response)

if __name__ == "__main__":
    main()
