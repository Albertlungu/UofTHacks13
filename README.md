# UofTHacks13 - Center Stage Camera System

## Features

- **Camera Feed**: Live webcam streaming
- **Face Detection**: Real-time face recognition using OpenCV
- **Center Stage Mode**: Automatic camera tracking that follows people
- **Stepper Motor Control**: Hardware integration for camera pan movement

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

### Option 3: Center Stage Mode (Auto-Tracking)

```bash
# Terminal 1 - Backend with center stage
source venv/bin/activate
python src/camera/center_stage.py

# Terminal 2 - Frontend
cd src/frontend
npm start
```

### Option 4: Test Center Stage (No Frontend)

```bash
# Run standalone test with OpenCV window
source venv/bin/activate
python tests/test_center_stage.py

# Controls:
# - Press 'q' to quit
# - Press 't' to toggle tracking on/off
# - Press 'c' to calibrate motor to center
```

## API Endpoints

When running center stage mode:

- `GET /video_feed` - Video stream with face detection overlays
- `GET /face_data` - JSON data with face positions and tracking info
- `POST /tracking/toggle` - Toggle center stage tracking on/off
- `POST /motor/calibrate` - Reset motor to center position
- `GET /health` - Health check with system status
- `POST /shutdown` - Cleanup and shutdown

## Project Structure

```
src/
├── camera/
│   ├── feed/
│   │   └── camera_stream.py          # Basic camera stream
│   ├── facial_analysis/
│   │   ├── face_detector.py           # Face detection logic
│   │   └── camera_with_faces.py       # Camera with face detection
│   ├── tracking/
│   │   └── face_tracker.py            # Face tracking algorithms
│   └── center_stage.py                # Center stage system (Flask)
├── hardware/
│   └── stepper_motors/
│       └── stepper_controller.py      # Stepper motor control
└── frontend/
    └── src/
        └── App.js                     # React frontend

tests/
└── test_center_stage.py               # Standalone test
```

## Hardware Requirements

For full center stage functionality with motor control:
- Raspberry Pi (or any computer with GPIO pins)
- 28BYJ-48 stepper motor (or similar)
- ULN2003 motor driver board
- Webcam

**Note**: The system automatically runs in simulation mode on computers without GPIO support (like macOS/Windows). The tracking logic works, but motor commands are printed to console instead of controlling real hardware.

## How Center Stage Works

1. **Face Detection**: OpenCV detects faces in each frame
2. **Position Tracking**: Calculates face position relative to frame center
3. **Movement Decision**: If face is off-center beyond threshold, determines direction
4. **Motor Control**: Commands stepper motor to pan camera left/right
5. **Smoothing**: Uses position history to avoid jittery movements