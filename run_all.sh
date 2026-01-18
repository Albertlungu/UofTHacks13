#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "  GOONVENGERS Setup & Launcher"
echo "=========================================="
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Virtual environment directory
VENV_DIR="venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
    echo ""
else
    echo "✓ Virtual environment already exists"
    echo ""
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✓ Virtual environment activated"
echo ""

# Install/upgrade requirements
echo "📥 Installing requirements..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Requirements installed"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    if [ ! -z "$CAMERA_PID" ]; then
        echo "  - Stopping camera system..."
        kill $CAMERA_PID 2>/dev/null || true
    fi
    if [ ! -z "$AUDIO_PID" ]; then
        echo "  - Stopping audio conversation..."
        kill $AUDIO_PID 2>/dev/null || true
    fi
    if [ ! -z "$HAND_TRACKER_PID" ]; then
        echo "  - Stopping hand tracker..."
        kill $HAND_TRACKER_PID 2>/dev/null || true
    fi
    # Kill any remaining npm/node processes from frontend
    pkill -f "react-scripts start" 2>/dev/null || true
    echo "✓ Cleanup complete"
    exit 0
}

# Set up trap to catch Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start camera system in background
echo "📹 Starting camera system (Center Stage)..."
python src/camera/center_stage.py &
CAMERA_PID=$!
echo "✓ Camera system started (PID: $CAMERA_PID)"
echo "  - Flask server on http://localhost:5000"
echo "  - Video feed at http://localhost:5000/video_feed"
echo ""

# Wait a moment for camera to initialize
sleep 2

# Start audio conversation system in background
echo "🎤 Starting audio conversation system..."
python main.py &
AUDIO_PID=$!
echo "✓ Audio system started (PID: $AUDIO_PID)"
echo "  - Voice conversation active in terminal"
echo ""

# Wait a moment for audio to initialize
sleep 2

# Start hand tracker in background
echo "🖐️  Starting hand tracker (3D builder backend)..."
python run_hand_tracker.py 1 &
HAND_TRACKER_PID=$!
echo "✓ Hand tracker started (PID: $HAND_TRACKER_PID)"
echo ""

# Wait a moment for hand tracker to initialize
sleep 2

# Start frontend (this runs in foreground and keeps script alive)
echo "🌐 Starting frontend server..."
cd src/frontend
npm install
echo ""
echo "=========================================="
echo "  All services running!"
echo "=========================================="
echo "  - Camera (Center Stage): http://localhost:5000"
echo "  - 3D Builder (Frontend): http://localhost:3000"
echo "  - Audio Conversation: Running in terminal background"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Open browser windows before starting frontend
(sleep 3 && open http://localhost:3000/?app=hand_tracker && open http://localhost:5000/video_feed) &

# Start frontend in foreground (keeps script alive)
npm start

cd ../../
