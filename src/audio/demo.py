"""
Demo script for testing the audio pipeline with AirPods and Whisper.
"""

import signal
import sys
import threading
import time

from colorama import Fore, Style, init
from loguru import logger

from src.audio.audio_config import CALIBRATION_DURATION
from src.audio.audio_stream_manager import AudioStreamManager
from src.audio.error_handler import setup_logging

# Initialize colorama
init(autoreset=True)


class AudioDemo:
    """Demo application for testing the audio pipeline."""

    def __init__(self):
        self.stream_manager: AudioStreamManager = None
        self.is_running = False
        self.calibration_countdown_shown = False
        self.calibration_complete_shown = False
        self.style_analysis_triggered = False

    def on_transcription_received(self, text: str):
        """
        Callback when transcription is received.

        Args:
            text: Transcribed text from user
        """
        logger.info(f'USER SAID: "{text}"')
        print(f"\n{Fore.CYAN}>>> USER:{Style.RESET_ALL} {text}")

        # Show word count during calibration
        if self.stream_manager.vad.is_calibrating:
            words_spoken = self.stream_manager.user_profile.total_words_spoken
            print(
                f"{Fore.YELLOW}[CALIBRATION]{Style.RESET_ALL} Words spoken: {words_spoken}/100"
            )

        print()  # Empty line for spacing

        # Check if calibration just completed
        if (
            not self.stream_manager.vad.is_calibrating
            and not self.calibration_complete_shown
        ):
            self.calibration_complete_shown = True
            print("\n" + Fore.GREEN + "=" * 60 + Style.RESET_ALL)
            print(Fore.GREEN + "CALIBRATION COMPLETE!" + Style.RESET_ALL)
            print("You can keep speaking - system is now learning your style!")
            print(Fore.GREEN + "=" * 60 + Style.RESET_ALL + "\n")

        # Check if we should show style analysis trigger message
        if (
            not self.style_analysis_triggered
            and self.stream_manager.user_profile.is_calibrated
            and not self.stream_manager.calibration_manager.style_analysis_in_progress
        ):
            # Check if we have calibration transcripts to analyze
            if self.stream_manager.calibration_manager.calibration_transcripts:
                print("\n" + Fore.YELLOW + "=" * 60 + Style.RESET_ALL)
                print(
                    Fore.YELLOW
                    + "[STYLE ANALYSIS] Starting HelpingAI analysis..."
                    + Style.RESET_ALL
                )
                print("This will happen in the background while you continue speaking.")
                print(Fore.YELLOW + "=" * 60 + Style.RESET_ALL + "\n")
                self.style_analysis_triggered = True

    def monitor_calibration(self):
        """Monitor calibration progress and show countdown."""
        if not self.stream_manager.vad.is_calibrating:
            return

        calibration_start = self.stream_manager.vad.calibration_start_time

        while self.is_running and self.stream_manager.vad.is_calibrating:
            elapsed = time.time() - calibration_start
            remaining = CALIBRATION_DURATION - elapsed

            # Show countdown in last 5 seconds
            if (
                remaining <= 5
                and remaining > 0
                and not self.calibration_countdown_shown
            ):
                self.calibration_countdown_shown = True
                print("\n" + Fore.YELLOW + "=" * 60 + Style.RESET_ALL)
                print(
                    Fore.YELLOW + "[NOTICE] CALIBRATION ENDING SOON!" + Style.RESET_ALL
                )
                print(Fore.YELLOW + "=" * 60 + Style.RESET_ALL)

                for i in range(5, 0, -1):
                    current_elapsed = time.time() - calibration_start
                    if current_elapsed >= CALIBRATION_DURATION:
                        break
                    print(
                        f"{Fore.YELLOW}[COUNTDOWN]{Style.RESET_ALL} {i} seconds remaining..."
                    )
                    time.sleep(1)

                break

            time.sleep(0.1)

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
        logger.info("shadow Audio Pipeline Demo with Style Analysis")
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
            print(Fore.GREEN + "READY TO LISTEN (Calibrated Profile)" + Style.RESET_ALL)
            print("=" * 60)
            print(f"\n{Fore.CYAN}Your speech profile:{Style.RESET_ALL}")
            print(
                f"  - Speaking rate: {self.stream_manager.user_profile.words_per_minute:.1f} WPM"
            )
            print(
                f"  - Silence threshold: {self.stream_manager.user_profile.silence_threshold:.2f}s"
            )
            print(
                f"  - Thinking pause: {self.stream_manager.user_profile.thinking_pause_threshold:.2f}s"
            )

            if self.stream_manager.user_profile.style_summary:
                print(
                    f"\n  {Fore.GREEN}[OK]{Style.RESET_ALL} Style profile available for Gemini"
                )
            else:
                print(
                    f"\n  {Fore.YELLOW}[PENDING]{Style.RESET_ALL} Style profile will be generated from your speech"
                )
        else:
            print(Fore.YELLOW + "READY TO LISTEN (Calibration Mode)" + Style.RESET_ALL)
            print("=" * 60)
            print(
                f"\n{Fore.CYAN}[CALIBRATION]{Style.RESET_ALL} First 45-60 seconds: Learning your speech patterns..."
            )
            print("Please speak naturally - the system is adapting to you!")
            print(
                f"\n{Fore.YELLOW}[NOTICE]{Style.RESET_ALL} A countdown will appear 5 seconds before calibration ends."
            )
            print(
                "After calibration, HelpingAI will analyze your style in the background."
            )

        print("\n" + "=" * 60)
        print("INSTRUCTIONS")
        print("=" * 60)
        print("\nSpeak naturally into your AirPods.")
        print("The system will detect when you start and stop speaking.")
        print(f"\n{Fore.CYAN}Special commands:{Style.RESET_ALL}")
        print("  - Say 'wait' or 'hold on' to enter thinking mode")
        print("  - Say 'okay' or 'continue' to resume")
        print("  - Say 'need more time' to temporarily increase pause tolerance")
        print("  - Say 'recalibrate' to reset and relearn your patterns")
        print(f"\n{Fore.RED}Press Ctrl+C to exit.{Style.RESET_ALL}\n")

        # Start listening
        try:
            self.stream_manager.start()
            self.is_running = True

            # Start calibration monitor thread if in calibration mode
            if self.stream_manager.vad.is_calibrating:
                monitor_thread = threading.Thread(
                    target=self.monitor_calibration, daemon=True
                )
                monitor_thread.start()

            # Keep the main thread alive
            while self.is_running:
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
            # Show final style summary if available
            style_summary = self.stream_manager.get_style_summary_for_gemini()
            if style_summary:
                print("\n" + Fore.GREEN + "=" * 60 + Style.RESET_ALL)
                print(Fore.GREEN + "STYLE ANALYSIS COMPLETE" + Style.RESET_ALL)
                print(Fore.GREEN + "=" * 60 + Style.RESET_ALL)
                print("\nYour communication style profile is ready!")
                print("This will be used by Gemini to adapt its responses.")
                print(
                    f"\nSummary length: {Fore.CYAN}{len(style_summary)}{Style.RESET_ALL} characters"
                )
                print(
                    f"\n{Fore.CYAN}Profile saved to:{Style.RESET_ALL}",
                    self.stream_manager.profile_manager.get_profile_path(
                        self.stream_manager.user_profile.user_id
                    ),
                )
                print(Fore.GREEN + "=" * 60 + Style.RESET_ALL + "\n")
            elif self.stream_manager.calibration_manager.style_analysis_in_progress:
                print(
                    f"\n{Fore.YELLOW}[NOTICE]{Style.RESET_ALL} Style analysis still in progress..."
                )
                print("Profile will be available in your next session.\n")

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
