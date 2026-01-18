"""
Encryption utilities for user data
Uses AES-256 with password-derived keys
"""
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit encryption key from a password using Scrypt KDF.
    
    Args:
        password: User's password
        salt: Random salt (store this with encrypted data)
    
    Returns:
        32-byte encryption key
    """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,  # CPU/memory cost parameter
        r=8,      # Block size
        p=1,      # Parallelization
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt_data(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt data using AES-GCM (authenticated encryption).
    
    Args:
        key: 32-byte encryption key
        plaintext: Data to encrypt
    
    Returns:
        iv (12 bytes) + ciphertext + auth tag
    """
    aesgcm = AESGCM(key)
    iv = os.urandom(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return iv + ciphertext


def decrypt_data(key: bytes, ciphertext: bytes) -> str:
    """
    Decrypt data encrypted with encrypt_data().
    
    Args:
        key: 32-byte encryption key
        ciphertext: iv + encrypted data + tag
    
    Returns:
        Decrypted plaintext
    
    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails (wrong key/tampered data)
    """
    aesgcm = AESGCM(key)
    iv = ciphertext[:12]
    ct = ciphertext[12:]
    plaintext = aesgcm.decrypt(iv, ct, None)
    return plaintext.decode()


def encrypt_user_profile(password: str, profile_data: dict, salt: bytes = None) -> tuple:
    """
    Encrypt user profile data.
    
    Args:
        password: User's password
        profile_data: Dictionary to encrypt (will be JSON-encoded)
        salt: Optional salt (generates new if None)
    
    Returns:
        (encrypted_blob_base64, salt_base64)
    """
    import json
    
    if salt is None:
        salt = os.urandom(16)
    
    key = derive_key(password, salt)
    plaintext = json.dumps(profile_data)
    encrypted = encrypt_data(key, plaintext)
    
    return base64.b64encode(encrypted).decode(), base64.b64encode(salt).decode()


def decrypt_user_profile(password: str, encrypted_blob_base64: str, salt_base64: str) -> dict:
    """
    Decrypt user profile data.
    
    Args:
        password: User's password
        encrypted_blob_base64: Base64-encoded encrypted data
        salt_base64: Base64-encoded salt
    
    Returns:
        Decrypted profile dictionary
    
    Raises:
        InvalidTag: Wrong password or corrupted data
    """
    import json
    
    salt = base64.b64decode(salt_base64)
    encrypted = base64.b64decode(encrypted_blob_base64)
    
    key = derive_key(password, salt)
    plaintext = decrypt_data(key, encrypted)
    
    return json.loads(plaintext)


# Example usage
if __name__ == "__main__":
    # Test encryption/decryption
    password = "my_secure_password"
    profile = {
        "voice_profile": {"pitch": 1.0, "speed": 1.2},
        "mannerisms": {"humor_level": 0.8},
        "preferences": {"avatar": "chibi", "theme": "dark"}
    }
    
    # Encrypt
    encrypted, salt = encrypt_user_profile(password, profile)
    print(f"Encrypted: {encrypted[:50]}...")
    print(f"Salt: {salt}")
    
    # Decrypt
    decrypted = decrypt_user_profile(password, encrypted, salt)
    print(f"Decrypted: {decrypted}")
    assert decrypted == profile
    print("✓ Encryption/decryption test passed!")
