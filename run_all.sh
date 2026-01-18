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
    echo "🛑 Shutting down..."
    if [ ! -z "$HAND_TRACKER_PID" ]; then
        kill $HAND_TRACKER_PID 2>/dev/null || true
    fi
    if [ ! -z "$MAIN_PID" ]; then
        kill $MAIN_PID 2>/dev/null || true
    fi
    echo "✓ Cleanup complete"
    exit 0
}

# Set up trap to catch Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start hand tracker in background
echo "🖐️  Starting hand tracker..."
python run_hand_tracker.py 1 &
HAND_TRACKER_PID=$!
echo "✓ Hand tracker started (PID: $HAND_TRACKER_PID)"
echo ""

# Wait a moment for hand tracker to initialize
sleep 2


# Start main application
echo "🚀 Starting main application..."
python main.py &
MAIN_PID=$!
echo "✓ Main application started (PID: $MAIN_PID)"
echo ""


echo "Starting localhost"
cd src/frontend
npm install
npm start

cd ../../

open http://localhost:3000/?app=hand_tracker

echo "=========================================="
echo "  All services running!"
echo "  Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Wait for both processes
wait $HAND_TRACKER_PID $MAIN_PID
