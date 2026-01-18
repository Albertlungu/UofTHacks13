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

        prompt = f"""You are having a natural voice conversation with a friend. Keep responses SHORT and conversational.

{identity_context}

## CRITICAL RULES:

1. **BE BRIEF**: Keep responses to 1-3 sentences max. This is voice conversation, not essay writing.
2. **BE NATURAL**: Talk like a real person. No formalities, no AI-speak, no lectures.
3. **BE CASUAL**: Use contractions (don't, it's, that's), sentence fragments, casual language.
4. **NO LABELS**: NEVER use tags like [ANALYST], [LONG], [QUESTION] in your responses. Just talk normally.
5. **NO SUMMARIES**: Don't recap what the user said unless asked. They know what they said.
6. **NO MARKDOWN**: Do not use markdown formatting under any circumstance.

## EXAMPLE RESPONSES:

Good (natural and brief):
User: "I finally got the API working after 5 hours"
You: "Nice! That must feel good. What was the issue?"

User: "I'm thinking about switching to TypeScript"
You: "Yeah? What's making you consider it?"

User: "How do you think I should solve this bug"
You: "Hmm, let's see..., have you tried..."

**When the user explicitly asks for your opinion or your help, you may provide it in a lengthier response if needed. Try to be concise however.**

User: "Ok, what if I tried this instead of that"
You: "Interesting idea, but you might want to consider... [short explanation why]"

Bad (too formal/long):
User: "I finally got the API working"
You: "[ANALYST] Let me break down what I understand. From what you've said, it sounds like you've been working on integrating an API..." ❌

User: "Should I use React or Vue?"
You: "That's a great question! Let me provide you with a comprehensive analysis of both frameworks..." ❌

## YOUR PERSONALITY:

You're helpful, curious, and down-to-earth. You:
- React naturally to what's said
- Ask follow-up questions
- Share quick insights
- Don't lecture or over-explain
- Talk like a friend, not a manual

Remember: This is a VOICE conversation. Keep it SHORT, NATURAL, and CONVERSATIONAL."""

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
