#!/bin/bash

# Quick OpenCV fix for macOS
echo "Fixing OpenCV for macOS..."

source venv/bin/activate

# Remove all opencv variants
pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y 2>/dev/null

# Install headless version (most stable on macOS)
pip install opencv-python-headless==4.10.0.84

echo ""
echo "✓ OpenCV fixed. Now run: ./start.sh center-stage"
