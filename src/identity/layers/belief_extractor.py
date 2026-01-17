"""
Belief Extractor

Extracts WHAT the user believes - opinions, values, decision patterns.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from loguru import logger


class BeliefExtractor:
    """Extracts user opinions, beliefs, and values using Gemini"""

    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.2  # Very low for factual extraction
            },
        )

    def extract(self, exchanges: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract beliefs and values from conversation exchanges.

        Args:
            exchanges: Recent conversation exchanges with user_text and ai_response

        Returns:
            Dict matching OpinionsBeliefs schema
        """
        if not exchanges:
            return self._get_empty_beliefs()

        prompt = self._build_extraction_prompt(exchanges)

        try:
            response = self.model.generate_content(prompt)
            # Check if response or response.text is empty
            if not response or not response.text.strip():
                logger.warning(
                    "Gemini API returned an empty or whitespace-only response for belief extraction."
                )
                return self._get_empty_beliefs()

            # Attempt to parse JSON
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
                    f"JSON decoding error in belief extraction: {e}. Raw response: '{response.text}'"
                )
                return self._get_empty_beliefs()

            # Add metadata
            result["last_updated"] = datetime.now().isoformat()

            # Add IDs and timestamps to beliefs
            for belief in result.get("beliefs", []):
                if "id" not in belief:
                    belief["id"] = f"belief_{int(datetime.now().timestamp())}"
                if "first_mentioned" not in belief:
                    belief["first_mentioned"] = datetime.now().isoformat()
                if "mention_count" not in belief:
                    belief["mention_count"] = 1

            for value in result.get("values", []):
                if "id" not in value:
                    value["id"] = f"value_{int(datetime.now().timestamp())}"

            logger.info(
                f"Belief extraction complete ({len(result.get('beliefs', []))} beliefs found)"
            )
            return result

        except Exception as e:
            logger.error(f"Belief extraction failed: {e}")
            return self._get_empty_beliefs()

    def _build_extraction_prompt(self, exchanges: List[Dict[str, str]]) -> str:
        """Build Gemini prompt for belief extraction"""
        conversation_text = ""
        for ex in exchanges:
            conversation_text += f"User: {ex.get('user_text', '')}\n"
            conversation_text += f"AI: {ex.get('ai_response', '')}\n\n"

        belief_json = {
            "beliefs": [
                {
                    "category": "technology|work|life|philosophy|etc",
                    "topic": "specific topic",
                    "stance": "what they believe",
                    "confidence": "0 to 10",
                    "supporting_quotes": ["quote from conversation"],
                }
            ],
            "values": [
                {
                    "value": "core value name",
                    "evidence": ["supporting quote"],
                    "strength": "0 to 10",
                }
            ],
            "decision_patterns": {
                "risk_tolerance": "low|moderate|high",
                "speed_vs_quality": "speed|balanced|quality",
                "examples": ["example"],
            },
            "preferences": {
                "work_style": "description",
                "communication": "description",
                "problem_solving": "description",
            },
        }

        return f"""Extract the user's opinions, beliefs, and values from this conversation:

CONVERSATION:
{conversation_text}

Identify and return ONLY valid JSON:

{json.dumps(belief_json, indent=4)}

Only include beliefs that are clearly expressed. Don't infer too much."""

    def _get_empty_beliefs(self) -> Dict[str, Any]:
        """Return empty beliefs structure"""
        return {
            "beliefs": [],
            "values": [],
            "decision_patterns": {
                "risk_tolerance": "moderate",
                "speed_vs_quality": "balanced",
                "examples": [],
            },
            "preferences": {
                "work_style": "",
                "communication": "",
                "problem_solving": "",
            },
            "last_updated": datetime.now().isoformat(),
        }

    def merge_beliefs(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge new beliefs with existing, updating counts and confidence.

        Args:
            existing: Existing beliefs dict
            new: New beliefs dict from analysis

        Returns:
            Merged beliefs dict
        """
        merged = existing.copy()

        # Merge beliefs - increment count if similar topic exists
        for new_belief in new.get("beliefs", []):
            found_similar = False
            for existing_belief in merged["beliefs"]:
                if self._beliefs_similar(existing_belief, new_belief):
                    # Update existing belief
                    existing_belief["mention_count"] = (
                        existing_belief.get("mention_count", 1) + 1
                    )
                    existing_belief["confidence"] = min(
                        existing_belief.get("confidence", 0.5) + 0.1, 1.0
                    )
                    existing_belief["supporting_quotes"].extend(
                        new_belief.get("supporting_quotes", [])
                    )
                    found_similar = True
                    break

            if not found_similar:
                merged["beliefs"].append(new_belief)

        # Merge values similarly
        for new_value in new.get("values", []):
            found_similar = False
            for existing_value in merged["values"]:
                if existing_value["value"].lower() == new_value["value"].lower():
                    existing_value["strength"] = min(
                        existing_value.get("strength", 0.5) + 0.1, 1.0
                    )
                    existing_value["evidence"].extend(new_value.get("evidence", []))
                    found_similar = True
                    break

            if not found_similar:
                merged["values"].append(new_value)

        # Update patterns and preferences
        merged["decision_patterns"] = new.get(
            "decision_patterns", merged["decision_patterns"]
        )
        merged["preferences"] = new.get("preferences", merged["preferences"])
        merged["last_updated"] = new.get("last_updated", datetime.now().isoformat())

        return merged

    def _beliefs_similar(self, belief1: Dict, belief2: Dict) -> bool:
        """Check if two beliefs are about the same topic"""
        topic1 = belief1.get("topic", "").lower()
        topic2 = belief2.get("topic", "").lower()
        category1 = belief1.get("category", "").lower()
        category2 = belief2.get("category", "").lower()

        return (topic1 == topic2 and category1 == category2) or (
            topic1 in topic2 or topic2 in topic1
        )
