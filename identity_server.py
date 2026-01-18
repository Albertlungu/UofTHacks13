"""
Identity Server - Authentication & User Management API
Runs on port 5001 (separate from main app on 5000)
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os

from src.identity.auth import register_auth_routes
from src.identity.database import get_database, setup_indexes, close_connection

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Check if server is running."""
    try:
        # Test database connection
        db = get_database()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "collections": db.list_collection_names()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API documentation."""
    return jsonify({
        "name": "shadow Identity API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "POST /api/auth/signup": "Create new user account",
                "POST /api/auth/login": "Login and get JWT token",
                "GET /api/auth/me": "Get current user info (requires token)",
                "GET /api/auth/profile": "Get encrypted profile (requires token + password)",
                "PUT /api/auth/profile": "Update profile (requires token + password)"
            },
            "health": {
                "GET /health": "Check server health"
            }
        }
    })


# Register authentication routes
register_auth_routes(app)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🔐 shadow Identity Server")
    print("="*50)
    print("\nInitializing database...")
    
    try:
        setup_indexes()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Warning: {e}")
    
    print("\nStarting authentication API...")
    print("Endpoints:")
    print("  • POST /api/auth/signup")
    print("  • POST /api/auth/login")
    print("  • GET  /api/auth/me")
    print("  • GET  /api/auth/profile")
    print("  • PUT  /api/auth/profile")
    print("\n" + "="*50 + "\n")
    
    # Run server on port 5001 (main app is on 5000)
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
