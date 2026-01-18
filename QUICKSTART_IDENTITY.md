# 🚀 Identity System - Quick Start Guide

## What Was Built

A complete user authentication system with:
- ✅ User signup & login (bcrypt password hashing)
- ✅ JWT token authentication
- ✅ MongoDB database storage
- ✅ AES-256 encryption for sensitive data
- ✅ Flask API server on port 5001
- ✅ Production-ready with environment config

## Files Created

```
src/identity/
  ├── auth.py           - Authentication routes & JWT tokens
  ├── database.py       - MongoDB connection & collections
  └── encryption.py     - AES-256 encryption utilities

identity_server.py      - Flask server (port 5001)
test_identity.py        - Test suite
setup_mongodb.sh        - MongoDB installation script
.env.example           - Environment configuration template
docs/IDENTITY_SYSTEM.md - Full documentation

requirements.txt        - Updated with new dependencies:
  ├── bcrypt==4.1.2
  ├── pyjwt==2.8.0
  ├── pymongo==4.6.1
  └── cryptography==42.0.0
```

## 🏃 Getting Started (5 minutes)

### Step 1: Install MongoDB
```bash
./setup_mongodb.sh
brew services start mongodb-community@7.0
```

### Step 2: Setup Environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work locally)
```

### Step 3: Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Test System
```bash
python test_identity.py
```

### Step 5: Start Identity Server
```bash
python identity_server.py
```

Server runs on **http://localhost:5001**

## 🧪 Quick Test

### 1. Create User
```bash
curl -X POST http://localhost:5001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"test123"}'
```

Response:
```json
{
  "message": "User created successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "alice"
}
```

### 2. Login
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"test123"}'
```

### 3. Get Profile (use token from login)
```bash
TOKEN="<paste_token_here>"

curl -X GET http://localhost:5001/api/auth/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"test123"}'
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create new account |
| POST | `/api/auth/login` | Login & get JWT token |
| GET | `/api/auth/me` | Get user info (auth required) |
| GET | `/api/auth/profile` | Get encrypted profile (auth required) |
| PUT | `/api/auth/profile` | Update profile (auth required) |
| GET | `/health` | Health check |

## 🔗 Integration with Your App

### Protect Routes
```python
from src.identity.auth import auth_required

@app.route('/ai/chat', methods=['POST'])
@auth_required
def ai_chat():
    user_id = request.user_id  # Auto-injected by decorator
    username = request.username
    # Your code here...
```

### Frontend (React)
```javascript
// Login
const response = await fetch('http://localhost:5001/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const { token } = await response.json();
localStorage.setItem('token', token);

// Protected Request
const token = localStorage.getItem('token');
fetch('http://localhost:5001/api/auth/profile', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## 🔒 Security Features

- **Passwords:** Hashed with bcrypt (never stored plaintext)
- **Encryption:** AES-256-GCM for user profiles
- **Tokens:** JWT with 7-day expiry
- **Key Derivation:** Scrypt KDF (password → encryption key)
- **Per-User:** Each user's data encrypted with their password

## 🌐 Production Checklist

- [ ] Sign up for MongoDB Atlas (free tier)
- [ ] Get connection string
- [ ] Generate strong JWT secret: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Update `.env` with production values
- [ ] Deploy identity_server.py (Vercel/Fly.io/Render)
- [ ] Enable HTTPS (never send passwords over HTTP)
- [ ] Update CORS settings for your domain

## 📚 Full Documentation

See [docs/IDENTITY_SYSTEM.md](docs/IDENTITY_SYSTEM.md) for complete documentation.

## 🐛 Troubleshooting

**MongoDB connection failed:**
```bash
# Check if running
brew services list

# Start it
brew services start mongodb-community@7.0
```

**Module not found:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**JWT token invalid:**
- Token expired (7 days)
- Wrong JWT_SECRET_KEY
- Missing "Bearer " prefix

## ✅ What's Next?

1. **Test the system** with curl or Postman
2. **Build React login UI** (components provided in docs)
3. **Integrate with main app** using `@auth_required` decorator
4. **Store user preferences** in encrypted profiles
5. **Deploy to production** with MongoDB Atlas

---

**Ready to go!** 🚀

Start the identity server and test with the curl commands above.
