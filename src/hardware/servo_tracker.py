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
        
        # Servo angle limits
        self.pan_min = 0      # Left limit
        self.pan_max = 180    # Right limit
        self.pan_center = 90  # Center position
        
        # Current servo positions
        self.current_pan = 90
        
        # Smoothing for servo movement
        self.pan_smoothing = 0.5  # Increased for more responsive
        
        # Debug
        self.last_pan = 90
        self.update_count = 0
        
        print("âœ“ ServoTracker initialized")
    
    def connect(self) -> bool:
        """Connect to Arduino via serial"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            self.is_connected = True
            print(f"âœ“ Connected to {self.port} @ {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"âœ— Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("â— Disconnected from servo tracker")
    
    def start_tracking(self):
        """Start continuous tracking"""
        if not self.is_connected:
            print("âœ— Not connected to Arduino")
            return
        
        self.tracking_enabled = True
        print("âœ“ Tracking enabled")
    
    def stop_tracking(self):
        """Stop tracking and center servos"""
        self.tracking_enabled = False
        self.center_servos()
        print("â— Tracking disabled")
    
    def update_face_position(self, face_center_x: int, face_center_y: int, 
                        frame_width: int, frame_height: int):
        """Update servo position based on face X location (pan only)"""
        if not self.tracking_enabled or not self.is_connected:
            return
        
        self.update_count += 1
        
        # Calculate normalized X position (-1 to 1)
        norm_x = (face_center_x - frame_width / 2) / (frame_width / 2)
        norm_x = max(-1, min(1, norm_x))
        
        # Calculate target pan angle
        target_pan = self.pan_center + (norm_x * 90)
        target_pan = max(self.pan_min, min(self.pan_max, target_pan))
        
        # Apply smoothing
        self.current_pan = int(
            self.current_pan * (1 - self.pan_smoothing) + 
            target_pan * self.pan_smoothing
        )
        
        # DEBUG: Print every 10 updates
        if self.update_count % 10 == 0:
            print(f"SERVO DEBUG | Face X: {face_center_x:4d}/{frame_width} | "
                  f"Norm: {norm_x:6.2f} | Target: {target_pan:3.0f}Â° | "
                  f"Current: {self.current_pan:3d}Â° | Delta: {self.current_pan - self.last_pan:+3d}Â°")
        
        # Send to Arduino
        self._send_servo_command(self.current_pan)
        self.last_pan = self.current_pan
    
    def _send_servo_command(self, pan: int):
        """Send servo angle to Arduino via serial"""
        if not self.is_connected:
            return
        
        try:
            # Format: "PAN:90\n"
            command = f"PAN:{pan}\n"
            self.serial_conn.write(command.encode())
            # DEBUG: uncomment to see every command
            # print(f"  â†’ Sent: {command.strip()}")
        except Exception as e:
            print(f"âœ— Serial write error: {e}")
            self.is_connected = False
    
    def center_servos(self):
        """Center servo to neutral position"""
        self.current_pan = self.pan_center
        self._send_servo_command(self.pan_center)
        print(f"â— Servo centered to 90Â°")
        
    def set_servo_limits(self, pan_min: int, pan_max: int):
        """Adjust servo angle limits"""
        self.pan_min = pan_min
        self.pan_max = pan_max
        print(f"âœ“ Servo limits updated: Pan({pan_min}-{pan_max})")
    
    def set_smoothing(self, pan_smoothing: float):
        """Adjust tracking smoothness (0.0-1.0, higher = more responsive)"""
        self.pan_smoothing = 0.1
        print(f"âœ“ Smoothing updated: {self.pan_smoothing}")