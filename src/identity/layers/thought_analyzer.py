"""
Thought Pattern Analyzer

Analyzes HOW the user thinks - cognitive style and reasoning patterns.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from loguru import logger


class ThoughtAnalyzer:
    """Analyzes user's cognitive and thought patterns using Gemini"""

    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.4  # Moderate for pattern recognition
            },
        )

    def analyze(self, exchanges: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Deep analysis of how the user thinks.

        Args:
            exchanges: Last 20 exchanges for pattern detection

        Returns:
            Dict matching ThoughtPatterns schema
        """
        if not exchanges:
            return self._get_default_patterns()

        prompt = self._build_analysis_prompt(exchanges)

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)

            result["last_updated"] = datetime.now().isoformat()
            result["analysis_count"] = result.get("analysis_count", 0) + 1

            logger.info(f"Thought pattern analysis complete")
            return result

        except Exception as e:
            logger.error(f"Thought analysis failed: {e}")
            return self._get_default_patterns()

    def _build_analysis_prompt(self, exchanges: List[Dict[str, str]]) -> str:
        """Build deep thought pattern analysis prompt"""
        conversation_text = ""
        for ex in exchanges:
            conversation_text += f"User: {ex.get('user_text', '')}\n"
            conversation_text += f"AI: {ex.get('ai_response', '')}\n\n"

        analysis_json = {
            "cognitive_style": {
                "primary_mode": "analytical|intuitive|creative|practical",
                "secondary_mode": "...",
                "confidence": "0 to 10",
                "evidence": ["specific example"],
            },
            "thinking_preferences": {
                "thinks_in": "concrete examples|abstract concepts|visual patterns|logical steps",
                "question_style": "asks how|asks why|asks what if",
                "examples": ["example question they asked"],
            },
            "problem_approach": {
                "style": "top-down|bottom-up|lateral|systematic",
                "starts_with": "description",
                "examples": ["example"],
            },
            "interaction_style": {
                "role": "challenger|supporter|explorer|analyzer",
                "asks_questions": true | false,
                "pushes_back": "never|rarely|moderate|often",
                "examples": ["example"],
            },
            "perspective_tendency": {
                "sees": "opportunities|problems|both",
                "optimism_score": "0 to 10",
                "examples": ["example"],
            },
            "processing_speed": {
                "makes_decisions": "quickly|moderately|deliberately",
                "changes_mind": "easily|sometimes|rarely",
                "deliberation_time": "short|medium|long",
            },
        }

        return f"""DEEP COGNITIVE ANALYSIS: How does this user THINK?

Analyze their thought patterns, cognitive style, and reasoning approach:

CONVERSATION:
{conversation_text}

Return ONLY valid JSON:

{json.dumps(analysis_json, indent=4)}

Look for PATTERNS across multiple exchanges. Be specific and evidence-based."""

    def _get_default_patterns(self) -> Dict[str, Any]:
        """Return default thought patterns"""
        return {
            "cognitive_style": {
                "primary_mode": "analytical",
                "secondary_mode": "",
                "confidence": 0.0,
                "evidence": [],
            },
            "thinking_preferences": {
                "thinks_in": "concrete examples",
                "question_style": "",
                "examples": [],
            },
            "problem_approach": {
                "style": "systematic",
                "starts_with": "",
                "examples": [],
            },
            "interaction_style": {
                "role": "explorer",
                "asks_questions": True,
                "pushes_back": "moderate",
                "examples": [],
            },
            "perspective_tendency": {
                "sees": "both",
                "optimism_score": 0.5,
                "examples": [],
            },
            "processing_speed": {
                "makes_decisions": "moderately",
                "changes_mind": "sometimes",
                "deliberation_time": "medium",
            },
            "last_updated": datetime.now().isoformat(),
            "analysis_count": 0,
        }
