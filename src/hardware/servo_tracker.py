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
        self.target_pan = 90
        
        # IMPROVED: Smoothing and deadzone
        self.pan_smoothing = 0.15  # Lower = smoother (0.1-0.3 recommended)
        self.deadzone = 15  # Degrees - don't move if within this range of target
        
        # Debug
        self.last_pan = 90
        self.update_count = 0
        
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
        print("✓ Tracking enabled")
    
    def stop_tracking(self):
        """Stop tracking and center servos"""
        self.tracking_enabled = False
        self.center_servos()
        print("● Tracking disabled")
    
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
        self.target_pan = self.pan_center + (norm_x * 90)
        self.target_pan = max(self.pan_min, min(self.pan_max, self.target_pan))
        
        # Apply deadzone - only move if target is far enough from current
        pan_diff = abs(self.target_pan - self.current_pan)
        
        if pan_diff > self.deadzone:
            # Apply smoothing
            self.current_pan = (
                self.current_pan * (1 - self.pan_smoothing) + 
                self.target_pan * self.pan_smoothing
            )
            
            # Send to Arduino
            pan_int = int(self.current_pan)
            self._send_servo_command(pan_int)
            
            # DEBUG: Print every 10 updates
            if self.update_count % 10 == 0:
                print(f"SERVO | Face X: {face_center_x:4d}/{frame_width} | "
                      f"Norm: {norm_x:6.2f} | Target: {self.target_pan:3.0f}° | "
                      f"Current: {pan_int:3d}° | Diff: {pan_diff:5.1f}° | "
                      f"{'MOVING' if pan_diff > self.deadzone else 'SETTLED'}")
            
            self.last_pan = pan_int
        else:
            # Within deadzone - settled on target
            if self.update_count % 50 == 0:
                print(f"SERVO | SETTLED at {int(self.current_pan)}° (target: {self.target_pan:.0f}°)")
    
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
        self.target_pan = self.pan_center
        self._send_servo_command(self.pan_center)
        print(f"● Servo centered to 90°")
        
    def set_servo_limits(self, pan_min: int, pan_max: int):
        """Adjust servo angle limits"""
        self.pan_min = pan_min
        self.pan_max = pan_max
        print(f"✓ Servo limits updated: Pan({pan_min}-{pan_max})")
    
    def set_smoothing(self, pan_smoothing: float):
        """Adjust tracking smoothness (0.0-1.0, higher = more responsive)"""
        self.pan_smoothing = max(0.05, min(0.5, pan_smoothing))
        print(f"✓ Smoothing updated: {self.pan_smoothing}")
    
    def set_deadzone(self, deadzone: float):
        """Adjust deadzone in degrees (how close to settle before stopping)"""
        self.deadzone = max(5, min(30, deadzone))
        print(f"✓ Deadzone updated: {self.deadzone}°")