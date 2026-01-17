"""
Calibration manager that coordinates audio calibration and style analysis.
"""

from datetime import datetime
from typing import Callable, List, Optional

from loguru import logger

from src.audio.user_profile import UserProfileManager, UserSpeechProfile


class CalibrationManager:
    """
    Manages the calibration process including both audio pattern learning
    and style analysis with HelpingAI.
    """

    def __init__(
        self, profile_manager: UserProfileManager, user_profile: UserSpeechProfile
    ):
        """
        Initialize calibration manager.

        Args:
            profile_manager: User profile manager instance
            user_profile: Current user profile
        """
        self.profile_manager = profile_manager
        self.user_profile = user_profile

        # Calibration transcripts
        self.calibration_transcripts: List[str] = []

        # Style analyzer (will be initialized lazily)
        self.style_analyzer = None
        self.style_analysis_in_progress = False

        # Callback for when style analysis completes
        self.on_style_complete: Optional[Callable[[str], None]] = None

        logger.info("CalibrationManager initialized")

    def add_calibration_transcript(self, text: str):
        """
        Add a transcript from the calibration period.

        Args:
            text: Transcribed text from user
        """
        self.calibration_transcripts.append(text)
        logger.debug(
            f"Added calibration transcript ({len(self.calibration_transcripts)} total)"
        )

    def start_style_analysis(self, callback: Optional[Callable[[str], None]] = None):
        """
        Start style analysis in the background.

        Args:
            callback: Function to call when analysis completes
        """
        if self.style_analysis_in_progress:
            logger.warning("Style analysis already in progress")
            return

        if not self.calibration_transcripts:
            logger.warning("No calibration transcripts available for style analysis")
            return

        self.on_style_complete = callback
        self.style_analysis_in_progress = True

        logger.info(
            f"Starting style analysis on {len(self.calibration_transcripts)} transcripts"
        )

        # Import here to avoid loading the model until needed
        try:
            from src.ai.style_analyzer import StyleAnalyzer

            if self.style_analyzer is None:
                self.style_analyzer = StyleAnalyzer()
                logger.info("Loading HelpingAI model...")
                self.style_analyzer.load_model()

            # Run analysis in background
            self.style_analyzer.analyze_style(
                self.calibration_transcripts,
                analysis_type="initial",
                callback=self._on_analysis_complete,
            )

        except Exception as e:
            logger.error(f"Failed to start style analysis: {e}")
            self.style_analysis_in_progress = False

    def _on_analysis_complete(self, style_summary: str):
        """
        Called when style analysis completes.

        Args:
            style_summary: The generated style summary
        """
        self.style_analysis_in_progress = False

        if not style_summary:
            logger.error("Style analysis returned empty result")
            return

        # Update user profile
        self.user_profile.style_summary = style_summary
        self.user_profile.style_last_updated = datetime.now().isoformat()

        # Save profile
        self.profile_manager.save_profile(self.user_profile)

        logger.info("Style analysis complete and saved to profile")
        logger.debug(f"Style summary length: {len(style_summary)} characters")

        # Call user callback if provided
        if self.on_style_complete:
            try:
                self.on_style_complete(style_summary)
            except Exception as e:
                logger.error(f"Error in style complete callback: {e}")

    def get_style_summary_for_gemini(self) -> Optional[str]:
        """
        Get the formatted style summary for Gemini system instructions.

        Returns:
            Formatted style summary, or None if not available
        """
        if not self.user_profile.style_summary:
            return None

        # Add a header to make it clear this is user style info
        formatted = f"""<user_communication_profile>
{self.user_profile.style_summary}
</user_communication_profile>

Instructions: Adapt your communication style to match the user's patterns described above. Mirror their vocabulary level, tone, and pacing. Use similar sentence structures and expressions."""

        return formatted

    def cleanup(self):
        """Clean up resources."""
        if self.style_analyzer:
            self.style_analyzer.stop_background_processing()
            # Don't unload model as it might be needed for refinements
            logger.info("CalibrationManager cleaned up")
