"""
AI package for Goonvengers.

This package handles:
- Gemini-based conversation companion with style adaptation
- Conversation flow management and orchestration
- Style analysis using HelpingAI-9B
- Conversation tracking and exchange management
"""

from src.ai.conversation_manager import ConversationManager
from src.ai.conversation_tracker import ConversationExchange, ConversationTracker
from src.ai.gemini_companion import GeminiCompanion
from src.ai.style_analyzer import StyleAnalyzer

__all__ = [
    "ConversationManager",
    "GeminiCompanion",
    "StyleAnalyzer",
    "ConversationTracker",
    "ConversationExchange",
]
