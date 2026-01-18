"""
Quick test script to debug login issue
"""
import bcrypt
from src.identity.database import get_collection

# Get the user
users = get_collection("users")
user = users.find_one({"username": "testuser"})

if user:
    print(f"✓ User found: {user['username']}")
    print(f"  Password hash type: {type(user['password_hash'])}")
    print(f"  Password hash: {user['password_hash']}")
    
    # Try password verification
    test_password = "testpass123"
    print(f"\nTesting password: {test_password}")
    
    try:
        # This is what the login route does
        result = bcrypt.checkpw(test_password.encode(), user["password_hash"])
        print(f"✓ Password check result: {result}")
    except Exception as e:
        print(f"✗ Password check error: {e}")
        print(f"  Error type: {type(e)}")
else:
    print("✗ User not found")
