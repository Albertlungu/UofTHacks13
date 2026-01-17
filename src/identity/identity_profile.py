"""
Core Identity Profile data structures.

Represents the complete identity of a user across 4 layers:
1. Communication Style - HOW they speak
2. Opinions & Beliefs - WHAT they believe
3. Thought Patterns - HOW they think
4. Memory & Context - Facts about them
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CommunicationStyle:
    """Layer 1: How the user communicates"""

    sentence_length: Dict[str, Any] = field(
        default_factory=lambda: {"avg_words": 0, "preference": "medium", "examples": []}
    )
    vocabulary: Dict[str, Any] = field(
        default_factory=lambda: {
            "level": "casual",
            "common_words": [],
            "technical_terms": [],
            "formality_score": 0.5,
        }
    )
    humor_style: Dict[str, Any] = field(
        default_factory=lambda: {"type": "none", "frequency": "never", "examples": []}
    )
    expressiveness: Dict[str, Any] = field(
        default_factory=lambda: {
            "level": "moderate",
            "uses_emphasis": False,
            "uses_qualifiers": [],
        }
    )
    filler_words: List[str] = field(default_factory=list)
    last_updated: str = ""
    confidence: float = 0.0
    sample_size: int = 0


@dataclass
class OpinionsBeliefs:
    """Layer 2: What the user believes"""

    beliefs: List[Dict[str, Any]] = field(default_factory=list)
    values: List[Dict[str, Any]] = field(default_factory=list)
    decision_patterns: Dict[str, Any] = field(
        default_factory=lambda: {
            "risk_tolerance": "moderate",
            "speed_vs_quality": "balanced",
            "examples": [],
        }
    )
    preferences: Dict[str, Any] = field(
        default_factory=lambda: {
            "work_style": "",
            "communication": "",
            "problem_solving": "",
        }
    )
    last_updated: str = ""


@dataclass
class ThoughtPatterns:
    """Layer 3: How the user thinks"""

    cognitive_style: Dict[str, Any] = field(
        default_factory=lambda: {
            "primary_mode": "analytical",
            "secondary_mode": "",
            "confidence": 0.0,
            "evidence": [],
        }
    )
    thinking_preferences: Dict[str, Any] = field(
        default_factory=lambda: {
            "thinks_in": "concrete examples",
            "question_style": "",
            "examples": [],
        }
    )
    problem_approach: Dict[str, Any] = field(
        default_factory=lambda: {
            "style": "systematic",
            "starts_with": "",
            "examples": [],
        }
    )
    interaction_style: Dict[str, Any] = field(
        default_factory=lambda: {
            "role": "explorer",
            "asks_questions": True,
            "pushes_back": "moderate",
            "examples": [],
        }
    )
    perspective_tendency: Dict[str, Any] = field(
        default_factory=lambda: {"sees": "both", "optimism_score": 0.5, "examples": []}
    )
    processing_speed: Dict[str, Any] = field(
        default_factory=lambda: {
            "makes_decisions": "moderately",
            "changes_mind": "sometimes",
            "deliberation_time": "medium",
        }
    )
    last_updated: str = ""
    analysis_count: int = 0


@dataclass
class MemoryContext:
    """Layer 4: Facts and context about the user"""

    personal_facts: List[Dict[str, Any]] = field(default_factory=list)
    people_mentioned: List[Dict[str, Any]] = field(default_factory=list)
    goals: List[Dict[str, Any]] = field(default_factory=list)
    interests: List[Dict[str, Any]] = field(default_factory=list)
    experiences: List[Dict[str, Any]] = field(default_factory=list)
    recent_topics: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class IdentityProfile:
    """
    Complete identity profile for a user.

    Progressively builds over time from 'nascent' to 'mature'.
    """

    user_id: str
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    opinions_beliefs: OpinionsBeliefs = field(default_factory=OpinionsBeliefs)
    thought_patterns: ThoughtPatterns = field(default_factory=ThoughtPatterns)
    memory_context: MemoryContext = field(default_factory=MemoryContext)
    total_exchanges_analyzed: int = 0
    created_at: str = ""
    last_updated: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

    @property
    def profile_maturity(self) -> str:
        """Determine profile maturity based on exchanges analyzed"""
        if self.total_exchanges_analyzed < 10:
            return "nascent"
        elif self.total_exchanges_analyzed < 30:
            return "emerging"
        elif self.total_exchanges_analyzed < 100:
            return "established"
        else:
            return "mature"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "communication_style": asdict(self.communication_style),
            "opinions_beliefs": asdict(self.opinions_beliefs),
            "thought_patterns": asdict(self.thought_patterns),
            "memory_context": asdict(self.memory_context),
            "total_exchanges_analyzed": self.total_exchanges_analyzed,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "profile_maturity": self.profile_maturity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityProfile":
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            communication_style=CommunicationStyle(
                **data.get("communication_style", {})
            ),
            opinions_beliefs=OpinionsBeliefs(**data.get("opinions_beliefs", {})),
            thought_patterns=ThoughtPatterns(**data.get("thought_patterns", {})),
            memory_context=MemoryContext(**data.get("memory_context", {})),
            total_exchanges_analyzed=data.get("total_exchanges_analyzed", 0),
            created_at=data.get("created_at", ""),
            last_updated=data.get("last_updated", ""),
        )

    @classmethod
    def create_empty(cls, user_id: str) -> "IdentityProfile":
        """Create a new empty profile"""
        return cls(user_id=user_id)

    def update_timestamp(self):
        """Update the last_updated timestamp"""
        self.last_updated = datetime.now().isoformat()
