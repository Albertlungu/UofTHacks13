"""
AI Interjection Analyzer - Determines when and how AI should interrupt user.

Phase 1: Quick Reactions - Pattern matching for excited/emotional moments
"""

import random
import re
import time
from typing import Optional, Tuple
from loguru import logger


class InterjectionType:
    """Types of interjections the AI can make."""
    EXCITED = "excited"  # Quick excited reactions
    AGREEMENT = "agreement"  # Quick agreements
    SURPRISE = "surprise"  # Surprised reactions
    CLARIFYING = "clarifying"  # Asking for clarification
    NONE = None  # No interjection


class InterjectionAnalyzer:
    """
    Analyzes user speech in real-time to determine when AI should interject.

    Phase 1 Implementation: Pattern matching for quick reactions
    """

    def __init__(self):
        """Initialize the interjection analyzer."""
        # Excitement triggers - user saying something exciting
        self.excitement_patterns = [
            r"\bguess what\b",
            r"\byou (won't|wont) believe\b",
            r"\bi just got\b",
            r"\bfinally\b",
            r"\bamazing\b",
            r"\bincredible\b",
            r"\bi('m| am) so excited\b",
            r"\bcheck this out\b",
            r"\bthis is crazy\b",
            r"\bi won\b",
            r"\bi got accepted\b",
            r"\bi passed\b",
        ]

        # Surprise triggers - user revealing something
        self.surprise_patterns = [
            r"\byou know what\b",
            r"\bi found out\b",
            r"\bturns out\b",
            r"\bapparently\b",
            r"\bbelieve it or not\b",
        ]

        # Agreement triggers - user saying something AI agrees with
        self.agreement_patterns = [
            r"\b(python|ai|machine learning) is (the best|amazing|great)\b",
            r"\bi (love|really like)\b",
            r"\bi think .* is awesome\b",
        ]

        # Negative/concerning triggers
        self.concern_patterns = [
            r"\bterrible\b",
            r"\bawful\b",
            r"\bfrustrating\b",
            r"\bi can't figure out\b",
            r"\bnothing('s| is) working\b",
            r"\bi('m| am) stuck\b",
        ]

        # Quick reaction responses (pre-generated for speed)
        self.excitement_responses = [
            "Oh wow!",
            "Really?!",
            "No way!",
            "That's awesome!",
            "Amazing!",
            "Incredible!",
        ]

        self.surprise_responses = [
            "Oh really?",
            "Interesting!",
            "Tell me more!",
            "What happened?",
        ]

        self.agreement_responses = [
            "I know right!",
            "Exactly!",
            "Yes!",
            "Totally agree!",
            "For sure!",
        ]

        self.concern_responses = [
            "Oh no!",
            "That's frustrating!",
            "I can help with that!",
            "Let me help!",
        ]

        # Rate limiting
        self.last_interjection_time = 0
        self.min_interjection_interval = 8.0  # Min 8s between interjections
        self.interjections_in_last_minute = []
        self.max_interjections_per_minute = 4  # Allow slightly more interjections

        # Timing thresholds for each interjection type
        self.timing_thresholds = {
            InterjectionType.EXCITED: (0.5, 2.0),  # React quickly to excitement
            InterjectionType.SURPRISE: (1.0, 3.0),  # React to reveals
            InterjectionType.AGREEMENT: (1.5, 3.0),  # Validate their opinions
            InterjectionType.CLARIFYING: (2.0, 5.0),  # Wait a bit for context
        }

        logger.info("InterjectionAnalyzer initialized (Phase 1: Quick Reactions)")

    def _check_rate_limit(self) -> bool:
        """
        Check if we're allowed to interject based on rate limiting.

        Returns:
            True if interjection is allowed, False otherwise
        """
        current_time = time.time()

        # Clean up old interjections from tracking (older than 60s)
        self.interjections_in_last_minute = [
            t for t in self.interjections_in_last_minute
            if current_time - t < 60.0
        ]

        # Check if we've exceeded max interjections per minute
        if len(self.interjections_in_last_minute) >= self.max_interjections_per_minute:
            logger.debug("Rate limit: Max interjections per minute reached")
            return False

        # Check minimum interval between interjections
        if current_time - self.last_interjection_time < self.min_interjection_interval:
            logger.debug("Rate limit: Too soon since last interjection")
            return False

        return True

    def _matches_pattern(self, text: str, patterns: list) -> bool:
        """
        Check if text matches any of the given patterns.

        Args:
            text: Text to check
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    def analyze(
        self,
        partial_text: str,
        duration_seconds: float,
        conversation_context: Optional[list] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Analyze partial transcript to determine if AI should interject.

        Args:
            partial_text: What user has said so far
            duration_seconds: How long they've been speaking
            conversation_context: Recent conversation history (optional)

        Returns:
            Tuple of (interjection_type, response_text) or (None, None)
        """
        # Don't analyze very short text
        if len(partial_text.strip()) < 10:
            return None, None

        # Check rate limiting first
        if not self._check_rate_limit():
            return None, None

        # Phase 1: Pattern matching for quick reactions

        # Check for excitement (highest priority, fastest response)
        if self._matches_pattern(partial_text, self.excitement_patterns):
            min_time, max_time = self.timing_thresholds[InterjectionType.EXCITED]
            if min_time <= duration_seconds <= max_time:
                response = random.choice(self.excitement_responses)
                logger.info(f"[INTERJECTION] Excited reaction triggered at {duration_seconds:.1f}s")
                self._record_interjection()
                return InterjectionType.EXCITED, response

        # Check for surprise reveals
        if self._matches_pattern(partial_text, self.surprise_patterns):
            min_time, max_time = self.timing_thresholds[InterjectionType.SURPRISE]
            if min_time <= duration_seconds <= max_time:
                response = random.choice(self.surprise_responses)
                logger.info(f"[INTERJECTION] Surprise reaction triggered at {duration_seconds:.1f}s")
                self._record_interjection()
                return InterjectionType.SURPRISE, response

        # Check for agreement moments
        if self._matches_pattern(partial_text, self.agreement_patterns):
            min_time, max_time = self.timing_thresholds[InterjectionType.AGREEMENT]
            if min_time <= duration_seconds <= max_time:
                response = random.choice(self.agreement_responses)
                logger.info(f"[INTERJECTION] Agreement triggered at {duration_seconds:.1f}s")
                self._record_interjection()
                return InterjectionType.AGREEMENT, response

        # Check for concern/frustration
        if self._matches_pattern(partial_text, self.concern_patterns):
            # Be a bit more careful here, wait slightly longer
            if 1.5 <= duration_seconds <= 4.0:
                response = random.choice(self.concern_responses)
                logger.info(f"[INTERJECTION] Concern reaction triggered at {duration_seconds:.1f}s")
                self._record_interjection()
                return "concern", response

        # No interjection triggered
        return None, None

    def _record_interjection(self):
        """Record that an interjection occurred for rate limiting."""
        current_time = time.time()
        self.last_interjection_time = current_time
        self.interjections_in_last_minute.append(current_time)

    def reset_rate_limit(self):
        """Reset rate limiting (useful if user says 'let me finish')."""
        self.last_interjection_time = 0
        self.interjections_in_last_minute = []
        logger.info("Interjection rate limit reset")


# Quick test
if __name__ == "__main__":
    analyzer = InterjectionAnalyzer()

    # Test cases
    test_cases = [
        ("Guess what happened today!", 1.0),  # Should trigger excitement
        ("I just got accepted to Stanford!", 1.5),  # Should trigger excitement
        ("Python is the best language", 2.0),  # Should trigger agreement
        ("You know what I found out?", 1.2),  # Should trigger surprise
        ("This is so frustrating", 2.0),  # Should trigger concern
        ("Hello how are you", 1.0),  # Should NOT trigger
    ]

    print("\n=== Testing Interjection Analyzer ===\n")
    for text, duration in test_cases:
        interjection_type, response = analyzer.analyze(text, duration)
        if interjection_type:
            print(f"✓ '{text}' ({duration}s)")
            print(f"  → {interjection_type}: {response}\n")
        else:
            print(f"✗ '{text}' ({duration}s) - No interjection\n")
