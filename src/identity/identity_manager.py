"""
Identity Manager

Central orchestrator for the identity learning system.
Coordinates analysis triggers, background workers, and profile updates.
"""

import json
import os
from typing import Any, Dict, Optional

from loguru import logger

from src.identity.background_worker import BackgroundWorker
from src.identity.identity_profile import (
    CommunicationStyle,
    IdentityProfile,
    MemoryContext,
    OpinionsBeliefs,
    ThoughtPatterns,
)
from src.identity.layers.belief_extractor import BeliefExtractor
from src.identity.layers.communication_analyzer import CommunicationAnalyzer
from src.identity.layers.memory_extractor import MemoryExtractor
from src.identity.layers.thought_analyzer import ThoughtAnalyzer
from src.identity.prompt_builder import PromptBuilder


class IdentityManager:
    """
    Central coordinator for identity learning system.
    Manages analysis triggers, background workers, and profile updates.
    """

    def __init__(
        self, user_id: str, gemini_api_key: str, profile_dir: str = "./data/profiles"
    ):
        self.user_id = user_id
        self.profile_dir = profile_dir
        self.profile_path = os.path.join(profile_dir, f"{user_id}_identity.json")

        # Load or create identity profile
        self.identity_profile = self._load_or_create_profile()

        # Initialize analyzers
        self.comm_analyzer = CommunicationAnalyzer(gemini_api_key)
        self.belief_extractor = BeliefExtractor(gemini_api_key)
        self.thought_analyzer = ThoughtAnalyzer(gemini_api_key)
        self.memory_extractor = MemoryExtractor(gemini_api_key)

        # Background worker for non-blocking analysis
        self.bg_worker = BackgroundWorker()
        self.bg_worker.start()

        # Prompt builder
        self.prompt_builder = PromptBuilder()

        # Track recent exchanges for analysis
        self.recent_exchanges = []

        # Flag to track if profile was updated since last check
        self._profile_updated = False

        logger.info(
            f"IdentityManager initialized for '{user_id}' "
            f"(maturity: {self.identity_profile.profile_maturity}, "
            f"exchanges: {self.identity_profile.total_exchanges_analyzed})"
        )

    def on_new_exchange(self, exchange_number: int, user_text: str, ai_response: str):
        """
        Called after each conversation exchange.
        Determines which analyses to trigger.

        Args:
            exchange_number: Current exchange count
            user_text: What the user said
            ai_response: What the AI responded
        """
        # Store exchange for analysis
        self.recent_exchanges.append(
            {"user_text": user_text, "ai_response": ai_response}
        )

        # Keep only last 50 exchanges in memory
        if len(self.recent_exchanges) > 50:
            self.recent_exchanges = self.recent_exchanges[-50:]

        # Communication Style + Memory: Every 5 exchanges
        if exchange_number % 5 == 0:
            self._trigger_communication_analysis()
            self._trigger_memory_extraction()

        # Opinions/Beliefs: Every 10 exchanges
        if exchange_number % 10 == 0:
            self._trigger_belief_extraction()

        # Thought Patterns: Every 20 exchanges
        if exchange_number % 20 == 0:
            self._trigger_thought_analysis()

        # Increment analyzed count
        self.identity_profile.total_exchanges_analyzed = exchange_number

    def _trigger_communication_analysis(self):
        """Queue communication style analysis in background"""
        # Get recent user utterances (last 10)
        recent_utterances = [ex["user_text"] for ex in self.recent_exchanges[-10:]]

        if not recent_utterances:
            return

        logger.debug("Triggering communication analysis")
        self.bg_worker.enqueue_task(
            task_type="communication_style",
            analyzer=self.comm_analyzer,
            data=recent_utterances,
            callback=self._on_communication_update,
        )

    def _on_communication_update(self, result: Dict[str, Any]):
        """Update profile with new communication analysis"""
        if not result:
            return

        self.identity_profile.communication_style = CommunicationStyle(**result)
        self.identity_profile.update_timestamp()
        self._save_profile()
        self._profile_updated = True
        logger.info(
            f"Communication style updated (confidence: {result.get('confidence', 0):.2f})"
        )

    def _trigger_belief_extraction(self):
        """Queue belief extraction in background"""
        # Get last 10 exchanges with both user and AI text
        recent = self.recent_exchanges[-10:]

        if not recent:
            return

        logger.debug("Triggering belief extraction")
        self.bg_worker.enqueue_task(
            task_type="beliefs",
            analyzer=self.belief_extractor,
            data=recent,
            callback=self._on_belief_update,
        )

    def _on_belief_update(self, result: Dict[str, Any]):
        """Update profile with new beliefs"""
        if not result:
            return

        # Merge new beliefs with existing
        existing_dict = self.identity_profile.opinions_beliefs.__dict__
        merged = self.belief_extractor.merge_beliefs(existing_dict, result)

        self.identity_profile.opinions_beliefs = OpinionsBeliefs(**merged)
        self.identity_profile.update_timestamp()
        self._save_profile()
        self._profile_updated = True
        logger.info(f"Beliefs updated ({len(result.get('beliefs', []))} new beliefs)")

    def _trigger_thought_analysis(self):
        """Queue thought pattern analysis in background"""
        # Get last 20 exchanges for deep pattern analysis
        recent = self.recent_exchanges[-20:]

        if not recent:
            return

        logger.debug("Triggering thought pattern analysis")
        self.bg_worker.enqueue_task(
            task_type="thought_patterns",
            analyzer=self.thought_analyzer,
            data=recent,
            callback=self._on_thought_update,
        )

    def _on_thought_update(self, result: Dict[str, Any]):
        """Update profile with new thought patterns"""
        if not result:
            return

        self.identity_profile.thought_patterns = ThoughtPatterns(**result)
        self.identity_profile.update_timestamp()
        self._save_profile()
        self._profile_updated = True
        logger.info("Thought patterns updated")

    def _trigger_memory_extraction(self):
        """Queue memory extraction in background"""
        # Get last 5 exchanges for fact extraction
        recent = self.recent_exchanges[-5:]

        if not recent:
            return

        logger.debug("Triggering memory extraction")
        self.bg_worker.enqueue_task(
            task_type="memory",
            analyzer=self.memory_extractor,
            data=recent,
            callback=self._on_memory_update,
        )

    def _on_memory_update(self, result: Dict[str, Any]):
        """Update profile with new memories"""
        if not result:
            return

        # Merge new memory with existing
        existing_dict = self.identity_profile.memory_context.__dict__
        merged = self.memory_extractor.merge_memory(existing_dict, result)

        self.identity_profile.memory_context = MemoryContext(**merged)
        self.identity_profile.update_timestamp()
        self._save_profile()
        self._profile_updated = True
        logger.info(
            f"Memory updated ({len(result.get('personal_facts', []))} new facts)"
        )

    def get_system_prompt_additions(self) -> str:
        """
        Generate identity-based additions to system prompt.

        Returns:
            Formatted prompt string to inject into GeminiCompanion
        """
        return self.prompt_builder.build_from_profile(self.identity_profile)

    def profile_was_updated(self) -> bool:
        """
        Check if profile was updated since last check.

        Returns:
            True if profile was updated, resets flag
        """
        if self._profile_updated:
            self._profile_updated = False
            return True
        return False

    def _load_or_create_profile(self) -> IdentityProfile:
        """Load existing profile or create new one"""
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded identity profile from {self.profile_path}")
                return IdentityProfile.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load profile: {e}, creating new")

        logger.info(f"Creating new identity profile for '{self.user_id}'")
        return IdentityProfile.create_empty(self.user_id)

    def _save_profile(self):
        """Save identity profile to disk"""
        try:
            # Ensure directory exists
            os.makedirs(self.profile_dir, exist_ok=True)

            # Save profile
            with open(self.profile_path, "w") as f:
                json.dump(self.identity_profile.to_dict(), f, indent=2)

            logger.debug(f"Saved identity profile to {self.profile_path}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    def cleanup(self):
        """Stop background workers and save final state"""
        logger.info("Cleaning up IdentityManager...")
        self.bg_worker.stop()
        self._save_profile()
        logger.info("IdentityManager cleanup complete")
