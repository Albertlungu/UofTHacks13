"""
Speaking rate (Words Per Minute) calculation for adaptive speech pattern learning.
"""

import time
from typing import Optional

from loguru import logger


class SpeakingRateCalculator:
    """Calculates and tracks user's speaking rate (WPM)."""

    def __init__(self):
        self.speech_start_time: Optional[float] = None
        self.total_words = 0
        self.total_speech_time = 0.0

        logger.info("SpeakingRateCalculator initialized")

    def start_speech_segment(self):
        """Mark the start of a speech segment."""
        self.speech_start_time = time.time()

    def end_speech_segment(self, transcribed_text: str) -> Optional[float]:
        """
        End a speech segment and calculate WPM.

        Args:
            transcribed_text: The transcribed text from this segment

        Returns:
            Words per minute for this segment, or None if invalid
        """
        if self.speech_start_time is None:
            logger.warning("end_speech_segment called without start_speech_segment")
            return None

        # Calculate duration
        duration = time.time() - self.speech_start_time
        self.speech_start_time = None

        if duration < 0.5:
            logger.debug("Speech segment too short for WPM calculation")
            return None

        # Count words (simple split on whitespace)
        words = transcribed_text.split()
        word_count = len(words)

        if word_count == 0:
            return None

        # Calculate WPM for this segment
        minutes = duration / 60.0
        wpm = word_count / minutes

        # Update totals
        self.total_words += word_count
        self.total_speech_time += duration

        logger.debug(f"Segment: {word_count} words in {duration:.2f}s = {wpm:.1f} WPM")

        return wpm

    def get_average_wpm(self) -> Optional[float]:
        """
        Get the average WPM across all speech segments.

        Returns:
            Average words per minute, or None if not enough data
        """
        if self.total_speech_time < 1.0:
            return None

        minutes = self.total_speech_time / 60.0
        avg_wpm = self.total_words / minutes

        return avg_wpm

    def reset(self):
        """Reset all calculations."""
        self.speech_start_time = None
        self.total_words = 0
        self.total_speech_time = 0.0
        logger.debug("Speaking rate calculator reset")
