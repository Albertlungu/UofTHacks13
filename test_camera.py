#!/usr/bin/env python3
"""
Simple camera test to diagnose segfault issues
"""

import sys
print(f"Python version: {sys.version}")

try:
    import cv2
    print(f"OpenCV version: {cv2.__version__}")
    print("✓ OpenCV imported successfully")
except Exception as e:
    print(f"✗ Error importing OpenCV: {e}")
    sys.exit(1)

try:
    print("\nTrying to open camera...")
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("✗ Could not open camera")
        print("\nPossible fixes:")
        print("1. Close other apps using the camera")
        print("2. Grant camera permissions in System Preferences")
        print("3. Try a different camera index: cv2.VideoCapture(1)")
        sys.exit(1)
    
    print("✓ Camera opened successfully")
    
    # Try to read a frame
    print("\nReading frame...")
    ret, frame = camera.read()
    
    if not ret:
        print("✗ Could not read frame")
        camera.release()
        sys.exit(1)
    
    print(f"✓ Frame read successfully: {frame.shape}")
    
    # Test face detection
    print("\nTesting face detection...")
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    print(f"✓ Face detection working. Found {len(faces)} faces")
    
    camera.release()
    print("\n✅ All tests passed! Your system is ready.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
