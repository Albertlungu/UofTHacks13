#!/bin/bash

# shadow Setup Script
# This script sets up the development environment for the shadow AI companion

set -e  # Exit on error

echo "=========================================="
echo "shadow Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Python >= 3.9
required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

# Create logs directory
echo ""
echo "Creating logs directory..."
mkdir -p logs

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt --no-cache-dir

# Check for PyAudio issues on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "macOS detected - checking PyAudio installation..."
    if ! python -c "import pyaudio" 2>/dev/null; then
        echo "PyAudio installation failed. Installing portaudio..."
        if command -v brew &> /dev/null; then
            brew install portaudio
            pip install pyaudio
        else
            echo "Warning: Homebrew not found. Please install portaudio manually:"
            echo "  brew install portaudio"
            echo "  pip install pyaudio"
        fi
    fi
fi

# Download Whisper model
echo ""
echo "Downloading Whisper model (this may take a few minutes)..."
python3 -c "from faster_whisper import WhisperModel; model = WhisperModel('base', device='cpu', compute_type='int8'); print('Whisper model downloaded successfully')"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys"
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v || echo "Warning: Some tests failed. This is normal if audio devices aren't connected."

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To run the audio demo:"
echo "  1. Connect your AirPods"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run: python -m src.audio.demo"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v"
echo ""
