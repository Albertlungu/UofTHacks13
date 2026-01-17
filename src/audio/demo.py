"""
Demo script for testing the audio pipeline with AirPods and Whisper.
"""

import signal
import sys

from loguru import logger

from src.audio.audio_stream_manager import AudioStreamManager
from src.audio.error_handler import setup_logging


class AudioDemo:
    """Demo application for testing the audio pipeline."""

    def __init__(self):
        self.stream_manager: AudioStreamManager = None
        self.is_running = False

    def on_transcription_received(self, text: str):
        """
        Callback when transcription is received.

        Args:
            text: Transcribed text from user
        """
        logger.info(f'USER SAID: "{text}"')
        print(f"\n>>> USER: {text}\n")

        # Here you would:
        # 1. Send text to emotion detection model
        # 2. Store in Amplitude
        # 3. Send to Gemini for response
        # 4. Use ElevenLabs to speak response
        # For now, just echo it

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self):
        """Run the demo application."""
        logger.info("=" * 60)
        logger.info("Goonvengers Audio Pipeline Demo")
        logger.info("=" * 60)

        # Set up signal handlers
        self.setup_signal_handlers()

        # Create stream manager
        self.stream_manager = AudioStreamManager(
            on_transcription=self.on_transcription_received
        )

        # Setup audio devices
        logger.info("Setting up audio devices...")
        if not self.stream_manager.setup():
            logger.error("Failed to set up audio devices")
            return

        logger.info("Audio setup complete!")
        print("\n" + "=" * 60)

        # Show calibration status
        if self.stream_manager.user_profile.is_calibrated:
            print("READY TO LISTEN (Calibrated Profile)")
            print("=" * 60)
            print(f"\nYour speech profile:")
            print(
                f"  - Speaking rate: {self.stream_manager.user_profile.words_per_minute:.1f} WPM"
            )
            print(
                f"  - Silence threshold: {self.stream_manager.user_profile.silence_threshold:.2f}s"
            )
            print(
                f"  - Thinking pause: {self.stream_manager.user_profile.thinking_pause_threshold:.2f}s"
            )
        else:
            print("READY TO LISTEN (Calibration Mode)")
            print("=" * 60)
            print("\nFirst 45-60 seconds: Learning your speech patterns...")
            print("Please speak naturally - the system is adapting to you!")

        print("\nSpeak naturally into your AirPods.")
        print("The system will detect when you start and stop speaking.")
        print("\nSpecial commands:")
        print("  - Say 'wait' or 'hold on' to enter thinking mode")
        print("  - Say 'okay' or 'continue' to resume")
        print("  - Say 'need more time' to temporarily increase pause tolerance")
        print("  - Say 'recalibrate' to reset and relearn your patterns")
        print("\nPress Ctrl+C to exit.\n")

        # Start listening
        try:
            self.stream_manager.start()
            self.is_running = True

            # Keep the main thread alive
            while self.is_running:
                import time

                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown the demo application."""
        if not self.is_running:
            return

        logger.info("Shutting down...")
        self.is_running = False

        if self.stream_manager:
            self.stream_manager.cleanup()

        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    # Set up logging
    setup_logging()

    # Create and run demo
    demo = AudioDemo()
    demo.run()


if __name__ == "__main__":
    main()
