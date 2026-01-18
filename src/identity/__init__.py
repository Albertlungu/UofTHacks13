"""
Identity Learning System

Progressive multi-layer identity learning that makes the AI become more like the user.
Includes authentication, JWT tokens, and encrypted profile storage.
"""

from src.identity.identity_manager import IdentityManager
from src.identity.identity_profile import IdentityProfile

# Authentication & database imports
try:
    from src.identity.auth import auth_required, generate_token, verify_token
    from src.identity.database import get_database, get_collection
    from src.identity.encryption import encrypt_user_profile, decrypt_user_profile
    
    __all__ = [
        "IdentityProfile", 
        "IdentityManager",
        "auth_required",
        "generate_token",
        "verify_token",
        "get_database",
        "get_collection",
        "encrypt_user_profile",
        "decrypt_user_profile"
    ]
except ImportError:
    # Auth modules not yet installed
    __all__ = ["IdentityProfile", "IdentityManager"]
