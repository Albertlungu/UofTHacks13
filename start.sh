#!/bin/bash

# Center Stage Camera System - Start Script
# Usage: ./start.sh [mode]
# Modes: basic, faces, center-stage, test

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}  Center Stage Camera System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Set OpenCV environment variables for macOS stability
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
export OPENCV_VIDEOIO_DEBUG=0
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Check if dependencies are installed
if ! python -c "import cv2" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Check if frontend dependencies are installed
if [ ! -d "src/frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing...${NC}"
    cd src/frontend
    npm install
    cd ../..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

# Determine mode
MODE=${1:-center-stage}

echo ""
echo -e "${BLUE}Starting in mode: ${GREEN}${MODE}${NC}"
echo ""

case $MODE in
    basic)
        echo -e "${BLUE}Mode: Basic Camera Feed${NC}"
        echo -e "  - Simple camera streaming"
        echo -e "  - No face detection"
        echo -e "  - No motor control"
        echo ""
        
        # Start backend in background
        echo -e "${BLUE}Starting backend...${NC}"
        python src/camera/feed/camera_stream.py &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 3
        
        # Start frontend
        echo -e "${BLUE}Starting frontend...${NC}"
        cd src/frontend
        npm start &
        FRONTEND_PID=$!
        cd ../..
        
        echo ""
        echo -e "${GREEN}✓ System started!${NC}"
        echo -e "  Backend PID: ${BACKEND_PID}"
        echo -e "  Frontend PID: ${FRONTEND_PID}"
        echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
        echo -e "  Backend: ${BLUE}http://localhost:5000${NC}"
        ;;
        
    faces)
        echo -e "${BLUE}Mode: Camera with Face Detection${NC}"
        echo -e "  - Camera streaming"
        echo -e "  - Face detection boxes"
        echo -e "  - No motor control"
        echo ""
        
        # Start backend in background
        echo -e "${BLUE}Starting backend with face detection...${NC}"
        python src/camera/facial_analysis/camera_with_faces.py &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 3
        
        # Start frontend
        echo -e "${BLUE}Starting frontend...${NC}"
        cd src/frontend
        npm start &
        FRONTEND_PID=$!
        cd ../..
        
        echo ""
        echo -e "${GREEN}✓ System started!${NC}"
        echo -e "  Backend PID: ${BACKEND_PID}"
        echo -e "  Frontend PID: ${FRONTEND_PID}"
        echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
        echo -e "  Backend: ${BLUE}http://localhost:5000${NC}"
        ;;
        
    center-stage)
        echo -e "${BLUE}Mode: Center Stage (Auto-Tracking)${NC}"
        echo -e "  - Camera streaming"
        echo -e "  - Face detection"
        echo -e "  - Automatic face tracking"
        echo -e "  - Motor control (Arduino required)"
        echo ""
        
        # Check for Arduino
        echo -e "${YELLOW}Checking for Arduino...${NC}"
        if ls /dev/tty.usbmodem* 1> /dev/null 2>&1 || ls /dev/ttyACM* 1> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Arduino port detected${NC}"
        else
            echo -e "${YELLOW}⚠ No Arduino detected - will run in simulation mode${NC}"
        fi
        echo ""
        
        # Test camera first
        echo -e "${BLUE}Testing camera...${NC}"
        if python test_camera.py 2>/dev/null; then
            echo -e "${GREEN}✓ Camera test passed${NC}"
        else
            echo -e "${RED}✗ Camera test failed${NC}"
            echo -e "${YELLOW}Trying to fix OpenCV installation...${NC}"
            pip uninstall opencv-python opencv-contrib-python -y 2>/dev/null
            pip install opencv-python-headless==4.10.0.84
            echo -e "${YELLOW}Please restart: ./start.sh center-stage${NC}"
            exit 1
        fi
        echo ""
        
        # Start backend in background
        echo -e "${BLUE}Starting center stage backend...${NC}"
        python src/camera/facial_analysis/camera_with_faces.py &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 3
        
        # Start frontend
        echo -e "${BLUE}Starting frontend...${NC}"
        cd src/frontend
        npm start &
        FRONTEND_PID=$!
        cd ../..
        
        echo ""
        echo -e "${GREEN}✓ System started!${NC}"
        echo -e "  Backend PID: ${BACKEND_PID}"
        echo -e "  Frontend PID: ${FRONTEND_PID}"
        echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
        echo -e "  Backend: ${BLUE}http://localhost:5000${NC}"
        echo -e "  API Endpoints:"
        echo -e "    - GET  /video_feed    - Video stream"
        echo -e "    - GET  /face_data     - Face tracking data"
        echo -e "    - POST /tracking/toggle - Toggle tracking"
        echo -e "    - POST /motor/calibrate - Calibrate motor"
        ;;
        
    test)
        echo -e "${BLUE}Mode: Standalone Test (No Frontend)${NC}"
        echo -e "  - OpenCV window display"
        echo -e "  - Face detection"
        echo -e "  - Face tracking"
        echo -e "  - Motor control"
        echo ""
        echo -e "${YELLOW}Controls:${NC}"
        echo -e "  q - Quit"
        echo -e "  t - Toggle tracking on/off"
        echo -e "  c - Calibrate motor to center"
        echo ""
        
        # Run test directly (blocking)
        python tests/test_center_stage.py
        exit 0
        ;;
        
    *)
        echo -e "${RED}Unknown mode: ${MODE}${NC}"
        echo ""
        echo "Available modes:"
        echo "  basic         - Basic camera feed only"
        echo "  faces         - Camera with face detection"
        echo "  center-stage  - Full center stage with tracking (default)"
        echo "  test          - Standalone test (no frontend)"
        echo ""
        echo "Usage: ./start.sh [mode]"
        exit 1
        ;;
esac

# Wait for user to stop
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Trap Ctrl+C to cleanup
trap 'echo ""; echo -e "${YELLOW}Stopping services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e "${GREEN}✓ Stopped${NC}"; exit 0' INT

# Keep script running
wait
