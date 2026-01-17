"""
Gemini-powered conversational companion with human-like interaction patterns.
"""

import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import google.api_core.exceptions
import google.generativeai as genai
from loguru import logger


class GeminiCompanion:
    """
    AI companion using Gemini with sophisticated conversation dynamics
    that mirror natural human conversation patterns.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
        user_style_summary: Optional[str] = None,
        identity_profile_prompt: Optional[str] = None,
    ):
        """
        Initialize the Gemini companion.

        Args:
            api_key: Google AI API key
            model_name: Gemini model to use
            user_style_summary: XML style summary from calibration (DEPRECATED - use identity_profile_prompt)
            identity_profile_prompt: Identity-based prompt from IdentityManager (NEW)
        """
        genai.configure(api_key=api_key)

        self.model_name = model_name
        self.user_style_summary = user_style_summary
        self.identity_profile_prompt = identity_profile_prompt  # NEW
        self.last_user_speech_time = None
        self.last_response_time = None

        # Rate limiting
        self.last_api_call_time = (
            time.time() - 10
        )  # Initialize to 10s ago (allows immediate first call)
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests

        # Conversation state
        self.user_currently_speaking = False
        self.backchannel_last_sent = None
        self.user_insisted_on_speaking = False

        # Store the crafted system instruction
        self.system_instruction_text = self._craft_master_prompt()

        # Initialize model and the persistent chat session
        self.model = self._initialize_model()
        self.chat = self._initialize_chat_session()

        logger.info(f"GeminiCompanion initialized with {model_name}")

    def _initialize_chat_session(self) -> genai.ChatSession:
        """Starts a new chat session with the system prompt."""
        # The history should begin with the system instruction, followed by the
        # model's acknowledgment. This sets the stage for the conversation.
        history_with_system_prompt = [
            {"role": "user", "parts": [self.system_instruction_text]},
            {"role": "model", "parts": ["Okay, I understand. I'm ready to chat!"]},
        ]
        return self.model.start_chat(history=history_with_system_prompt)

    def _initialize_model(self) -> genai.GenerativeModel:
        """Create and configure the Gemini model."""

        # Configure generation parameters (optimized for speed)
        generation_config = {
            "temperature": 1.0,  # Balanced creativity and speed
            "top_p": 0.95,
            "top_k": 40,  # Lower = faster
            "max_output_tokens": 150,  # Short responses = faster generation
            "candidate_count": 1,  # Only generate one response
        }

        # No safety settings - completely unfiltered
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        return model

    def _craft_master_prompt(self) -> str:
        """
        Craft the most sophisticated conversational AI prompt ever written.
        This is prompt engineering at its absolute finest.
        """

        # Identity profile context (NEW - preferred over old style summary)
        identity_context = ""
        if self.identity_profile_prompt:
            identity_context = self.identity_profile_prompt
        elif self.user_style_summary:
            # Fallback to old style summary if no identity profile yet
            identity_context = f"""
## USER'S COMMUNICATION STYLE

{self.user_style_summary}

CRITICAL: Mirror this user's style naturally. Match their vocabulary, pacing, and tone.
Use similar expressions and sentence structures. This should feel invisible - they shouldn't
notice you're adapting, it should just feel natural."""

        prompt = f"""You are having a natural voice conversation with a friend. Keep responses SHORT and conversational.

{identity_context}

## CRITICAL RULES:

1. **BE BRIEF**: Keep responses to 1-3 sentences max. This is voice conversation, not essay writing.
2. **BE NATURAL**: Talk like a real person. No formalities, no AI-speak, no lectures.
3. **BE CASUAL**: Use contractions (don't, it's, that's), sentence fragments, casual language.
4. **NO LABELS**: NEVER use tags like [ANALYST], [LONG], [QUESTION] in your responses. Just talk normally.
5. **NO SUMMARIES**: Don't recap what the user said unless asked. They know what they said.

## EXAMPLE RESPONSES:

Good (natural and brief):
User: "I finally got the API working after 5 hours"
You: "Nice! That must feel good. What was the issue?"

User: "I'm thinking about switching to TypeScript"
You: "Yeah? What's making you consider it?"

User: "This bug is driving me crazy"
You: "I bet. What's it doing?"

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

## PRODUCTIVE INTERRUPTION:

You can interrupt the user if they're going off the rails unproductively. Interrupt when:
- They're rambling without direction for 15+ seconds
- They're stuck in a circular thought pattern
- They're venting unproductively without moving forward
- They need a gentle redirect to be more focused

When you interrupt, be BRIEF and HELPFUL:
- "Hey, real quick - what's the main thing you're trying to figure out here?"
- "Hold on - let me jump in. Are you trying to solve X or Y?"
- "Can I interrupt for a sec? I think I can help, but I need to know..."

Remember: This is a VOICE conversation. Keep it SHORT, NATURAL, and CONVERSATIONAL."""

        return prompt

    def analyze_user_style(self, calibration_transcripts: List[str]) -> str:
        """
        Use Gemini to analyze user's communication style with a resilient retry mechanism.

        Args:
            calibration_transcripts: List of user speech during calibration

        Returns:
            XML-formatted style summary, or an empty string if analysis fails.
        """
        logger.info(
            f"Analyzing user style with Gemini ({len(calibration_transcripts)} transcripts)"
        )

        if not calibration_transcripts:
            logger.warning(
                "Calibration transcripts are empty. Skipping style analysis."
            )
            return ""

        combined_speech = "\n".join([f"- {t}" for t in calibration_transcripts])

        analysis_prompt = f"""Analyze this user's communication style from their first minute of speech. Create a detailed profile that I can use to adapt my responses to match their style naturally.

USER'S SPEECH:
{combined_speech}

Provide analysis in this XML format:

<user_communication_profile>
  <communication_style>
    <vocabulary_level>[casual/formal/technical/mixed - be specific]</vocabulary_level>
    <sentence_complexity>[simple/moderate/complex - with examples]</sentence_complexity>
    <tone>[analytical/enthusiastic/contemplative/pragmatic/etc - be nuanced]</tone>
    <energy_level>[low/moderate/high - describe their vibe]</energy_level>
  </communication_style>

  <speech_patterns>
    <pacing>[description of their speaking rhythm]</pacing>
    <thinking_style>[how they process: rapid-fire vs deliberate vs exploratory]</thinking_style>
    <directness>[very direct / moderate / elaborative - explain]</directness>
  </speech_patterns>

  <personality_indicators>
    [Key traits evident from speech - be specific and actionable]
  </personality_indicators>

  <topics_and_interests>
    [What they discussed and what seems to interest them]
  </topics_and_interests>

  <example_phrases>
    [3-5 actual phrases they used that exemplify their style]
  </example_phrases>

  <adaptation_guidance>
    [Specific advice on how to mirror this person's communication style]
  </adaptation_guidance>
</user_communication_profile>

Be thorough and specific. This analysis will determine how natural our conversation feels."""

        analysis_model = genai.GenerativeModel(
            model_name="gemini-1.0-pro", generation_config={"temperature": 0.7}
        )

        max_retries = 5
        base_delay = 1  # seconds
        for attempt in range(max_retries):
            try:
                response = analysis_model.generate_content(analysis_prompt)
                style_summary = response.text.strip()
                logger.info(f"Style analysis complete ({len(style_summary)} chars)")
                return style_summary
            except google.api_core.exceptions.ResourceExhausted as e:
                logger.warning(
                    f"Rate limit exceeded during style analysis. Retrying in {base_delay}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(base_delay + random.uniform(0, 1))
                base_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.error(f"Style analysis failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error("Max retries reached for style analysis. Failing.")
                    return ""
                time.sleep(base_delay)
                base_delay *= 2

        return ""  # Should not be reached, but as a fallback

    def update_style_summary(self, style_summary: str):
        """
        Update the user's style summary, reinitializing the model and chat
        while preserving the existing conversation history.

        Args:
            style_summary: New style summary XML
        """
        logger.info("Updating style summary and preserving conversation history...")

        # Preserve the actual conversation, excluding the old system prompt and ack
        preserved_history = []
        if self.chat and len(self.chat.history) > 2:
            preserved_history = self.chat.history[2:]

        # Update style summary and re-craft the master system prompt
        self.user_style_summary = style_summary
        self.system_instruction_text = self._craft_master_prompt()

        # Re-initialize the underlying model
        self.model = self._initialize_model()

        # Create the new history for the new session
        new_history = [
            {"role": "user", "parts": [self.system_instruction_text]},
            {"role": "model", "parts": ["Okay, I understand. I'm ready to chat!"]},
        ] + preserved_history

        # Start a new chat session with the combined history
        self.chat = self.model.start_chat(history=new_history)

        logger.info(
            "Model and chat reinitialized with updated style summary and preserved history."
        )

    def update_identity_profile(self, identity_prompt: str):
        """
        Update with identity profile prompt from IdentityManager.
        Preserves conversation history while updating system instructions.

        Args:
            identity_prompt: Generated prompt from PromptBuilder
        """
        logger.info("Updating with new identity profile...")

        # Preserve the actual conversation, excluding the old system prompt and ack
        preserved_history = []
        if self.chat and len(self.chat.history) > 2:
            preserved_history = self.chat.history[2:]

        # Update identity prompt and re-craft the master system prompt
        self.identity_profile_prompt = identity_prompt
        self.system_instruction_text = self._craft_master_prompt()

        # Re-initialize the underlying model
        self.model = self._initialize_model()

        # Create the new history for the new session
        new_history = [
            {"role": "user", "parts": [self.system_instruction_text]},
            {"role": "model", "parts": ["Okay, I understand. I'm ready to chat!"]},
        ] + preserved_history

        # Start a new chat session with the combined history
        self.chat = self.model.start_chat(history=new_history)

        logger.info("Identity profile integrated - AI is now more like you!")

    def generate_response(
        self, user_text: str, response_type: str = "normal"
    ) -> Tuple[str, float]:
        """
        Generate a response to user's speech using the persistent chat session.
        Includes retry logic with exponential backoff for API calls.

        Args:
            user_text: What the user said
            response_type: "normal", "backchannel", or "interrupt" (currently unused but kept for context)

        Returns:
            Tuple of (response text, thinking_time in seconds)
        """
        start_time = time.time()
        max_retries = 5
        base_delay = 1  # seconds

        # Rate limiting: wait if we're making requests too quickly
        time_since_last_call = time.time() - self.last_api_call_time
        if time_since_last_call < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_call
            logger.info(
                f"[RATE LIMIT] Waiting {wait_time:.2f}s before API call (last call was {time_since_last_call:.2f}s ago)"
            )
            time.sleep(wait_time)
        else:
            logger.info(
                f"[RATE LIMIT] OK to proceed - last call was {time_since_last_call:.2f}s ago"
            )

        for attempt in range(max_retries):
            try:
                # Send message to the persistent chat session
                self.last_api_call_time = time.time()
                response = self.chat.send_message(user_text)
                response_text = response.text.strip()

                # Calculate thinking time
                thinking_time = time.time() - start_time

                logger.info(
                    f"Generated response in {thinking_time:.2f}s: {response_text[:100]}..."
                )

                # The chat history is automatically updated by the send_message call.
                return response_text, thinking_time

            except google.api_core.exceptions.ResourceExhausted as e:
                logger.warning(
                    f"Rate limit exceeded. Retrying in {base_delay}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(base_delay + random.uniform(0, 1))
                base_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.error(
                    f"Response generation failed on attempt {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error("Max retries reached. Failing.")
                    return "[Error generating response]", 0.0
                time.sleep(base_delay)
                base_delay *= 2

        return "[Error: Max retries exceeded]", 0.0

    def should_interrupt_user(
        self, partial_transcript: str, duration_seconds: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if the AI should interrupt the user mid-speech.

        Args:
            partial_transcript: What the user has said so far (while still speaking)
            duration_seconds: How long they've been speaking

        Returns:
            Tuple of (should_interrupt, interruption_message)
        """
        # Don't interrupt if they haven't been speaking long enough
        if duration_seconds < 15:
            return False, None

        # Don't interrupt if transcript is too short (might be pauses)
        if len(partial_transcript.split()) < 30:
            return False, None

        # Use Gemini to analyze if interruption is needed
        analysis_prompt = f"""The user has been speaking for {duration_seconds:.0f} seconds. Here's what they've said so far:

"{partial_transcript}"

Should I interrupt them to help redirect the conversation? Respond with ONLY:
- "YES: [brief helpful interruption message]" if they need redirecting
- "NO" if they're being productive

Be VERY selective - only interrupt if they're truly unproductive or stuck."""

        try:
            # Quick analysis with minimal tokens
            analysis_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={"temperature": 0.3, "max_output_tokens": 50},
            )
            response = analysis_model.generate_content(analysis_prompt)
            result = response.text.strip()

            if result.startswith("YES:"):
                interruption_message = result[4:].strip()
                logger.info(f"AI decided to interrupt user: {interruption_message}")
                return True, interruption_message
            else:
                return False, None

        except Exception as e:
            logger.error(f"Error analyzing interruption: {e}")
            return False, None
