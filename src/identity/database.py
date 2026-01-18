"""
MongoDB Database Connection and Configuration
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection URI
# Get from environment variable or use default for local development
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "shadow_identity")

# Initialize MongoDB client
_client = None
_db = None


def get_database():
    """
    Get MongoDB database instance.
    Creates connection on first call, reuses thereafter.
    
    Returns:
        Database instance
    """
    global _client, _db
    
    if _db is None:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            _client.admin.command('ping')
            _db = _client[DATABASE_NAME]
            print(f"✓ Connected to MongoDB: {DATABASE_NAME}")
        except ConnectionFailure as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise
    
    return _db


def get_collection(collection_name: str):
    """
    Get a specific collection from the database.
    
    Args:
        collection_name: Name of collection (users, conversations, etc.)
    
    Returns:
        Collection instance
    """
    db = get_database()
    return db[collection_name]


def close_connection():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("● MongoDB connection closed")


# Collection names
USERS_COLLECTION = "users"
CONVERSATIONS_COLLECTION = "conversations"
VOICE_PROFILES_COLLECTION = "voice_profiles"
PREFERENCES_COLLECTION = "preferences"
MANNERISMS_COLLECTION = "mannerisms"


# Create indexes for better performance
def setup_indexes():
    """Create database indexes for faster queries."""
    db = get_database()
    
    # Unique index on username
    db[USERS_COLLECTION].create_index("username", unique=True)
    
    # Index on user_id for quick lookups
    db[CONVERSATIONS_COLLECTION].create_index("user_id")
    db[VOICE_PROFILES_COLLECTION].create_index("user_id")
    db[PREFERENCES_COLLECTION].create_index("user_id")
    db[MANNERISMS_COLLECTION].create_index("user_id")
    
    print("✓ Database indexes created")


if __name__ == "__main__":
    # Test connection
    try:
        db = get_database()
        setup_indexes()
        print(f"✓ Database '{DATABASE_NAME}' ready")
        print(f"Collections: {db.list_collection_names()}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        close_connection()
