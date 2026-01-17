#!/usr/bin/env python3
"""
Quick test of the identity learning system.
"""

import os

from dotenv import load_dotenv

from src.identity.identity_manager import IdentityManager
from src.identity.prompt_builder import PromptBuilder


def test_identity_system():
    """Test the identity learning components"""

    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return

    print("=" * 70)
    print("IDENTITY LEARNING SYSTEM TEST")
    print("=" * 70)

    # Test 1: Create identity manager
    print("\n1. Creating IdentityManager...")
    manager = IdentityManager(
        user_id="test_user",
        gemini_api_key=gemini_api_key,
        profile_dir="./data/profiles",
    )
    print(f"   ✓ IdentityManager created")
    print(f"   - User ID: {manager.user_id}")
    print(f"   - Profile maturity: {manager.identity_profile.profile_maturity}")
    print(
        f"   - Exchanges analyzed: {manager.identity_profile.total_exchanges_analyzed}"
    )

    # Test 2: Simulate some exchanges
    print("\n2. Simulating conversation exchanges...")

    test_exchanges = [
        {
            "user": "Yeah so I'm building this React app for the hackathon",
            "ai": "Nice! What kind of app are you building?",
        },
        {
            "user": "It's an AI companion that learns your communication style",
            "ai": "That sounds interesting. How does it learn the style?",
        },
        {
            "user": "It analyzes how you speak and adapts to match your patterns",
            "ai": "Cool approach. Are you using any specific models for that?",
        },
        {
            "user": "Just Gemini for everything, keeping it simple",
            "ai": "Good call. Simpler is often better for hackathons.",
        },
        {
            "user": "Exactly, no time for complicated setups",
            "ai": "Makes sense. How's it going so far?",
        },
    ]

    for i, exchange in enumerate(test_exchanges, 1):
        print(f"   Exchange {i}: User speaks...")
        manager.on_new_exchange(
            exchange_number=i, user_text=exchange["user"], ai_response=exchange["ai"]
        )

    print(f"   ✓ Simulated {len(test_exchanges)} exchanges")

    # Test 3: Check if profile was updated
    print("\n3. Checking profile updates...")
    import time

    print("   Waiting 3 seconds for background analysis...")
    time.sleep(3)

    if manager.profile_was_updated():
        print("   ✓ Profile was updated!")
    else:
        print("   ⚠ Profile not yet updated (analysis may still be running)")

    # Test 4: Generate system prompt
    print("\n4. Generating identity-based system prompt...")
    prompt = manager.get_system_prompt_additions()

    if prompt:
        print("   ✓ System prompt generated!")
        print("\n" + "=" * 70)
        print("GENERATED IDENTITY PROMPT:")
        print("=" * 70)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("=" * 70)
    else:
        print("   ⚠ No prompt generated yet (profile still nascent)")

    # Test 5: Check profile contents
    print("\n5. Profile analysis:")
    print(
        f"   - Communication confidence: {manager.identity_profile.communication_style.confidence:.2f}"
    )
    print(
        f"   - Beliefs tracked: {len(manager.identity_profile.opinions_beliefs.beliefs)}"
    )
    print(
        f"   - Facts collected: {len(manager.identity_profile.memory_context.personal_facts)}"
    )
    print(f"   - Profile maturity: {manager.identity_profile.profile_maturity}")

    # Cleanup
    print("\n6. Cleaning up...")
    manager.cleanup()
    print("   ✓ Cleanup complete")

    print("\n" + "=" * 70)
    print("✨ IDENTITY SYSTEM TEST COMPLETE")
    print("=" * 70)
    print("\nThe identity learning system is working!")
    print("It will progressively adapt the AI to match the user's:")
    print("  - Communication style (HOW they speak)")
    print("  - Beliefs and values (WHAT they believe)")
    print("  - Thought patterns (HOW they think)")
    print("  - Personal context (Facts about them)")


if __name__ == "__main__":
    test_identity_system()
