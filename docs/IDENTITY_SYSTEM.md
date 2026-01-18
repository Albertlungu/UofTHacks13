# 🔐 Identity & Authentication System

Complete user authentication system with MongoDB storage and AES-256 encryption for sensitive data.

## 📋 Features

- ✅ User signup & login
- ✅ JWT token-based authentication  
- ✅ Password hashing with bcrypt
- ✅ AES-256 encryption for user profiles
- ✅ MongoDB database storage
- ✅ Secure API endpoints
- ✅ Works on localhost & production

## 🗄️ Database Collections

```
users                  - User accounts & encrypted profiles
conversations          - Chat history per user
voice_profiles         - TTS settings & voice clones (encrypted)
preferences            - User settings
mannerisms            - Behavioral traits
```

## 🚀 Quick Start

### 1. Install MongoDB Locally

```bash
./setup_mongodb.sh
```

Start MongoDB:
```bash
brew services start mongodb-community@7.0
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and update if needed (defaults work for local development).

### 3. Install Python Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start Identity Server

```bash
python identity_server.py
```

Server runs on `http://localhost:5001`

## 📡 API Endpoints

### Authentication

#### POST /api/auth/signup
Create new user account.

**Request:**
```json
{
  "username": "alice",
  "password": "secure_password",
  "email": "alice@example.com"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "alice"
}
```

#### POST /api/auth/login
Authenticate user and get JWT token.

**Request:**
```json
{
  "username": "alice",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "alice",
  "user_id": "65a1b2c3d4e5f6789012345"
}
```

#### GET /api/auth/me
Get current user info (requires JWT token).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "65a1b2c3d4e5f6789012345",
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-01-17T10:30:00",
  "last_login": "2026-01-17T12:00:00"
}
```

### User Profile (Encrypted)

#### GET /api/auth/profile
Get decrypted user profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "password": "user_password"
}
```

**Response:**
```json
{
  "profile": {
    "voice_profile": { "pitch": 1.0, "speed": 1.2 },
    "mannerisms": { "humor_level": 0.8 },
    "preferences": { "avatar": "chibi", "theme": "dark" }
  }
}
```

#### PUT /api/auth/profile
Update user profile (encrypted).

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "password": "user_password",
  "profile": {
    "voice_profile": { "pitch": 1.2, "speed": 1.0 },
    "mannerisms": { "humor_level": 0.9 },
    "preferences": { "avatar": "chibi", "theme": "light" }
  }
}
```

## 🔒 Security Features

### Password Security
- **Hashing:** bcrypt with automatic salting
- **Never stored plaintext**
- **Minimum length:** 6 characters

### Data Encryption
- **Algorithm:** AES-256-GCM (authenticated encryption)
- **Key Derivation:** Scrypt KDF (password → encryption key)
- **Per-user encryption:** Each user's data encrypted with their password
- **Protection:** Other users cannot decrypt your data

### JWT Tokens
- **Expiry:** 7 days
- **Signature:** HS256
- **Payload:** user_id, username, timestamps
- **Validation:** Required for protected endpoints

## 🧪 Testing with curl

### Signup
```bash
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"test123"}'
```

### Login
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"test123"}'
```

### Get Profile (use token from login)
```bash
curl -X GET http://localhost:5001/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"password":"test123"}'
```

## 🌐 Production Deployment

### MongoDB Atlas Setup

1. Create account: https://www.mongodb.com/cloud/atlas/register
2. Create free cluster
3. Add database user
4. Set network access (whitelist IPs)
5. Get connection string

Update `.env`:
```env
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
JWT_SECRET_KEY=<generate_strong_random_key>
```

### Generate Strong JWT Secret
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📁 File Structure

```
src/identity/
  ├── __init__.py          - Package init
  ├── auth.py              - Authentication routes & JWT
  ├── database.py          - MongoDB connection & setup
  └── encryption.py        - AES-256 encryption utilities

identity_server.py         - Flask server entry point
.env.example              - Environment configuration template
setup_mongodb.sh          - MongoDB installation script
```

## 🔗 Integration with Main App

In your main Flask app:

```python
from src.identity.auth import auth_required

@app.route('/ai/chat', methods=['POST'])
@auth_required
def ai_chat():
    user_id = request.user_id
    username = request.username
    # Use authenticated user info...
```

## 📚 Resources

- **MongoDB Docs:** https://www.mongodb.com/docs/
- **JWT Tutorial:** https://pyjwt.readthedocs.io/
- **Bcrypt Guide:** https://github.com/pyca/bcrypt/
- **Cryptography:** https://cryptography.io/

## ⚠️ Important Notes

1. **Change JWT_SECRET_KEY in production!**
2. **Use HTTPS in production** (never send passwords over HTTP)
3. **Backup your MongoDB database regularly**
4. **User passwords cannot recover encrypted data** (if user forgets password, their encrypted profile is lost)
5. **Store .env in .gitignore** (never commit secrets!)

## 🐛 Troubleshooting

**MongoDB connection failed:**
```bash
# Check if MongoDB is running
brew services list

# Start if stopped
brew services start mongodb-community@7.0
```

**JWT token invalid:**
- Check token hasn't expired (7 days)
- Verify JWT_SECRET_KEY matches server
- Ensure "Bearer " prefix in Authorization header

**Decryption failed:**
- Wrong password
- Corrupted encrypted data
- Salt mismatch

## 📝 License

Part of the shadow project.
