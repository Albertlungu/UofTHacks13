"""
Authentication System - Flask Routes for Signup/Login
Includes JWT token generation and validation
"""
from flask import Flask, request, jsonify, Blueprint
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId
import os

from .database import get_collection, USERS_COLLECTION
from .encryption import encrypt_user_profile, decrypt_user_profile

# Create blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

# JWT Secret Key (load from environment in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_super_secret_key_change_in_production")
TOKEN_EXPIRY_DAYS = 7


def generate_token(user_id: str, username: str) -> str:
    """
    Generate JWT token for authenticated user.
    
    Args:
        user_id: MongoDB user _id
        username: Username
    
    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict
    
    Raises:
        jwt.InvalidTokenError: If token is invalid/expired
    """
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def auth_required(f):
    """
    Decorator to protect routes that require authentication.
    Extracts token from Authorization header and verifies it.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"error": "Missing authorization token"}), 401
        
        # Handle "Bearer <token>" format
        token = auth_header.replace("Bearer ", "").strip()
        
        try:
            # Verify and decode token
            payload = verify_token(token)
            
            # Attach user info to request object
            request.user_id = payload["user_id"]
            request.username = payload["username"]
            
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
    
    return wrapper


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new user account.
    
    Request body:
        {
            "username": "alice",
            "password": "secure_password",
            "email": "alice@example.com" (optional)
        }
    
    Returns:
        201: User created successfully
        400: Username already exists or validation error
    """
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        users = get_collection(USERS_COLLECTION)
        
        # Check if username exists
        if users.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Create default empty profile (encrypted)
        default_profile = {
            "voice_profile": {},
            "mannerisms": {},
            "preferences": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        encrypted_profile, salt = encrypt_user_profile(password, default_profile)
        
        # Insert user
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "profile_encrypted": encrypted_profile,
            "profile_salt": salt,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = users.insert_one(user_doc)
        
        # Generate token for immediate login
        token = generate_token(str(result.inserted_id), username)
        
        return jsonify({
            "message": "User created successfully",
            "token": token,
            "username": username
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user and return JWT token.
    
    Request body:
        {
            "username": "alice",
            "password": "secure_password"
        }
    
    Returns:
        200: Login successful with token
        401: Invalid credentials
    """
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({"username": username})
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode(), user["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Update last login
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Generate token
        token = generate_token(str(user["_id"]), username)
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "username": username,
            "user_id": str(user["_id"])
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Login error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/me", methods=["GET"])
@auth_required
def get_current_user():
    """
    Get current authenticated user's info.
    Requires valid JWT token in Authorization header.
    
    Returns:
        200: User info
        401: Unauthorized
    """
    try:
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({"_id": ObjectId(request.user_id)})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": str(user["_id"]),
            "username": user["username"],
            "email": user.get("email", ""),
            "created_at": user["created_at"].isoformat(),
            "last_login": user["last_login"].isoformat() if user["last_login"] else None
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/profile", methods=["GET", "POST"])
@auth_required
def get_profile():
    """
    Get user's decrypted profile data.
    Requires password in request body for decryption.
    
    Request body:
        {
            "password": "user_password"
        }
    
    Returns:
        200: Decrypted profile data
        401: Wrong password
    """
    try:
        data = request.json if request.json else {}
        password = data.get("password", "")
        
        if not password:
            return jsonify({"error": "Password required for decryption"}), 400
        
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({"_id": ObjectId(request.user_id)})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Verify password
        if not bcrypt.checkpw(password.encode(), user["password_hash"]):
            return jsonify({"error": "Invalid password"}), 401
        
        # Decrypt profile
        try:
            profile = decrypt_user_profile(
                password,
                user["profile_encrypted"],
                user["profile_salt"]
            )
            return jsonify({"profile": profile}), 200
        except Exception as e:
            return jsonify({"error": f"Decryption failed: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/profile", methods=["PUT"])
@auth_required
def update_profile():
    """
    Update user's profile data (encrypted).
    
    Request body:
        {
            "password": "user_password",
            "profile": {
                "voice_profile": {...},
                "mannerisms": {...},
                "preferences": {...}
            }
        }
    
    Returns:
        200: Profile updated
        401: Wrong password
    """
    try:
        data = request.json
        password = data.get("password", "")
        new_profile = data.get("profile", {})
        
        if not password:
            return jsonify({"error": "Password required for encryption"}), 400
        
        users = get_collection(USERS_COLLECTION)
        user = users.find_one({"_id": ObjectId(request.user_id)})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Verify password
        if not bcrypt.checkpw(password.encode(), user["password_hash"]):
            return jsonify({"error": "Invalid password"}), 401
        
        # Encrypt new profile
        encrypted_profile, salt = encrypt_user_profile(password, new_profile)
        
        # Update in database
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "profile_encrypted": encrypted_profile,
                "profile_salt": salt,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return jsonify({"message": "Profile updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def register_auth_routes(app: Flask):
    """Register authentication routes with Flask app."""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    print("✓ Auth routes registered at /api/auth")
