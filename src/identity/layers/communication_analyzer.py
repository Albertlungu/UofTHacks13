"""
Communication Style Analyzer

Analyzes HOW the user speaks using Gemini API.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from loguru import logger


class CommunicationAnalyzer:
    """Analyzes user's communication style using Gemini"""

    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.3  # Lower for consistent analysis
            },
        )

    def analyze(self, recent_utterances: List[str]) -> Dict[str, Any]:
        """
        Analyze communication style from recent utterances.

        Args:
            recent_utterances: Last 5-10 user utterances

        Returns:
            Dict matching CommunicationStyle schema
        """
        if not recent_utterances:
            return self._get_default_style()

        prompt = self._build_analysis_prompt(recent_utterances)

        try:
            response = self.model.generate_content(prompt)
            # Check if response or response.text is empty
            if not response or not response.text.strip():
                logger.warning(
                    "Gemini API returned an empty or whitespace-only response for communication analysis."
                )
                return self._get_default_style()

            # Attempt to parse JSON (strip code blocks if present)
            try:
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(
                    f"JSON decoding error in communication analysis: {e}. Raw response: '{response.text}'"
                )
                return self._get_default_style()

            # Add metadata
            result["last_updated"] = datetime.now().isoformat()
            result["sample_size"] = len(recent_utterances)
            result["confidence"] = self._calculate_confidence(
                result, len(recent_utterances)
            )

            # Ensure confidence is a float
            result["confidence"] = float(result["confidence"])

            logger.info(
                f"Communication analysis complete (confidence: {result['confidence']:.2f})"
            )
            return result

        except Exception as e:
            logger.error(f"Communication analysis failed: {e}")
            return self._get_default_style()

    def _build_analysis_prompt(self, utterances: List[str]) -> str:
        """Build Gemini prompt for communication analysis"""
        utterances_text = "\n".join([f"- {u}" for u in utterances])

        communication_json = {
            "sentence_length": {
                "avg_words": "number",
                "preference": "short|medium|long",
                "examples": ["example1", "example2"],
            },
            "vocabulary": {
                "level": "casual|formal|technical|mixed",
                "common_words": ["word1", "word2", "word3"],
                "technical_terms": ["term1", "term2"],
                "formality_score": "0 to 10",
            },
            "humor_style": {
                "type": "none|dry|playful|sarcastic|witty",
                "frequency": "never|rare|moderate|frequent",
                "examples": ["example if present"],
            },
            "expressiveness": {
                "level": "reserved|moderate|enthusiastic",
                "uses_emphasis": "true|false",
                "uses_qualifiers": ["qualifier1", "qualifier2"],
            },
            "filler_words": ["um", "like", "you know"],
        }

        return f"""Analyze this user's communication style from their speech:

USER'S RECENT UTTERANCES:
{utterances_text}

Extract detailed communication patterns and return ONLY valid JSON:

{json.dumps(communication_json, indent=4)}

Be specific and evidence-based. Only include patterns you can clearly see."""

    def _calculate_confidence(self, result: Dict, sample_size: int) -> float:
        """Calculate confidence score based on sample size and consistency"""
        # More samples = higher confidence
        size_factor = min(sample_size / 20.0, 1.0)
        # Presence of specific examples = higher confidence
        has_examples = len(result.get("vocabulary", {}).get("common_words", [])) > 0
        example_factor = 0.3 if has_examples else 0.0

        return min(0.5 + (size_factor * 0.4) + example_factor, 1.0)

    def _get_default_style(self) -> Dict[str, Any]:
        """Return default communication style"""
        return {
            "sentence_length": {
                "avg_words": 10,
                "preference": "medium",
                "examples": [],
            },
            "vocabulary": {
                "level": "casual",
                "common_words": [],
                "technical_terms": [],
                "formality_score": 0.5,
            },
            "humor_style": {"type": "none", "frequency": "never", "examples": []},
            "expressiveness": {
                "level": "moderate",
                "uses_emphasis": False,
                "uses_qualifiers": [],
            },
            "filler_words": [],
            "last_updated": datetime.now().isoformat(),
            "confidence": 0.0,
            "sample_size": 0,
        }
