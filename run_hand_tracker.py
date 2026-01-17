#!/usr/bin/env python3
"""
Run the hand tracking server for 3D block building.

Usage:
    python run_hand_tracker.py [camera_index]

Example:
    python run_hand_tracker.py 0  # Use default camera
    python run_hand_tracker.py 1  # Use external camera
"""

import asyncio
import sys
import os

# Add repo root to path
repo_root = os.path.abspath(os.path.dirname(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.hand_tracking.server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
