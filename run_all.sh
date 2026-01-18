#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "  shadow Setup & Launcher"
echo "=========================================="
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Virtual environment directory
VENV_DIR="venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created"
    echo ""
else
    echo "Virtual environment already exists"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Virtual environment activated"
echo ""

# Install/upgrade requirements
echo "Installing requirements..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Requirements installed"
echo ""

# Check available cameras
echo "Checking available cameras..."
python3 << 'PYTHON_EOF'
import cv2
import sys

available_cameras = []
for i in range(5):  # Check first 5 camera indices
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        available_cameras.append(i)
        cap.release()

print(f"Available cameras: {available_cameras}")

if len(available_cameras) < 2:
    print("\nWARNING: Only {} camera(s) detected!".format(len(available_cameras)))
    print("For full functionality, you need 2 cameras:")
    print("  - Camera 0: Face tracking (center_stage)")
    print("  - Camera 1: Hand tracking (3D builder)")
    print("\nContinuing with available cameras...")
    sys.exit(len(available_cameras))
else:
    print("Both cameras detected - ready to launch!")
    sys.exit(2)
PYTHON_EOF

NUM_CAMERAS=$?
echo ""

echo "=========================================="
echo "  Launching services in separate iTerm tabs..."
echo "=========================================="
echo ""

# Start camera system in new iTerm tab (requires camera 0)
if [ $NUM_CAMERAS -ge 1 ]; then
    echo "Starting camera system (Center Stage) on camera 0..."
    osascript <<EOF
tell application "iTerm"
    tell current window
        create tab with default profile
        tell current session
            write text "cd \"$SCRIPT_DIR\" && source venv/bin/activate && python src/camera/center_stage.py"
        end tell
    end tell
end tell
EOF
    echo "Camera system launched in new tab"
    echo "  - Flask server on http://localhost:5000"
    echo "  - Video feed at http://localhost:5000/video_feed"
    echo ""
    sleep 2
else
    echo "SKIPPING: Camera system (no camera 0 available)"
    echo ""
fi

# Start audio conversation system in new iTerm tab
echo "Starting audio conversation system..."
osascript <<EOF
tell application "iTerm"
    tell current window
        create tab with default profile
        tell current session
            write text "cd \"$SCRIPT_DIR\" && source venv/bin/activate && python main.py"
        end tell
    end tell
end tell
EOF
echo "Audio system launched in new tab"
echo "  - Voice conversation active"
echo ""
sleep 2

# Start hand tracker in new iTerm tab (requires camera 1)
if [ $NUM_CAMERAS -ge 2 ]; then
    echo "Starting hand tracker (3D builder backend) on camera 1..."
    osascript <<EOF
tell application "iTerm"
    tell current window
        create tab with default profile
        tell current session
            write text "cd \"$SCRIPT_DIR\" && source venv/bin/activate && python run_hand_tracker.py 1"
        end tell
    end tell
end tell
EOF
    echo "Hand tracker launched in new tab"
    echo ""
    sleep 2
else
    echo "SKIPPING: Hand tracker (no camera 1 available)"
    echo "  - If you want hand tracking, connect a second camera"
    echo "  - Or modify run_hand_tracker.py to use camera 0 (conflicts with face tracking)"
    echo ""
fi

# Start frontend in new iTerm tab
echo "Starting frontend server..."
osascript <<EOF
tell application "iTerm"
    tell current window
        create tab with default profile
        tell current session
            write text "cd \"$SCRIPT_DIR/src/frontend/src\" && npm install && npm start"
        end tell
    end tell
end tell
EOF
echo "Frontend server launched in new tab"
echo ""

echo "=========================================="
echo "  All available services launched!"
echo "=========================================="
if [ $NUM_CAMERAS -ge 1 ]; then
    echo "  - Camera (Center Stage): http://localhost:5000"
fi
echo "  - 3D Builder (Frontend): http://localhost:3000"
echo "  - Audio Conversation: Running in separate tab"
if [ $NUM_CAMERAS -ge 2 ]; then
    echo "  - Hand Tracker: Running in separate tab"
fi
echo ""
echo "  Each service is running in its own iTerm tab."
echo "  Close individual tabs to stop specific services."
echo "=========================================="
echo ""

# Open browser windows after a delay
if [ $NUM_CAMERAS -ge 2 ]; then
    (sleep 5 && open http://localhost:3000/?app=hand_tracker && open http://localhost:5000/video_feed) &
elif [ $NUM_CAMERAS -eq 1 ]; then
    (sleep 5 && open http://localhost:3000 && open http://localhost:5000/video_feed) &
else
    (sleep 5 && open http://localhost:3000) &
fi

echo "Browser windows will open in 5 seconds..."
echo "Script complete. All services are running in separate tabs."
