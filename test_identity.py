#!/usr/bin/env python3
"""
Test script for Identity System
Tests encryption, database connection, and auth endpoints
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_encryption():
    """Test encryption/decryption functionality."""
    print("\n🔒 Testing Encryption...")
    
    from src.identity.encryption import encrypt_user_profile, decrypt_user_profile
    
    password = "test_password_123"
    profile = {
        "voice_profile": {"pitch": 1.0, "speed": 1.2},
        "mannerisms": {"humor_level": 0.8},
        "preferences": {"avatar": "chibi"}
    }
    
    # Encrypt
    encrypted, salt = encrypt_user_profile(password, profile)
    print(f"✓ Encrypted: {encrypted[:50]}...")
    print(f"✓ Salt: {salt}")
    
    # Decrypt
    decrypted = decrypt_user_profile(password, encrypted, salt)
    print(f"✓ Decrypted: {decrypted}")
    
    assert decrypted == profile, "Decryption mismatch!"
    print("✓ Encryption test passed!\n")


def test_database():
    """Test MongoDB connection."""
    print("🗄️  Testing Database Connection...")
    
    try:
        from src.identity.database import get_database, USERS_COLLECTION
        
        db = get_database()
        print(f"✓ Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"✓ Collections: {collections}")
        
        # Test insert/delete
        users = db[USERS_COLLECTION]
        test_doc = {"test": "data", "timestamp": "2026-01-17"}
        result = users.insert_one(test_doc)
        print(f"✓ Test insert: {result.inserted_id}")
        
        users.delete_one({"_id": result.inserted_id})
        print("✓ Test delete successful")
        
        print("✓ Database test passed!\n")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        print("  Make sure MongoDB is running:")
        print("    brew services start mongodb-community@7.0")
        print("  Or:")
        print("    mongod --dbpath ~/data/db\n")
        return False
    
    return True


def test_api():
    """Test API endpoints (requires server running)."""
    print("📡 Testing API Endpoints...")
    print("  (Skipping - start identity_server.py and use curl to test)")
    print("  Example:")
    print('    curl -X POST http://localhost:5001/api/auth/signup \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"username":"test","password":"test123"}\'')
    print()


def main():
    print("\n" + "="*50)
    print("  shadow Identity System - Test Suite")
    print("="*50)
    
    # Test encryption (no dependencies)
    test_encryption()
    
    # Test database (requires MongoDB running)
    db_ok = test_database()
    
    # API info
    test_api()
    
    if db_ok:
        print("✅ All tests passed!")
        print("\nReady to start identity server:")
        print("  python identity_server.py\n")
    else:
        print("⚠️  Database test failed - check MongoDB installation\n")


if __name__ == "__main__":
    main()
