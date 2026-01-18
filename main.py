#!/usr/bin/env python3
"""
Main entry point for shadow AI Companion.

This script starts the complete conversation system including:
- Audio capture and transcription (Whisper)
- Voice activity detection with 0.75s pause batching
- User style analysis (HelpingAI-9B)
- AI companion responses (Gemini) adapted to user's style
"""

import argparse
import signal
import sys
import time

from colorama import Fore, Style, init
from loguru import logger

from src.ai.conversation_manager import ConversationManager
from src.audio.error_handler import setup_logging

# Initialize colorama for colored terminal output
init(autoreset=True)


def print_banner():
    """Print the welcome banner."""
    print("\n" + Fore.CYAN + "=" * 70 + Style.RESET_ALL)
    print(Fore.CYAN + "  shadow AI COMPANION" + Style.RESET_ALL)
    print(
        Fore.CYAN
        + "  Real-time Voice Conversation with Style Adaptation"
        + Style.RESET_ALL
    )
    print(Fore.CYAN + "=" * 70 + Style.RESET_ALL)


def print_instructions():
    """Print usage instructions."""
    print("\n" + Fore.YELLOW + "HOW IT WORKS:" + Style.RESET_ALL)
    print("  1. Speak naturally into your microphone")
    print("  2. The system detects when you pause (0.75s) and processes your speech")
    print("  3. During the first minute, it learns your communication style")
    print("  4. AI responses are adapted to match your speaking patterns")

    print("\n" + Fore.YELLOW + "SPECIAL COMMANDS:" + Style.RESET_ALL)
    print("  - Say 'wait' or 'hold on' to make the AI wait for you to think")
    print("  - Say 'okay' or 'continue' to resume normal conversation")
    print("  - Say 'need more time' to increase pause tolerance temporarily")
    print("  - Say 'recalibrate' to reset and relearn your speech patterns")

    print("\n" + Fore.RED + "Press Ctrl+C to exit" + Style.RESET_ALL)
    print(Fore.CYAN + "=" * 70 + Style.RESET_ALL + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="shadow AI Companion - Voice conversation with style adaptation"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="default_user",
        help="User identifier for profile management (default: default_user)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    # Print banner and instructions
    print_banner()
    print(f"\n{Fore.GREEN}Initializing system...{Style.RESET_ALL}")

    # Create conversation manager
    manager = None

    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received")
        print(f"\n\n{Fore.YELLOW}Shutting down gracefully...{Style.RESET_ALL}")
        if manager:
            manager.cleanup()
        print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}\n")
        sys.exit(0)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize the conversation manager
        manager = ConversationManager(user_id=args.user_id)

        print(f"{Fore.GREEN}System initialized successfully!{Style.RESET_ALL}")
        print_instructions()

        # Check calibration status
        # NOTE: Calibration system is currently disabled
        # if manager.audio_manager.user_profile.is_calibrated:
        #     print(
        #         f"{Fore.GREEN}[PROFILE LOADED]{Style.RESET_ALL} Using your saved speech profile"
        #     )
        #     print(
        #         f"  - Speaking rate: {manager.audio_manager.user_profile.words_per_minute:.1f} WPM"
        #     )
        #     print(
        #         f"  - Pause threshold: {manager.audio_manager.user_profile.silence_threshold:.2f}s"
        #     )
        #
        #     if manager.audio_manager.user_profile.style_summary:
        #         print(f"  - Style profile: {Fore.GREEN}Available{Style.RESET_ALL}")
        #     else:
        #         print(
        #             f"  - Style profile: {Fore.YELLOW}Will be generated{Style.RESET_ALL}"
        #         )
        # else:
        #     print(
        #         f"{Fore.YELLOW}[CALIBRATION MODE]{Style.RESET_ALL} First 45-60 seconds"
        #     )
        #     print(
        #         "  The system will learn your speech patterns and communication style"
        #     )
        #    print("  Please speak naturally - the AI is adapting to you!")

        print(f"\n{Fore.GREEN}Starting conversation system...{Style.RESET_ALL}\n")

        # Start the system
        manager.start()

        # Keep main thread alive
        while manager.is_running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        if manager:
            manager.cleanup()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}\n")
        if manager:
            manager.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
