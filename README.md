# UofTHacks13 - Camera Feed with Facial Recognition

## Setup

### 1. Create and activate virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd src/frontend
npm install
cd ../..
```

## Running the Application

### Option 1: Camera Feed Only (No Facial Recognition)

```bash
# Terminal 1 - Backend
source venv/bin/activate
python src/camera/feed/camera_stream.py

# Terminal 2 - Frontend
cd src/frontend
npm start
```

### Option 2: Camera Feed with Facial Recognition

```bash
# Terminal 1 - Backend with facial analysis
source venv/bin/activate
python src/camera/facial_analysis/camera_with_faces.py

# Terminal 2 - Frontend
cd src/frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Video feed: http://localhost:5000/video_feed
- Face data API: http://localhost:5000/face_data

## Project Structure

```
src/
├── camera/
│   ├── feed/
│   │   └── camera_stream.py          # Basic camera stream
│   └── facial_analysis/
│       ├── face_detector.py           # Face detection logic
│       └── camera_with_faces.py       # Camera stream with facial analysis
└── frontend/
    └── src/
        └── App.js                     # React frontend
```