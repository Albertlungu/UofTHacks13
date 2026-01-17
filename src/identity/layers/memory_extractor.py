"""
Memory Extractor

Extracts factual information about the user - projects, people, goals, interests.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from loguru import logger


class MemoryExtractor:
    """Extracts factual information about user from conversations"""

    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.1  # Very low for factual extraction
            },
        )

    def extract(self, recent_exchanges: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract new facts about the user.

        Args:
            recent_exchanges: Last 5 exchanges

        Returns:
            Dict with new facts to add to memory
        """
        if not recent_exchanges:
            return self._get_empty_memory()

        prompt = self._build_extraction_prompt(recent_exchanges)

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)

            result["last_updated"] = datetime.now().isoformat()

            # Add timestamps and IDs
            timestamp = datetime.now().isoformat()
            for fact in result.get("personal_facts", []):
                if "id" not in fact:
                    fact["id"] = f"fact_{int(datetime.now().timestamp())}"
                if "timestamp" not in fact:
                    fact["timestamp"] = timestamp

            for person in result.get("people_mentioned", []):
                if "first_mentioned" not in person:
                    person["first_mentioned"] = timestamp

            for goal in result.get("goals", []):
                if "mentioned_at" not in goal:
                    goal["mentioned_at"] = timestamp

            logger.info(
                f"Memory extraction complete ({len(result.get('personal_facts', []))} new facts)"
            )
            return result

        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return self._get_empty_memory()

    def _build_extraction_prompt(self, exchanges: List[Dict[str, str]]) -> str:
        """Build fact extraction prompt"""
        conversation_text = ""
        for ex in exchanges:
            conversation_text += f"User: {ex.get('user_text', '')}\n\n"

        return f"""Extract FACTUAL INFORMATION about the user from these recent utterances:

USER SAID:
{conversation_text}

What new facts did you learn? Return ONLY valid JSON:

{{
  "personal_facts": [
    {{
      "category": "project|work|life|interest|skill",
      "fact": "clear factual statement",
      "source_quote": "exact quote",
      "relevance_score": <0-1>
    }}
  ],
  "people_mentioned": [
    {{
      "name": "person's name",
      "relationship": "relationship to user",
      "context": "context of mention"
    }}
  ],
  "goals": [
    {{
      "goal": "what they want to achieve",
      "status": "planning|in_progress|blocked|completed",
      "priority": "low|medium|high"
    }}
  ],
  "interests": [
    {{
      "topic": "topic name",
      "strength": <0-1>,
      "evidence": "why you think this"
    }}
  ],
  "experiences": [
    {{
      "type": "success|challenge|learning",
      "description": "what happened"
    }}
  ]
}}

Only extract facts that are clearly stated. Don't invent or over-infer."""

    def _get_empty_memory(self) -> Dict[str, Any]:
        """Return empty memory structure"""
        return {
            "personal_facts": [],
            "people_mentioned": [],
            "goals": [],
            "interests": [],
            "experiences": [],
            "recent_topics": [],
            "last_updated": datetime.now().isoformat(),
        }

    def merge_memory(
        self, existing: Dict[str, Any], new: Dict[str, Any], max_facts: int = 100
    ) -> Dict[str, Any]:
        """
        Merge new memory with existing, pruning old facts.

        Args:
            existing: Existing memory dict
            new: New memory dict from extraction
            max_facts: Maximum number of facts to keep

        Returns:
            Merged memory dict
        """
        merged = existing.copy()

        # Add new facts
        merged["personal_facts"].extend(new.get("personal_facts", []))

        # Sort by relevance * reference_count and prune
        for fact in merged["personal_facts"]:
            if "reference_count" not in fact:
                fact["reference_count"] = 1

        merged["personal_facts"] = sorted(
            merged["personal_facts"],
            key=lambda f: f.get("relevance_score", 0.5) * f.get("reference_count", 1),
            reverse=True,
        )[:max_facts]

        # Merge people (avoid duplicates)
        for new_person in new.get("people_mentioned", []):
            found = False
            for existing_person in merged["people_mentioned"]:
                if existing_person["name"].lower() == new_person["name"].lower():
                    found = True
                    break
            if not found:
                merged["people_mentioned"].append(new_person)

        # Merge goals
        for new_goal in new.get("goals", []):
            found = False
            for existing_goal in merged["goals"]:
                if existing_goal["goal"].lower() == new_goal["goal"].lower():
                    # Update status if changed
                    existing_goal["status"] = new_goal.get(
                        "status", existing_goal["status"]
                    )
                    found = True
                    break
            if not found:
                merged["goals"].append(new_goal)

        # Merge interests
        for new_interest in new.get("interests", []):
            found = False
            for existing_interest in merged["interests"]:
                if existing_interest["topic"].lower() == new_interest["topic"].lower():
                    # Strengthen interest
                    existing_interest["strength"] = min(
                        existing_interest.get("strength", 0.5) + 0.1, 1.0
                    )
                    existing_interest["evidence_count"] = (
                        existing_interest.get("evidence_count", 1) + 1
                    )
                    found = True
                    break
            if not found:
                new_interest["evidence_count"] = 1
                merged["interests"].append(new_interest)

        # Add new experiences
        merged["experiences"].extend(new.get("experiences", []))
        # Keep only last 50 experiences
        merged["experiences"] = merged["experiences"][-50:]

        merged["last_updated"] = new.get("last_updated", datetime.now().isoformat())

        return merged
