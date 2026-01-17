"""
Example demonstrating how to add custom vocabulary/slang to Whisper for better recognition.

This is useful when your users use specific terminology, slang, or jargon that Whisper
might not recognize correctly.
"""

from src.ai.conversation_manager import ConversationManager


def main():
    # METHOD 1: Pass vocabulary at initialization (recommended)
    slang_vocab = "Common slang: yeet, lit, fr, ngl, bruh, fam, lowkey, highkey, slay"
    manager = ConversationManager(user_id="example_user", custom_vocabulary=slang_vocab)

    # METHOD 2: Update vocabulary at runtime (can be called anytime after initialization)
    # manager = ConversationManager(user_id="example_user")
    # manager.update_whisper_vocabulary(slang_vocab)

    # Example: Add technical terms
    # tech_vocab = "Technical terms: Kubernetes, PostgreSQL, FastAPI, Redis, webhook"
    # manager.update_whisper_vocabulary(tech_vocab)

    # Example: Add names and places
    # names_vocab = "Names and places: Sakura, Helsinki, Guangzhou, Vladivostok"
    # manager.update_whisper_vocabulary(names_vocab)

    # Example: Combine multiple contexts
    # combined = "Common slang: yeet, lit, fr. Tech terms: Kubernetes, Redis. Names: Sakura, Helsinki"
    # manager.update_whisper_vocabulary(combined)

    # Start the conversation
    print("Starting conversation with custom vocabulary...")
    print(f"Vocabulary: {slang_vocab}")
    manager.start()

    try:
        # Keep running
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        manager.cleanup()


if __name__ == "__main__":
    main()
