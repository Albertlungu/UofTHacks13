# 3D Block Builder with Hand Tracking

A gesture-controlled 3D block building system using MediaPipe hand tracking and Three.js. Build in a Minecraft-style 3D grid using only your hands!

## Features

- White Minecraft-style 3D grid (5x5x5, 20x20x20 units)
- Real-time hand tracking with MediaPipe
- Gesture-based controls:
  - Right hand pinch: Add block (with hover preview)
  - Left hand pinch: Remove block
  - Single fist + drag: Rotate grid
  - Two fists + drag: Pan camera
  - Two hands pinch + spread/contract: Zoom in/out
  - Pinch re-center button: Reset camera and grid

## Architecture

### Backend (Python + MediaPipe)
- Clean hand tracking with MediaPipe Hands
- Gesture detection: pinch (left/right), fist detection
- WebSocket server streaming hand data to frontend
- Sends normalized 3D landmarks for proper coordinate transformation

### Frontend (React + Three.js)
- White Minecraft-style 3D grid visualization
- Proper MediaPipe-to-3D coordinate transformation using raycasting
- Real-time gesture processing
- Hover preview for block placement
- Interactive 3D re-center button

## Setup Instructions

### 1. Backend Setup

```bash
# Install Python dependencies (if not already installed)
pip install opencv-python mediapipe websockets loguru numpy

# Or use requirements.txt
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd src/frontend

# Install dependencies
npm install

# The following packages should be installed:
# - react
# - three
# - @react-three/fiber (optional, we use vanilla Three.js)
```

### 3. Running the System

**Terminal 1 - Start the hand tracking server:**
```bash
# From project root
python run_hand_tracker.py

# Or specify camera index if you have multiple cameras
python run_hand_tracker.py 1
```

**Terminal 2 - Start the React frontend:**
```bash
# From src/frontend
npm start

# This will open http://localhost:3000 in your browser
```

## Usage

1. Allow camera access when prompted
2. Position your hands in front of the camera
3. Use gestures to interact with the 3D grid:

### Gesture Guide

**Adding Blocks:**
- Make a pinch gesture with your RIGHT hand (thumb + index finger)
- A semi-transparent preview block will show where the block will be placed
- Release to confirm placement

**Removing Blocks:**
- Make a pinch gesture with your LEFT hand over an existing block
- The block will be removed

**Rotating the Grid:**
- Make a fist with ONE hand
- Drag your fist to rotate the grid in 3D space

**Panning the Camera:**
- Make fists with BOTH hands
- Drag to pan the camera view

**Zooming:**
- Make pinch gestures with BOTH hands
- Move hands apart to zoom in
- Move hands together to zoom out

**Re-centering:**
- Look for the blue circular button in the scene
- Pinch when your hand is near the button
- The camera and grid will reset to the default position

## Technical Details

### Coordinate Transformation
The key innovation in this implementation is proper coordinate transformation from MediaPipe's normalized screen space to Three.js 3D world space:

1. MediaPipe provides landmarks in normalized coordinates (x, y: 0-1, z: relative depth)
2. We convert to NDC (Normalized Device Coordinates: -1 to 1)
3. Use raycasting from camera through the screen point
4. Intersect with a plane at z=0 in world space
5. Snap to grid positions

This ensures perfect alignment between hand position and 3D interaction.

### Gesture Detection
- Pinch: Distance between thumb tip (landmark 4) and index tip (landmark 8) < threshold
- Fist: All fingers curled (fingertip Y >= PIP joint Y)
- Handedness: Properly handles camera mirroring (MediaPipe returns camera view)

### Performance
- 60 FPS target for smooth hand tracking
- Efficient WebSocket communication
- Optimized Three.js rendering
- Minimal latency between gesture and response

## Project Structure

```
.
├── run_hand_tracker.py          # Main runner script
├── src/
│   ├── hand_tracking/
│   │   ├── __init__.py
│   │   ├── tracker.py           # MediaPipe hand tracking
│   │   └── server.py            # WebSocket server
│   └── frontend/
│       └── src/
│           ├── App.js            # Main React app
│           └── BlockBuilder3D.js # Three.js 3D scene and gestures
└── 3D_BLOCK_BUILDER_README.md   # This file
```

## Troubleshooting

### Camera not detected
- Run `ls /dev/video*` on Linux or check System Preferences on macOS
- Try different camera indices: `python run_hand_tracker.py 1`
- Ensure no other application is using the camera

### WebSocket connection failed
- Make sure the backend is running first
- Check that port 8765 is not blocked by firewall
- Look for "WebSocket connected" message in browser console

### Hand tracking not working
- Ensure good lighting conditions
- Keep hands in frame and visible to camera
- Adjust `min_detection_confidence` in `tracker.py` if needed

### Performance issues
- Close other applications using GPU/camera
- Reduce frontend resolution or FPS if needed
- Check CPU usage of Python backend

## Future Enhancements

- Save/load block structures
- Different block colors
- Undo/redo functionality
- Export to 3D formats (OBJ, STL)
- Multiplayer mode
- More complex gestures (swipe to clear, etc.)

## Credits

Built with:
- [MediaPipe](https://google.github.io/mediapipe/) by Google
- [Three.js](https://threejs.org/) for 3D graphics
- [React](https://reactjs.org/) for UI
- [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) for real-time communication

## License

This project is part of UofTHacks13 hackathon submission.
