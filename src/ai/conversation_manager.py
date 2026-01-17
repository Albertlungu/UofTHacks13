"""
Orchestrates the entire conversation flow, managing real-time transcription,
AI response generation, and style adaptation.
"""

import json
import os
import queue
import threading
import time
from datetime import datetime
from queue import Queue
from typing import Dict, Optional

from dotenv import load_dotenv
from loguru import logger

from src.ai.gemini_companion import GeminiCompanion
from src.audio.audio_stream_manager import AudioStreamManager
from src.audio.tts_elevenlabs import ElevenLabsTTS


class ConversationManager:
    """
    Manages the conversational AI workflow by orchestrating transcription,
    voice activity detection (VAD), and AI response generation.

    This connects the audio pipeline (AudioStreamManager) to the AI companion
    (GeminiCompanion) and handles the complete conversation flow.
    """

    def __init__(self, user_id: str = "default_user"):
        """
        Initializes the ConversationManager, loading configurations and setting up
        the necessary components for the conversation.

        Args:
            user_id: User identifier for profile management
        """
        logger.info("Initializing ConversationManager...")

        # Load API keys and configurations from .env file
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.user_id = user_id

        # --- Logging Setup ---
        now = datetime.now()
        log_filename = f"conv_{now.strftime('%Y%m%d_%H%M%S')}.json"
        log_dir = os.path.join("data", "conversations")
        os.makedirs(log_dir, exist_ok=True)
        self.conversation_log_file = os.path.join(log_dir, log_filename)
        with open(self.conversation_log_file, "w") as f:
            json.dump([], f)  # Initialize with an empty list
        logger.info(f"Conversation log will be saved to {self.conversation_log_file}")

        # --- Component Initialization ---

        # Audio stream manager - handles transcription with 0.75s pause batching
        self.audio_manager = AudioStreamManager(
            on_transcription=self._on_transcription_received,
            user_id=user_id,
        )

        # Main AI companion for generating thoughtful, context-aware responses
        # Start without style summary - will be updated after calibration
        self.companion = GeminiCompanion(api_key=gemini_api_key)

        # TTS for speaking responses
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.tts = (
            ElevenLabsTTS(api_key=elevenlabs_api_key) if elevenlabs_api_key else None
        )
        if self.tts:
            logger.info("ElevenLabs TTS enabled")
        else:
            logger.warning("ELEVENLABS_API_KEY not found - TTS disabled")

        # --- Threading and State Management ---
        self.is_running = False

        # Queue for processing AI responses (to avoid blocking audio thread)
        self.ai_response_queue = Queue()
        self.ai_processing_thread: Optional[threading.Thread] = None
        self.batch_sender_thread: Optional[threading.Thread] = None

        # Track whether we've already updated the companion with style
        self.style_updated = False

        # Smart batching to avoid excessive API calls
        self.utterance_buffer = []
        self.last_utterance_time = 0
        self.batch_timeout_sentence_end = 0.0  # INSTANT response after sentence end!
        self.batch_timeout_mid_sentence = 1.2  # Wait longer if mid-sentence (thinking)
        self.min_words_for_immediate_response = 5  # Short utterances get batched
        self.buffer_lock = threading.Lock()

        # Predictive pregeneration - start responding while user is still talking!
        self.user_utterance_lengths = []  # Track typical word counts
        self.avg_user_utterance_words = 25  # Will learn from actual usage
        self.pregeneration_enabled = True  # Turn this on/off
        self.pregenerating = False
        self.pregenerated_response = None

        logger.info("ConversationManager initialized successfully")

    def _log_to_conversation_file(self, data: Dict):
        """
        Appends data to the conversation log JSON file.

        Args:
            data: The dictionary to append (e.g., {"user": "text"}, {"companion": "text"})
        """
        try:
            with open(self.conversation_log_file, "r+") as f:
                file_data = json.load(f)
                file_data.append(data)
                f.seek(0)  # Rewind to the beginning of the file
                json.dump(file_data, f, indent=4)
                f.truncate()  # Remove remaining part if new data is smaller
        except Exception as e:
            logger.error(f"Failed to write to conversation log: {e}")

    def _on_transcription_received(self, text: str):
        """
        Callback when transcription is received from AudioStreamManager.
        This is called when the user pauses for 0.75s (as per your batching logic).

        Implements smart batching to avoid excessive API calls:
        - Short utterances (< 5 words) are buffered
        - Longer utterances trigger immediate response
        - Buffer is sent after 3s of silence

        Args:
            text: Transcribed text from user
        """
        logger.info(f'User said: "{text}"')
        self._log_to_conversation_file(
            {"timestamp": datetime.now().isoformat(), "user": text}
        )

        # Check if we should update companion with style summary
        if not self.style_updated and self.audio_manager.user_profile.is_calibrated:
            style_summary = self.audio_manager.get_style_summary_for_gemini()
            if style_summary:
                logger.info("Updating companion with user's style profile")
                self.companion.update_style_summary(style_summary)
                self.style_updated = True

        # Smart batching: Buffer utterances and send after timeout
        word_count = len(text.split())

        with self.buffer_lock:
            # Add to buffer
            self.utterance_buffer.append(text)
            self.last_utterance_time = time.time()
            logger.info(
                f"[BUFFER] Added to buffer ({word_count} words). Buffer now has {len(self.utterance_buffer)} segment(s). Will send after 3s of silence."
            )

    def _batch_sender_loop(self):
        """
        Background thread that monitors the utterance buffer and sends batched
        utterances after the timeout period (3s of silence).
        """
        logger.info("Batch sender thread started")

        while self.is_running:
            try:
                time.sleep(0.5)  # Check every 500ms

                current_time = time.time()
                time_since_last_utterance = current_time - self.last_utterance_time

                # Check if we should send the buffer
                with self.buffer_lock:
                    if len(self.utterance_buffer) > 0:
                        # Determine appropriate timeout based on sentence ending
                        combined_text = " ".join(self.utterance_buffer)
                        last_char = (
                            combined_text.rstrip()[-1] if combined_text.strip() else ""
                        )

                        # Check if last utterance ends with sentence-ending punctuation
                        ends_with_sentence = last_char in ".!?"

                        # Use shorter timeout for sentence endings, longer for mid-sentence
                        timeout_to_use = (
                            self.batch_timeout_sentence_end
                            if ends_with_sentence
                            else self.batch_timeout_mid_sentence
                        )

                        if time_since_last_utterance >= timeout_to_use:
                            word_count = len(combined_text.split())

                            logger.info(
                                f"[BATCH SEND] Sending {len(self.utterance_buffer)} segment(s) ({word_count} words) after {time_since_last_utterance:.1f}s silence ({'sentence_end' if ends_with_sentence else 'mid_sentence'})"
                            )
                            logger.info(f"[BATCH SEND] Text: {combined_text[:150]}...")

                            # Queue for AI processing
                            self.ai_response_queue.put(combined_text)

                            # Clear buffer
                            self.utterance_buffer = []
                            self.last_utterance_time = 0
                        else:
                            # Still waiting
                            remaining = timeout_to_use - time_since_last_utterance
                            if remaining > 0:
                                context = (
                                    "sentence_end"
                                    if ends_with_sentence
                                    else "mid_sentence"
                                )
                                logger.debug(
                                    f"[BATCH WAIT] Buffer has {len(self.utterance_buffer)} segment(s), waiting {remaining:.1f}s more ({context}, timeout={timeout_to_use}s)..."
                                )

            except Exception as e:
                logger.error(f"Error in batch sender loop: {e}")

        logger.info("Batch sender thread stopped")

    def _ai_processing_loop(self):
        """
        Background thread that processes user utterances and generates AI responses.
        This runs separately from the audio thread to avoid blocking transcription.
        """
        logger.info("AI processing thread started")

        while self.is_running:
            try:
                # Wait for the next user utterance
                user_utterance = self.ai_response_queue.get(timeout=1)

                logger.info(
                    f"[API CALL] Processing utterance ({len(user_utterance.split())} words)"
                )
                logger.info(
                    f"[API CALL] Queue size: {self.ai_response_queue.qsize()} remaining"
                )

                # Generate AI response
                start_time = time.time()
                companion_response, thinking_time = self.companion.generate_response(
                    user_utterance
                )
                total_time = time.time() - start_time

                logger.info(
                    f"AI response generated in {total_time:.2f}s (thinking: {thinking_time:.2f}s)"
                )
                logger.info(f'AI Companion: "{companion_response}"')

                self._log_to_conversation_file(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "companion": companion_response,
                        "thinking_time": thinking_time,
                        "total_time": total_time,
                    }
                )

                # Send to TTS for audio output
                print(f"\n[AI COMPANION]: {companion_response}\n")

                if self.tts:
                    self.tts.speak(companion_response, block=False)
                else:
                    logger.warning("TTS not available - response only printed")

                self.ai_response_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in AI processing loop: {e}")

        logger.info("AI processing thread stopped")

    def start(self):
        """
        Starts the conversation manager, initializing audio and AI processing.
        """
        logger.info("Starting ConversationManager...")

        # Setup audio devices
        if not self.audio_manager.setup():
            logger.error("Failed to setup audio devices")
            raise RuntimeError("Audio setup failed")

        self.is_running = True

        # Start TTS
        if self.tts:
            self.tts.start()

        # Start batch sender thread (monitors buffer and sends after timeout)
        self.batch_sender_thread = threading.Thread(
            target=self._batch_sender_loop, daemon=True
        )
        self.batch_sender_thread.start()

        # Start AI processing thread
        self.ai_processing_thread = threading.Thread(
            target=self._ai_processing_loop, daemon=True
        )
        self.ai_processing_thread.start()

        # Start audio stream (which will start transcribing)
        self.audio_manager.start()

        logger.info("ConversationManager started - listening for speech")

    def stop(self):
        """
        Stops the conversation manager and all associated threads gracefully.
        """
        logger.info("Stopping ConversationManager...")
        self.is_running = False

        # Stop audio manager first (stops transcription)
        if self.audio_manager:
            self.audio_manager.stop()

        # Wait for batch sender thread to finish
        if self.batch_sender_thread and self.batch_sender_thread.is_alive():
            self.batch_sender_thread.join(timeout=2.0)

        # Wait for AI processing thread to finish
        if self.ai_processing_thread and self.ai_processing_thread.is_alive():
            self.ai_processing_thread.join(timeout=2.0)

        logger.info("ConversationManager stopped")

    def cleanup(self):
        """Clean up all resources."""
        self.stop()
        if self.audio_manager:
            self.audio_manager.cleanup()
        if self.tts:
            self.tts.cleanup()
        logger.info("ConversationManager cleanup complete")


if __name__ == "__main__":
    """
    Simple test/demo of the ConversationManager.
    Run this to test the complete pipeline.
    """
    import signal
    import sys

    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        if manager:
            manager.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("\n" + "=" * 60)
    print("GOONVENGERS CONVERSATION MANAGER - TEST MODE")
    print("=" * 60)
    print("\nStarting conversation system...")
    print("Speak into your microphone. The system will:")
    print("  1. Transcribe your speech (batched on 0.75s pauses)")
    print("  2. Learn your communication style during calibration")
    print("  3. Generate AI responses adapted to your style")
    print("\nPress Ctrl+C to exit\n")

    manager = ConversationManager(user_id="test_user")

    try:
        manager.start()

        # Keep main thread alive
        while manager.is_running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        manager.cleanup()
