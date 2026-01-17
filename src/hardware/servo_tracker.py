"""
Servo Motor Face Tracking Controller
Connects to Arduino Uno R4 via serial
Tracks face position and adjusts pan/tilt servos
"""

import serial
import json
import time
import threading
from typing import Optional, Tuple

class ServoTracker:
    def __init__(self, port: str = 'COM12', baudrate: int = 115200):
        """
        Initialize servo tracker connected to Arduino Uno R4
        
        Args:
            port: Serial port (e.g., 'COM12' on Windows, '/dev/ttyACM0' on Linux)
            baudrate: Serial communication speed (115200 for Arduino R4)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.tracking_enabled = False
        
        # Servo angle limits (adjust based on your servo)
        self.pan_min = 0      # Left limit
        self.pan_max = 180    # Right limit
        self.pan_center = 90  # Center position
        
        self.tilt_min = 45    # Down limit
        self.tilt_max = 135   # Up limit
        self.tilt_center = 90 # Center position
        
        # Current servo positions
        self.current_pan = 90
        self.current_tilt = 90
        
        # Smoothing for servo movement
        self.pan_smoothing = 0.3
        self.tilt_smoothing = 0.3
        
        # Threading
        self.update_thread = None
        self.running = False
        
        print("✓ ServoTracker initialized")
    
    def connect(self) -> bool:
        """Connect to Arduino via serial"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            self.is_connected = True
            print(f"✓ Connected to {self.port} @ {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("● Disconnected from servo tracker")
    
    def start_tracking(self):
        """Start continuous tracking"""
        if not self.is_connected:
            print("✗ Not connected to Arduino")
            return
        
        self.tracking_enabled = True
        self.running = True
        print("✓ Tracking enabled")
    
    def stop_tracking(self):
        """Stop tracking and center servos"""
        self.tracking_enabled = False
        self.center_servos()
        print("● Tracking disabled")
    
    def update_face_position(self, face_center_x: int, face_center_y: int, 
                        frame_width: int, frame_height: int):
        """
        Update servo position based on face X location (pan only)
        
        Args:
            face_center_x: X coordinate of face center (pixels)
            face_center_y: Y coordinate of face center (pixels)
            frame_width: Camera frame width (pixels)
            frame_height: Camera frame height (pixels)
        """
        if not self.tracking_enabled or not self.is_connected:
            return
        
        # Calculate normalized X position (-1 to 1)
        norm_x = (face_center_x - frame_width / 2) / (frame_width / 2)
        
        # Clamp to -1 to 1
        norm_x = max(-1, min(1, norm_x))
        
        # Calculate target servo angle
        # Pan: move left/right based on X position
        target_pan = self.pan_center + (norm_x * (self.pan_max - self.pan_center) / 2)
        
        # Clamp to servo limits
        target_pan = max(self.pan_min, min(self.pan_max, target_pan))
        
        # Apply smoothing (exponential moving average)
        self.current_pan = int(
            self.current_pan * (1 - self.pan_smoothing) + 
            target_pan * self.pan_smoothing
        )
        
        # Send to Arduino (pan only)
        self._send_servo_command(self.current_pan)
    
    def _send_servo_command(self, pan: int):
        """Send servo angle to Arduino via serial"""
        if not self.is_connected:
            return
        
        try:
            # Format: "PAN:90\n"
            command = f"PAN:{pan}\n"
            self.serial_conn.write(command.encode())
        except Exception as e:
            print(f"✗ Serial write error: {e}")
            self.is_connected = False
    
    def center_servos(self):
        """Center servo to neutral position"""
        self.current_pan = self.pan_center
        self._send_servo_command(self.pan_center)
        print(f"● Servo centered")
        
    def set_servo_limits(self, pan_min: int, pan_max: int, 
                        tilt_min: int, tilt_max: int):
        """Adjust servo angle limits"""
        self.pan_min = pan_min
        self.pan_max = pan_max
        self.tilt_min = tilt_min
        self.tilt_max = tilt_max
        print(f"✓ Servo limits updated: Pan({pan_min}-{pan_max}), Tilt({tilt_min}-{tilt_max})")
    
    def set_smoothing(self, pan_smoothing: float, tilt_smoothing: float):
        """Adjust tracking smoothness (0.0-1.0, higher = smoother)"""
        self.pan_smoothing = max(0, min(1, pan_smoothing))
        self.tilt_smoothing = max(0, min(1, tilt_smoothing))
        print(f"✓ Smoothing updated: Pan({self.pan_smoothing}), Tilt({self.tilt_smoothing})")