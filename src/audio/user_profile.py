"""
User profile management for adaptive speech pattern learning.
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from loguru import logger

from src.audio.audio_config import (
    DEFAULT_USER_ID,
    INITIAL_SILENCE_THRESHOLD,
    MAX_SILENCE_BEFORE_INTERRUPT,
    NORMAL_WORDS_PER_MINUTE,
    THINKING_PAUSE_THRESHOLD,
    USER_PROFILE_DIR,
)


@dataclass
class PausePattern:
    """Represents a pause pattern in speech."""

    duration: float  # Duration of pause in seconds
    location: str  # 'within_sentence', 'between_sentences', 'mid_thought'
    was_thinking_pause: bool  # True if user resumed speaking after


@dataclass
class UserSpeechProfile:
    """User's speech pattern profile."""

    user_id: str

    # Pause statistics
    avg_within_sentence_pause: float = 0.5
    avg_between_sentence_pause: float = 1.0
    avg_thinking_pause: float = 2.0

    # Speaking rate
    words_per_minute: float = NORMAL_WORDS_PER_MINUTE

    # Adapted thresholds
    silence_threshold: float = INITIAL_SILENCE_THRESHOLD
    thinking_pause_threshold: float = THINKING_PAUSE_THRESHOLD
    max_silence_before_interrupt: float = MAX_SILENCE_BEFORE_INTERRUPT

    # Calibration state
    is_calibrated: bool = False
    calibration_time: float = 0.0
    total_words_spoken: int = 0

    # Style analysis (from HelpingAI)
    style_summary: Optional[str] = None
    style_last_updated: Optional[str] = None

    # Raw pause data for learning
    pause_history: List[Dict] = None

    def __post_init__(self):
        if self.pause_history is None:
            self.pause_history = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "UserSpeechProfile":
        """Create from dictionary."""
        return cls(**data)


class UserProfileManager:
    """Manages user speech profiles with persistence."""

    def __init__(self, profile_dir: str = USER_PROFILE_DIR):
        self.profile_dir = profile_dir
        os.makedirs(profile_dir, exist_ok=True)
        logger.info(f"UserProfileManager initialized (dir: {profile_dir})")

    def get_profile_path(self, user_id: str) -> str:
        """Get the file path for a user profile."""
        return os.path.join(self.profile_dir, f"{user_id}.json")

    def load_profile(self, user_id: str = DEFAULT_USER_ID) -> UserSpeechProfile:
        """
        Load user profile from disk, or create default if doesn't exist.

        Args:
            user_id: User identifier

        Returns:
            UserSpeechProfile object
        """
        profile_path = self.get_profile_path(user_id)

        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    data = json.load(f)
                profile = UserSpeechProfile.from_dict(data)
                logger.info(
                    f"Loaded profile for user '{user_id}' "
                    f"(calibrated: {profile.is_calibrated}, "
                    f"WPM: {profile.words_per_minute:.1f})"
                )
                return profile
            except Exception as e:
                logger.error(f"Failed to load profile for '{user_id}': {e}")
                logger.info("Creating new default profile")

        # Create new profile
        profile = UserSpeechProfile(user_id=user_id)
        logger.info(f"Created new profile for user '{user_id}'")
        return profile

    def save_profile(self, profile: UserSpeechProfile):
        """
        Save user profile to disk.

        Args:
            profile: UserSpeechProfile to save
        """
        profile_path = self.get_profile_path(profile.user_id)

        try:
            with open(profile_path, "w") as f:
                json.dump(profile.to_dict(), f, indent=2)
            logger.info(f"Saved profile for user '{profile.user_id}'")
        except Exception as e:
            logger.error(f"Failed to save profile for '{profile.user_id}': {e}")

    def add_pause(self, profile: UserSpeechProfile, pause: PausePattern):
        """
        Add a pause observation to the profile.

        Args:
            profile: User profile to update
            pause: Pause pattern to add
        """
        # Add to history
        profile.pause_history.append(
            {
                "duration": pause.duration,
                "location": pause.location,
                "was_thinking_pause": pause.was_thinking_pause,
            }
        )

        # Keep only last 100 pauses for memory efficiency
        if len(profile.pause_history) > 100:
            profile.pause_history = profile.pause_history[-100:]

        logger.debug(
            f"Added pause: {pause.location}, {pause.duration:.2f}s, "
            f"thinking={pause.was_thinking_pause}"
        )

    def update_statistics(self, profile: UserSpeechProfile, learning_rate: float = 1.0):
        """
        Update profile statistics based on pause history.

        Args:
            profile: User profile to update
            learning_rate: How much to weight new data (0-1)
        """
        if not profile.pause_history:
            return

        # Calculate averages for different pause types
        within_sentence = [
            p["duration"]
            for p in profile.pause_history
            if p["location"] == "within_sentence"
        ]
        between_sentence = [
            p["duration"]
            for p in profile.pause_history
            if p["location"] == "between_sentences"
        ]
        thinking = [
            p["duration"] for p in profile.pause_history if p["was_thinking_pause"]
        ]

        # Update with exponential moving average
        if within_sentence:
            new_avg = sum(within_sentence) / len(within_sentence)
            profile.avg_within_sentence_pause = (
                learning_rate * new_avg
                + (1 - learning_rate) * profile.avg_within_sentence_pause
            )

        if between_sentence:
            new_avg = sum(between_sentence) / len(between_sentence)
            profile.avg_between_sentence_pause = (
                learning_rate * new_avg
                + (1 - learning_rate) * profile.avg_between_sentence_pause
            )

        if thinking:
            new_avg = sum(thinking) / len(thinking)
            profile.avg_thinking_pause = (
                learning_rate * new_avg
                + (1 - learning_rate) * profile.avg_thinking_pause
            )

        # Update thresholds based on averages
        profile.silence_threshold = max(
            profile.avg_between_sentence_pause + 0.5,
            1.0,  # Minimum 1 second
        )

        profile.thinking_pause_threshold = max(
            profile.avg_thinking_pause * 0.8,  # Slightly under average
            profile.silence_threshold + 0.5,
        )

        profile.max_silence_before_interrupt = max(
            profile.avg_thinking_pause * 1.5, profile.thinking_pause_threshold + 1.0
        )

        logger.debug(
            f"Updated stats: silence={profile.silence_threshold:.2f}s, "
            f"thinking={profile.thinking_pause_threshold:.2f}s, "
            f"max={profile.max_silence_before_interrupt:.2f}s"
        )

    def update_speaking_rate(
        self, profile: UserSpeechProfile, wpm: float, learning_rate: float = 1.0
    ):
        """
        Update user's words per minute.

        Args:
            profile: User profile to update
            wpm: New words per minute measurement
            learning_rate: How much to weight new data (0-1)
        """
        profile.words_per_minute = (
            learning_rate * wpm + (1 - learning_rate) * profile.words_per_minute
        )
        logger.debug(f"Updated WPM: {profile.words_per_minute:.1f}")

    def complete_calibration(self, profile: UserSpeechProfile):
        """
        Mark profile as calibrated.

        Args:
            profile: User profile to mark as calibrated
        """
        profile.is_calibrated = True
        logger.info(
            f"Calibration complete for user '{profile.user_id}' "
            f"({profile.total_words_spoken} words, "
            f"{profile.calibration_time:.1f}s)"
        )
        self.save_profile(profile)

    def reset_calibration(self, profile: UserSpeechProfile):
        """
        Reset calibration state to start fresh.

        Args:
            profile: User profile to reset
        """
        profile.is_calibrated = False
        profile.calibration_time = 0.0
        profile.total_words_spoken = 0
        profile.pause_history = []
        logger.info(f"Reset calibration for user '{profile.user_id}'")
