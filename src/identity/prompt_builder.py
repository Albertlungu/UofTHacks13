"""
Prompt Builder

Builds dynamic system prompts from identity profiles.
"""

from typing import Optional

from src.identity.identity_profile import IdentityProfile


class PromptBuilder:
    """Builds system prompt additions from identity profile"""

    def build_from_profile(self, profile: IdentityProfile) -> str:
        """
        Generate identity-based system prompt additions.

        Returns:
            Formatted string to inject into GeminiCompanion system prompt
        """
        sections = []

        # Communication Style Section
        if profile.communication_style.confidence > 0.3:
            sections.append(
                self._build_communication_section(profile.communication_style)
            )

        # Beliefs Section
        if (
            len(profile.opinions_beliefs.beliefs) > 0
            or len(profile.opinions_beliefs.values) > 0
        ):
            sections.append(self._build_beliefs_section(profile.opinions_beliefs))

        # Thought Patterns Section
        if profile.thought_patterns.analysis_count > 0:
            sections.append(self._build_thought_section(profile.thought_patterns))

        # Memory Section (always include if any facts exist)
        if len(profile.memory_context.personal_facts) > 0:
            sections.append(self._build_memory_section(profile.memory_context))

        # Maturity indicator
        maturity_note = self._build_maturity_note(profile)

        if not sections:
            return ""  # No identity data yet

        return f"""
## USER IDENTITY PROFILE

{maturity_note}

{chr(10).join(sections)}

## ADAPTATION INSTRUCTIONS

Mirror this user naturally:
- Match their communication style (vocabulary, sentence length, tone)
- Align with their values and beliefs
- Adapt your reasoning style to match theirs
- Reference relevant context from past conversations
- The more mature the profile, the more precisely you should mirror them
"""

    def _build_communication_section(self, comm) -> str:
        """Build communication style section"""
        vocab_level = comm.vocabulary.get("level", "casual")
        sentence_pref = comm.sentence_length.get("preference", "medium")
        formality = comm.vocabulary.get("formality_score", 0.5)

        common_words = comm.vocabulary.get("common_words", [])[:5]
        words_list = (
            ", ".join([f"'{w}'" for w in common_words]) if common_words else "N/A"
        )

        return f"""### Communication Style (confidence: {comm.confidence:.2f})

- **Vocabulary**: {vocab_level} (formality: {formality:.1f}/1.0)
- **Sentence Length**: Prefers {sentence_pref} sentences
- **Common Words**: {words_list}
- **Expressiveness**: {comm.expressiveness.get("level", "moderate")}
- **Humor**: {comm.humor_style.get("type", "none")} ({comm.humor_style.get("frequency", "rare")})

**Adaptation**: Match their vocabulary level and sentence structure. Use similar casual expressions."""

    def _build_beliefs_section(self, beliefs) -> str:
        """Build opinions and beliefs section"""
        lines = ["### User's Beliefs & Values\n"]

        # Top 5 most confident beliefs
        sorted_beliefs = sorted(
            beliefs.beliefs,
            key=lambda b: b.get("confidence", 0) * b.get("mention_count", 1),
            reverse=True,
        )[:5]

        if sorted_beliefs:
            for belief in sorted_beliefs:
                topic = belief.get("topic", "Unknown")
                stance = belief.get("stance", "")
                lines.append(f"- **{topic}**: {stance}")

        # Core values
        if beliefs.values:
            lines.append("\n**Core Values:**")
            for value in beliefs.values[:3]:
                lines.append(f"- {value.get('value', '')}")

        lines.append(
            "\n**Adaptation**: Align your suggestions with these beliefs. Don't contradict their values."
        )

        return "\n".join(lines)

    def _build_thought_section(self, thought) -> str:
        """Build thought patterns section"""
        primary_mode = thought.cognitive_style.get("primary_mode", "analytical")
        thinks_in = thought.thinking_preferences.get("thinks_in", "concrete examples")
        role = thought.interaction_style.get("role", "explorer")

        return f"""### Thought Patterns

- **Cognitive Style**: {primary_mode}
- **Thinks In**: {thinks_in}
- **Interaction Role**: {role}
- **Problem Approach**: {thought.problem_approach.get("style", "systematic")}

**Adaptation**:
- If analytical: Provide structured reasoning
- If intuitive: Use analogies and patterns
- If they think in examples: Give concrete cases
- If they're a challenger: Welcome their pushback"""

    def _build_memory_section(self, memory) -> str:
        """Build memory/context section"""
        lines = ["### Context About User\n"]

        # Recent facts (top 5 by relevance)
        sorted_facts = sorted(
            memory.personal_facts,
            key=lambda f: f.get("relevance_score", 0) * f.get("reference_count", 1),
            reverse=True,
        )[:5]

        if sorted_facts:
            lines.append("**Current Context:**")
            for fact in sorted_facts:
                lines.append(f"- {fact.get('fact', '')}")

        # Active goals
        active_goals = [g for g in memory.goals if g.get("status") == "in_progress"]
        if active_goals:
            lines.append("\n**Their Goals:**")
            for goal in active_goals[:3]:
                lines.append(f"- {goal.get('goal', '')}")

        # Recent topics
        recent = sorted(
            memory.recent_topics,
            key=lambda t: t.get("last_discussed", ""),
            reverse=True,
        )[:3]
        if recent:
            topics = ", ".join([t.get("topic", "") for t in recent])
            lines.append(f"\n**Recent Topics**: {topics}")

        lines.append(
            "\n**Adaptation**: Reference this context naturally. Show you remember past conversations."
        )

        return "\n".join(lines)

    def _build_maturity_note(self, profile: IdentityProfile) -> str:
        """Add note about profile maturity"""
        maturity = profile.profile_maturity
        exchanges = profile.total_exchanges_analyzed

        notes = {
            "nascent": "Profile is new - being cautious with adaptation",
            "emerging": "Profile is developing - moderate personalization",
            "established": "Profile is solid - strong personalization",
            "mature": "Profile is mature - deep personalization, mirror precisely",
        }

        return f"**Profile Maturity**: {maturity.upper()} ({exchanges} exchanges analyzed)\n{notes.get(maturity, '')}"
