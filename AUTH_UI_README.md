# Identity Auth UI

A minimalist authentication interface built with React and shadcn/ui components.

## Features

- Clean, minimal design with no emojis
- User signup and login
- Encrypted profile management
- JWT-based authentication
- Secure password-based profile encryption

## Quick Start

### Option 1: Use the startup script

```bash
chmod +x start_auth_ui.sh
./start_auth_ui.sh
```

### Option 2: Manual startup

1. Start MongoDB:
```bash
mongod --dbpath ./data/db
```

2. Start the Identity API server (port 5001):
```bash
python3 identity_server.py
```

3. Start the React frontend (port 3000):
```bash
cd src/frontend
# Temporarily use the auth app
cp src/index-auth.js src/index.js
npm start
```

4. Open browser to: http://localhost:3000

## API Endpoints

The Identity API runs on `http://localhost:5001`:

- `POST /api/auth/signup` - Create new account
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (requires auth)
- `GET /api/auth/profile` - Get encrypted profile (requires password)
- `PUT /api/auth/profile` - Update profile (requires password)

## UI Components

### Login Page
- Username and password fields
- Clean error messaging
- Switch to signup link

### Signup Page
- Username, email (optional), password fields
- Password confirmation
- Validation feedback
- Switch to login link

### Profile Page
- Display current user info
- Load encrypted profile with password
- Edit profile data (JSON format)
- Save changes with encryption
- Logout button

## Technology Stack

- **Frontend**: React 18
- **UI Components**: shadcn/ui (custom implementation)
- **Styling**: Tailwind CSS 4
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Authentication**: JWT tokens
- **Encryption**: AES-256 for profile data

## File Structure

```
src/frontend/src/
├── AuthApp.jsx                  # Main auth application
├── contexts/
│   └── AuthContext.js           # Authentication state management
├── components/
│   ├── Login.jsx               # Login form
│   ├── Signup.jsx              # Signup form
│   ├── Profile.jsx             # Profile management
│   └── ui/
│       ├── button.jsx          # Button component
│       ├── card.jsx            # Card component
│       ├── input.jsx           # Input component
│       └── label.jsx           # Label component
└── lib/
    └── utils.js                # Utility functions
```

## Profile Data Structure

The encrypted profile can store:

```json
{
  "voice_profile": {
    "pitch": 0,
    "speed": 1.0,
    "accent": "neutral"
  },
  "mannerisms": {
    "formal": true,
    "verbose": false
  },
  "preferences": {
    "theme": "light",
    "language": "en"
  }
}
```

## Security Features

1. **Password Hashing**: bcrypt with salt
2. **JWT Tokens**: 7-day expiration
3. **Profile Encryption**: AES-256 with user password
4. **CORS Enabled**: For local development

## Development Notes

- API server must be running on port 5001
- Frontend runs on port 3000
- MongoDB required for user storage
- All profile data is encrypted at rest

## Customization

The UI uses a minimalist black and white color scheme:
- Primary: `neutral-900` (black)
- Background: `neutral-50` (light gray)
- Borders: `neutral-300`
- No emojis or decorative elements

To customize colors, edit the component files in `src/components/ui/`.
