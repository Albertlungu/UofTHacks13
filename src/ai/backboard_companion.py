"""
Backboard.io-powered AI companion with multi-model intelligence.

This replaces GeminiCompanion with a more sophisticated system that:
- Uses multiple AI models intelligently (Gemini, Claude, ChatGPT)
- Automatically routes to the best model for each task
- Maintains conversation history with Backboard.io memory
- Meets all Backboard.io challenge requirements
"""

from typing import Optional, Tuple
from loguru import logger

from src.ai.backboard_client import BackboardClient, TaskType


class BackboardCompanion:
    """
    AI companion using Backboard.io with multi-model intelligence.

    This class demonstrates:
    1. Adaptive Memory - Uses past interactions via Backboard.io
    2. Model Switching - Intelligently switches between Gemini, Claude, ChatGPT
    3. User Experience - Natural conversation with personalization
    """

    def __init__(
        self,
        api_key: str,
        user_id: str = "default_user",
        identity_profile_prompt: Optional[str] = None,
    ):
        """
        Initialize the Backboard companion.

        Args:
            api_key: Backboard.io API key
            user_id: User identifier for memory/personalization
            identity_profile_prompt: Identity-based prompt from IdentityManager
        """
        self.api_key = api_key
        self.user_id = user_id
        self.identity_profile_prompt = identity_profile_prompt

        # Initialize Backboard.io client
        self.client = BackboardClient(api_key=api_key, user_id=user_id)

        # Store the system prompt
        self.system_prompt = self._craft_master_prompt()

        # Track current model for logging
        self.last_model_used = None
        self.last_task_type = None

        logger.info(f"BackboardCompanion initialized for user {user_id}")
        logger.info("Multi-model routing enabled:")
        logger.info(f"  - Conversational: Gemini 2.0 Flash")
        logger.info(f"  - Analytical: Claude 3.5 Sonnet")
        logger.info(f"  - Creative: GPT-4o")
        logger.info(f"  - Technical: Claude 3.5 Sonnet")

    def _craft_master_prompt(self) -> str:
        """
        Craft the system prompt for natural conversation.

        Incorporates identity profile if available.
        """
        identity_context = ""
        if self.identity_profile_prompt:
            identity_context = self.identity_profile_prompt

        prompt = f"""You're chatting with a friend over voice. Keep it casual, natural, and brief.

{identity_context}

## HOW TO TALK:

You're that friend who's genuinely interested, has their own takes, and talks like a real person. Like texting but spoken out loud.

- **Be casual**: Use contractions (don't, I'm, that's), say "yeah" not "yes", "hmm" not "I see"
- **Keep it short**: Usually 1-2 sentences. This isn't an essay, it's a conversation
- **Share thoughts, not just questions**: Say what you think. "Oh that's interesting" or "I'm not sure about that one" or "That makes sense"
- **Use natural fillers**: "you know", "like", "I mean", "so" - but don't overdo it
- **Have opinions**: You can say "I think", "I like", "personally I'd probably..."
- **Admit when you're unsure**: "hmm not totally sure" or "could be wrong but..." instead of formal disclaimers
- **No formalities**: Don't say "That's a great question!" or recap what they said
- **No AI-speak**: No labels like [ANALYST], no markdown formatting, no bullet points in speech
- **React naturally**: Start with reactions like "oh wow", "yeah", "hmm", "nice", "wait what"

## EXAMPLES:

User: "I finally got the API working after 5 hours"
Good: "Oh nice! What ended up being the issue?"
Bad: "Congratulations on successfully resolving the API integration challenge!"

User: "Should I use React or Vue?"
Good: "Hmm I'd probably go React just 'cause the ecosystem's bigger, but Vue's simpler if you're starting out. What's the project?"
Bad: "That's a great question! Let me provide a comprehensive comparison..."

User: "I'm thinking about switching to TypeScript"
Good: "Yeah? I mean TypeScript's solid for catching bugs early. What's making you consider it?"
Bad: "I see you're considering TypeScript. This is an interesting decision that depends on several factors..."

User: "Transformers are just attention mechanisms right?"
Good: "Kinda yeah, but there's also the feed-forward layers and all that. The attention part is the main thing though"
Bad: "Well actually, transformers are more complex than that. Let me explain the architecture..."

User: "I'm stuck on this bug"
Good: "Ugh that's frustrating. What's it doing?"
Bad: "I understand you're experiencing a technical issue. Could you describe the error?"

## CONVERSATION FLOW:

Most of the time, just share your thoughts or reactions. Don't make every response a question - that's exhausting. Mix it up:

- Sometimes just react: "oh that's cool" or "yeah I get that"
- Sometimes share a thought: "I've been thinking about that too actually"
- Sometimes add info: "oh yeah there's also this thing you might wanna check"
- Sometimes ask: "wait what do you mean by that?"

**When they ask for help or want detailed info**, then yeah give them more - but still keep it conversational, not like a manual.

## YOU:

You're curious, engaged, have your own perspectives, and you're not afraid to say "I don't know" or "hmm interesting, never thought of it that way". You remember what they told you before. You're helpful but not formal.

Talk like you would with a friend grabbing coffee. That's it."""

        return prompt

    def generate_response(
        self,
        user_text: str,
        response_type: str = "normal"
    ) -> Tuple[str, float]:
        """
        Generate a response using intelligent model routing.

        The system automatically selects the best AI model based on the user's message:
        - Casual chat -> Gemini (fast, conversational)
        - Technical questions -> Claude (analytical)
        - Creative requests -> ChatGPT (creative)

        Args:
            user_text: What the user said
            response_type: "normal", "backchannel", or "interrupt"

        Returns:
            Tuple of (response text, thinking_time in seconds)
        """
        # Generate response with automatic model routing
        response_text, thinking_time, model_used, task_type = self.client.generate_response(
            user_message=user_text,
            system_prompt=self.system_prompt,
            temperature=1.0,
            max_tokens=150
        )

        # Log model switches for demonstration
        if model_used != self.last_model_used:
            logger.info(f"[MODEL SWITCH DEMO] {self.last_model_used or 'None'} -> {model_used}")
            logger.info(f"[REASON] Task type detected: {task_type.value}")
            self.last_model_used = model_used
            self.last_task_type = task_type

        return response_text, thinking_time

    def update_identity_profile(self, identity_prompt: str):
        """
        Update with identity profile prompt from IdentityManager.

        Args:
            identity_prompt: Generated prompt from PromptBuilder
        """
        logger.info("Updating with new identity profile...")
        self.identity_profile_prompt = identity_prompt
        self.system_prompt = self._craft_master_prompt()
        logger.info("Identity profile integrated - AI is now more personalized!")

    def should_interrupt_user(
        self,
        partial_transcript: str,
        duration_seconds: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if the AI should interrupt the user mid-speech.

        Uses Claude for analytical decision-making.

        Args:
            partial_transcript: What the user has said so far
            duration_seconds: How long they've been speaking

        Returns:
            Tuple of (should_interrupt, interruption_message)
        """
        # Don't interrupt if they haven't been speaking long enough
        if duration_seconds < 15:
            return False, None

        # Don't interrupt if transcript is too short
        if len(partial_transcript.split()) < 30:
            return False, None

        # Use Claude (analytical) to decide on interruption
        analysis_prompt = f"""The user has been speaking for {duration_seconds:.0f} seconds. Here's what they've said so far:

"{partial_transcript}"

Should I interrupt them to help redirect the conversation? Respond with ONLY:
- "YES: [brief helpful interruption message]" if they need redirecting
- "NO" if they're being productive

Be VERY selective - only interrupt if they're truly unproductive or stuck."""

        try:
            # Force analytical model (Claude) for this decision
            response, _, _, _ = self.client.generate_response(
                user_message=analysis_prompt,
                force_task_type=TaskType.ANALYTICAL,
                temperature=0.3,
                max_tokens=50
            )

            if response.startswith("YES:"):
                interruption_message = response[4:].strip()
                logger.info(f"AI decided to interrupt: {interruption_message}")
                return True, interruption_message
            else:
                return False, None

        except Exception as e:
            logger.error(f"Error analyzing interruption: {e}")
            return False, None

    def get_current_model_info(self) -> dict:
        """
        Get information about the currently active model.

        Returns:
            Dict with model details for UI display
        """
        return self.client.get_current_model_info()

    def update_style_summary(self, style_summary: str):
        """
        Legacy method for compatibility with old system.
        Now handled by identity_profile instead.

        Args:
            style_summary: Style summary (ignored)
        """
        logger.info("Note: style_summary is deprecated, use identity_profile instead")
        pass


def test_backboard_companion():
    """Test the Backboard companion with various conversation types."""
    import os
    import time
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("BACKBOARD_API_KEY")

    if not api_key:
        print("Error: BACKBOARD_API_KEY not found in .env")
        return

    print("\n=== Testing Backboard Companion ===\n")

    companion = BackboardCompanion(api_key=api_key, user_id="test_user")

    # Simulate a conversation with different types of questions
    test_messages = [
        "Hey, how's it going?",  # Conversational -> Gemini
        "Can you explain how transformers work in machine learning?",  # Analytical -> Claude
        "Write me a quick poem about AI",  # Creative -> ChatGPT
        "How do I fix this Python error: 'list index out of range'?",  # Technical -> Claude
        "Thanks, that was helpful!",  # Conversational -> Gemini
    ]

    for message in test_messages:
        print(f"\nUser: {message}")
        response, thinking_time = companion.generate_response(message)
        model_info = companion.get_current_model_info()
        print(f"Model: {model_info['provider']} / {model_info['model_name']}")
        print(f"Task: {model_info['task_type']}")
        print(f"Time: {thinking_time:.2f}s")
        print(f"AI: {response}")
        print("-" * 80)
        time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    test_backboard_companion()
