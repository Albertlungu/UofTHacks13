"""
ElevenLabs Text-to-Speech integration for AI companion responses.
"""

import io
import os
import queue
import threading
from typing import Optional

import pyaudio
from elevenlabs import generate, play, set_api_key, voices
from loguru import logger


class ElevenLabsTTS:
    """
    Handles text-to-speech using ElevenLabs API with streaming audio output.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_name: str = "JBFqnCBsd6RMkjVDRZzb",
        output_device_index: Optional[int] = None,
    ):
        """
        Initialize ElevenLabs TTS.

        Args:
            api_key: ElevenLabs API key (or from env ELEVENLABS_API_KEY)
            voice_name: Voice name to use (default: George)
            output_device_index: Audio output device (e.g., AirPods)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")

        # Set API key globally
        set_api_key(self.api_key)

        self.voice_name = voice_name
        self.output_device_index = output_device_index

        # Audio playback
        self.audio = pyaudio.PyAudio()
        self.is_playing = False
        self.playback_queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Interruption control
        self.interrupt_flag = threading.Event()
        self.current_stream: Optional[pyaudio.Stream] = None
        self.stream_lock = threading.Lock()

        # Callback to notify when speaking starts/stops
        self.on_speaking_changed: Optional[callable] = None

        logger.info(f"ElevenLabsTTS initialized with George {voice_name}")

    def start(self):
        """Start the TTS playback thread."""
        if self.is_running:
            return

        self.is_running = True
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        logger.info("TTS playback thread started")

    def stop(self):
        """Stop the TTS playback thread."""
        self.is_running = False
        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)
        logger.info("TTS playback thread stopped")

    def speak(self, text: str, block: bool = False):
        """
        Convert text to speech and play it.

        Args:
            text: Text to speak
            block: If True, wait for speech to finish before returning
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return

        logger.info(f'TTS: Speaking "{text[:50]}..."')

        # Queue for playback
        self.playback_queue.put(text)

        if block:
            # Wait for queue to empty
            self.playback_queue.join()

    def interrupt(self):
        """
        Interrupt current speech playback immediately.
        Call this when user starts speaking to stop the AI.
        """
        logger.info("TTS interrupted by user speech")

        # Set interrupt flag
        self.interrupt_flag.set()

        # Stop current stream if playing
        with self.stream_lock:
            if self.current_stream:
                try:
                    self.current_stream.stop_stream()
                    self.current_stream.close()
                    self.current_stream = None
                except Exception as e:
                    logger.error(f"Error stopping stream: {e}")

        # Clear playback queue (discard pending speech)
        while not self.playback_queue.empty():
            try:
                self.playback_queue.get_nowait()
                self.playback_queue.task_done()
            except queue.Empty:
                break

        logger.info("TTS playback interrupted and queue cleared")

    def _playback_loop(self):
        """Background thread that plays TTS audio."""
        logger.info("TTS playback loop started")

        while self.is_running:
            try:
                # Get next text to speak
                text = self.playback_queue.get(timeout=1.0)

                # Clear interrupt flag at the start of new speech
                self.interrupt_flag.clear()
                logger.debug("Interrupt flag cleared for new speech")

                # Generate audio from ElevenLabs
                logger.debug("Generating speech with ElevenLabs...")

                try:
                    # Check if interrupted before generating
                    if self.interrupt_flag.is_set():
                        logger.info("Skipping speech generation (interrupted)")
                        self.playback_queue.task_done()
                        continue

                    # Generate speech
                    audio_data = generate(
                        text=text,
                        voice=self.voice_name,
                        model="eleven_turbo_v2",  # Fast model
                    )

                    logger.info(f"Generated audio for TTS ({len(text)} chars)")

                    # Check again before playing
                    if self.interrupt_flag.is_set():
                        logger.info("Skipping audio playback (interrupted)")
                        self.playback_queue.task_done()
                        continue

                    # Play audio (can be interrupted mid-playback)
                    self._play_audio(audio_data)

                except Exception as e:
                    logger.error(f"ElevenLabs TTS generation failed: {e}")

                self.playback_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in TTS playback loop: {e}")

        logger.info("TTS playback loop ended")

    def _play_audio(self, audio_data: bytes):
        """
        Play audio through PyAudio with interruption support.

        Args:
            audio_data: MP3 or PCM audio data
        """
        try:
            # Notify that AI is starting to speak
            if self.on_speaking_changed:
                self.on_speaking_changed(True)

            # ElevenLabs returns MP3, need to decode it
            from pydub import AudioSegment

            # Load audio
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Convert to raw PCM
            raw_data = audio.raw_data
            sample_width = audio.sample_width
            channels = audio.channels
            sample_rate = audio.frame_rate

            # Play through PyAudio
            with self.stream_lock:
                self.current_stream = self.audio.open(
                    format=self.audio.get_format_from_width(sample_width),
                    channels=channels,
                    rate=sample_rate,
                    output=True,
                    output_device_index=self.output_device_index,
                )

            # Write audio data in chunks, checking for interruption
            chunk_size = 1024
            for i in range(0, len(raw_data), chunk_size):
                # Check if interrupted
                if self.interrupt_flag.is_set():
                    logger.info("Audio playback interrupted mid-stream")
                    break

                chunk = raw_data[i : i + chunk_size]
                with self.stream_lock:
                    if self.current_stream:
                        self.current_stream.write(chunk)

            # Clean up stream
            with self.stream_lock:
                if self.current_stream:
                    self.current_stream.stop_stream()
                    self.current_stream.close()
                    self.current_stream = None

            if not self.interrupt_flag.is_set():
                logger.info("Audio playback complete")

        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
        finally:
            # Notify that AI has stopped speaking
            if self.on_speaking_changed:
                self.on_speaking_changed(False)

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.audio:
            self.audio.terminate()
        logger.info("ElevenLabsTTS cleaned up")


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    tts = ElevenLabsTTS()
    tts.start()

    # Test
    tts.speak(
        "Hello! This is a test of the ElevenLabs text to speech system.", block=True
    )

    tts.cleanup()
