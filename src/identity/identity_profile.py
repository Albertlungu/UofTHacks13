"""
Defines the core data structures for the multi-layered Identity Profile.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class CommunicationStyle:
    """Layer 1: HOW the user speaks."""
    sentence_length: Dict[str, Any] = field(default_factory=dict)
    vocabulary: Dict[str, Any] = field(default_factory=dict)
    humor_style: Dict[str, Any] = field(default_factory=dict)
    expressiveness: Dict[str, Any] = field(default_factory=dict)
    filler_words: List[str] = field(default_factory=list)
    last_updated: str = ""
    confidence: float = 0.0
    sample_size: int = 0


@dataclass
class OpinionsBeliefs:
    """Layer 2: WHAT the user believes."""
    beliefs: List[Dict[str, Any]] = field(default_factory=list)
    values: List[Dict[str, Any]] = field(default_factory=list)
    decision_patterns: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = ""


@dataclass
class ThoughtPatterns:
    """Layer 3: HOW the user thinks."""
    cognitive_style: Dict[str, Any] = field(default_factory=dict)
    thinking_preferences: Dict[str, Any] = field(default_factory=dict)
    problem_approach: Dict[str, Any] = field(default_factory=dict)
    interaction_style: Dict[str, Any] = field(default_factory=dict)
    perspective_tendency: Dict[str, Any] = field(default_factory=dict)
    processing_speed: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = ""
    analysis_count: int = 0


@dataclass
class MemoryContext:
    """Layer 4: Facts and context about the user."""
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
    Central dataclass representing all identity layers of a user.
    """
    user_id: str
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    opinions_beliefs: OpinionsBeliefs = field(default_factory=OpinionsBeliefs)
    thought_patterns: ThoughtPatterns = field(default_factory=ThoughtPatterns)
    memory_context: MemoryContext = field(default_factory=MemoryContext)
    total_exchanges_analyzed: int = 0

    @property
    def profile_maturity(self) -> str:
        """Determine profile maturity based on exchanges analyzed."""
        if self.total_exchanges_analyzed < 10:
            return "nascent"
        elif self.total_exchanges_analyzed < 30:
            return "emerging"
        elif self.total_exchanges_analyzed < 100:
            return "established"
        else:
            return "mature"

    def to_dict(self) -> Dict:
        """Convert the identity profile to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "IdentityProfile":
        """Create an IdentityProfile from a dictionary."""
        # Manually construct nested dataclasses
        comm_style = CommunicationStyle(**data.get('communication_style', {}))
        opinions = OpinionsBeliefs(**data.get('opinions_beliefs', {}))
        thought = ThoughtPatterns(**data.get('thought_patterns', {}))
        memory = MemoryContext(**data.get('memory_context', {}))
        
        return cls(
            user_id=data['user_id'],
            communication_style=comm_style,
            opinions_beliefs=opinions,
            thought_patterns=thought,
            memory_context=memory,
            total_exchanges_analyzed=data.get('total_exchanges_analyzed', 0)
        )

    @classmethod
    def create_empty(cls, user_id: str) -> "IdentityProfile":
        """Create a new, empty identity profile for a user."""
        return cls(user_id=user_id)

    def update_timestamp(self, layer_name: str, timestamp: str):
        """Updates the last_updated timestamp for a specific identity layer."""
        if hasattr(self, layer_name):
            layer = getattr(self, layer_name)
            if hasattr(layer, 'last_updated'):
                layer.last_updated = timestamp
        else:
            # Handle cases where the layer_name might not directly map to an attribute
            # For example, if layer_name is 'communication_style_analysis'
            # but the attribute is 'communication_style'
            # For now, we'll assume direct mapping.
            pass