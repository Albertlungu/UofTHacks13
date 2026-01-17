# Center Stage Camera - Quick Start

## What is Center Stage Mode?

Center Stage automatically tracks people using the webcam and controls a stepper motor to pan the camera, keeping the person centered in frame. If they move left, the camera follows left. If they move right, it follows right.

## Quick Test (No Hardware Required)

Run the standalone test to see face tracking in action:

```bash
# Activate virtual environment
source venv/bin/activate

# Run test
python tests/test_center_stage.py
```

**Controls:**
- `q` - Quit
- `t` - Toggle tracking on/off
- `c` - Calibrate motor to center

You'll see face detection boxes and motor position updates in the console. On macOS/Windows, it runs in simulation mode (no actual hardware needed).

## How It Works

1. **Face Detection** - Uses OpenCV to detect faces in real-time
2. **Position Analysis** - Calculates if face is off-center
3. **Movement Decision** - Determines direction and amount to move
4. **Motor Control** - Commands stepper motor to pan camera
5. **Smoothing** - Averages recent positions to prevent jittery movement

## Parameters You Can Adjust

### In `FaceTracker` (src/camera/tracking/face_tracker.py):
- `center_threshold`: How far off-center before moving (default: 0.2 = 20%)
- `sensitivity`: Steps per distance unit (default: 30-50)
- `history_size`: Positions to average for smoothing (default: 5)

### In `center_stage.py` or test:
- `movement_cooldown`: Minimum seconds between movements (default: 0.5)
- `step_delay`: Delay between motor steps (default: 0.001)

## Hardware Setup (Raspberry Pi)

### Required Components:
- 28BYJ-48 stepper motor
- ULN2003 driver board
- 4 jumper wires

### Wiring:
Connect ULN2003 board to Raspberry Pi GPIO:
- IN1 → GPIO 17 (Pin 11)
- IN2 → GPIO 18 (Pin 12)
- IN3 → GPIO 27 (Pin 13)
- IN4 → GPIO 22 (Pin 15)
- Power the board with 5V

### Enable GPIO on Raspberry Pi:
```bash
# Uncomment RPi.GPIO in requirements.txt
pip install RPi.GPIO==0.7.1
```

## Run with Flask + Frontend

```bash
# Terminal 1 - Backend
source venv/bin/activate
python src/camera/center_stage.py

# Terminal 2 - Frontend
cd src/frontend
npm start
```

Open http://localhost:3000 to see the camera feed with face tracking overlays.

## API Examples

```bash
# Get face data and tracking info
curl http://localhost:5000/face_data

# Toggle tracking on/off
curl -X POST http://localhost:5000/tracking/toggle

# Calibrate motor to center
curl -X POST http://localhost:5000/motor/calibrate

# Check system health
curl http://localhost:5000/health
```

## Troubleshooting

**Camera not opening?**
- Check if another app is using the webcam
- Try changing camera index: `cv2.VideoCapture(1)` instead of `0`

**No faces detected?**
- Ensure good lighting
- Face the camera directly
- Adjust `scaleFactor` and `minNeighbors` in face_detector.py

**Motor not moving on Raspberry Pi?**
- Check GPIO wiring
- Verify RPi.GPIO is installed
- Run with `sudo` if permission errors

**Movements too jerky?**
- Increase `movement_cooldown` to reduce frequency
- Increase `history_size` for more smoothing
- Decrease `sensitivity` for smaller steps
