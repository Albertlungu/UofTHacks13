"""
./src/ai/conversation_tracker.py

Conversation tracker for storing and managing user-AI exchanges.
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class ConversationExchange:
    """Represents a single user-AI exchange."""

    timestamp: str
    user_text: str
    ai_response: str
    exchange_number: int


class ConversationTracker:
    """
    Tracks conversation exchanges and triggers style analysis
    at appropriate intervals.
    """

    def __init__(
        self, user_id: str, conversation_dir: str = "./data/conversations"
    ) -> None:
        """
        Initialize conversation tracker.

        Args:
            user_id (str): User identifier
            conversation_dir (str, optional): Directory to store conversation logs. Defaults to "./data/conversations".
        """
        self.user_id = user_id
        self.conversation_dir = conversation_dir
        self.session_file = os.path.join(
            conversation_dir,
            f"{user_id}_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        # Create directory if needed
        os.makedirs(conversation_dir, exist_ok=True)

        # Exchange tracking
        self.exchanges: List[ConversationExchange] = []
        self.exchange_count = 0

        # Analysis trigger tracking
        self.last_analysis_at_exchange = 0
        self.analysis_intervals = [4, 8, 16, 24, 32]  # Decreasing frequency
        self.current_interval_index = 0

        logger.info(f"ConversationTracker initialized for user '{user_id}'")

    def add_exchange(self, user_text: str, ai_response: str) -> int:
        """
        Add a new conversation exchange.

        Args:
            user_text (str): What the user said
            ai_response (str): What the AI responded

        Returns:
            int: Current exchange number
        """
        self.exchange_count += 1

        exchange = ConversationExchange(
            timestamp=datetime.now().isoformat(),
            user_text=user_text,
            ai_response=ai_response,
            exchange_number=self.exchange_count,
        )

        self.exchanges.append(exchange)

        logger.debug(f"Added exchange #{self.exchange_count}")

        # Save to disk
        self._save_session()

        return self.exchange_count

    def should_trigger_analysis(self) -> bool:
        """
        Determine if style analysis should be triggered.

        Returns:
            True if analysis should run now
        """
        # First 8 exchanges: analyze every 4 exchanges
        if self.exchange_count <= 8:
            return self.exchange_count % 4 == 0

        # After exchange 8: use progressive intervals
        if self.current_interval_index < len(self.analysis_intervals):
            target_exchange = self.analysis_intervals[self.current_interval_index]

            if self.exchange_count >= target_exchange:
                self.current_interval_index += 1
                return True

        # After all defined intervals, analyze every 8 exchanges
        if self.exchange_count > 32:
            exchanges_since_last = self.exchange_count - self.last_analysis_at_exchange
            return exchanges_since_last >= 8

        return False

    def mark_analysis_completed(self):
        """Mark that analysis has been completed at current exchange."""
        self.last_analysis_at_exchange = self.exchange_count
        logger.info(f"Style analysis completed at exchange #{self.exchange_count}")

    def get_recent_exchanges(self, count: int = 4) -> List[ConversationExchange]:
        """
        Get the most recent N exchanges.

        Args:
            count: Number of exchanges to retrieve

        Returns:
            List of recent exchanges
        """
        return (
            self.exchanges[-count:] if len(self.exchanges) >= count else self.exchanges
        )

    def get_user_transcripts_since_last_analysis(self) -> List[str]:
        """
        Get all user transcripts since the last analysis.

        Returns:
            List of user text from recent exchanges
        """
        start_index = max(0, self.last_analysis_at_exchange)
        recent_exchanges = self.exchanges[start_index:]

        return [ex.user_text for ex in recent_exchanges]

    def get_all_user_transcripts(self) -> List[str]:
        """
        Get all user transcripts from the session.

        Returns:
            List of all user text
        """
        return [ex.user_text for ex in self.exchanges]

    def get_context_for_analysis(self, include_ai_responses: bool = True) -> str:
        """
        Get formatted context for style analysis.

        Args:
            include_ai_responses: Whether to include AI responses

        Returns:
            Formatted conversation context
        """
        recent = self.get_recent_exchanges(4)

        if not recent:
            return ""

        context_lines = []
        for ex in recent:
            context_lines.append(f"User: {ex.user_text}")
            if include_ai_responses:
                context_lines.append(f"AI: {ex.ai_response}")

        return "\n".join(context_lines)

    def _save_session(self):
        """Save current session to disk."""
        try:
            session_data = {
                "user_id": self.user_id,
                "exchange_count": self.exchange_count,
                "last_analysis_at": self.last_analysis_at_exchange,
                "exchanges": [asdict(ex) for ex in self.exchanges],
            }

            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def load_session(self, session_file: str) -> bool:
        """
        Load a previous session from file.

        Args:
            session_file: Path to session file

        Returns:
            True if loaded successfully
        """
        try:
            with open(session_file, "r") as f:
                data = json.load(f)

            self.exchange_count = data["exchange_count"]
            self.last_analysis_at_exchange = data["last_analysis_at"]
            self.exchanges = [ConversationExchange(**ex) for ex in data["exchanges"]]

            logger.info(f"Loaded session with {self.exchange_count} exchanges")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def get_session_summary(self) -> Dict:
        """
        Get a summary of the current session.

        Returns:
            Dictionary with session statistics
        """
        return {
            "user_id": self.user_id,
            "total_exchanges": self.exchange_count,
            "last_analysis_at": self.last_analysis_at_exchange,
            "next_analysis_in": self._exchanges_until_next_analysis(),
            "session_file": self.session_file,
        }

    def _exchanges_until_next_analysis(self) -> int:
        """Calculate how many exchanges until next analysis."""
        if self.exchange_count <= 8:
            return 4 - (self.exchange_count % 4)

        if self.current_interval_index < len(self.analysis_intervals):
            return (
                self.analysis_intervals[self.current_interval_index]
                - self.exchange_count
            )

        exchanges_since_last = self.exchange_count - self.last_analysis_at_exchange
        return 8 - exchanges_since_last


# Example usage
if __name__ == "__main__":
    tracker = ConversationTracker("test_user")

    # Simulate conversation
    for i in range(20):
        tracker.add_exchange(f"User message {i + 1}", f"AI response {i + 1}")

        if tracker.should_trigger_analysis():
            print(f"🔍 Trigger analysis at exchange #{tracker.exchange_count}")
            print(
                f"Recent transcripts: {tracker.get_user_transcripts_since_last_analysis()}"
            )
            tracker.mark_analysis_completed()

    print("\nSession summary:")
    print(json.dumps(tracker.get_session_summary(), indent=2))
