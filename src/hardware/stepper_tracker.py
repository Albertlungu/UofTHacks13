"""
Stepper Motor Face Tracking Controller
Connects to Arduino Uno R4 via serial
Tracks face position and adjusts stepper motor pan
"""

import serial
import json
import time
import threading
from typing import Optional, Tuple

class StepperTracker:  # Changed class name
    def __init__(self, port: str = 'COM12', baudrate: int = 115200):
        """
        Initialize stepper motor tracker connected to Arduino Uno R4
        
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
        self.pan_min = 0
        self.pan_max = 180
        self.pan_center = 90
        
        # Current servo positions
        self.current_pan = 90
        
        # Smoothing for servo movement
        self.pan_smoothing = 0.3
        
        # ✅ ADD THESE - Command throttling for stepper
        self.last_command_time = 0
        self.min_command_interval = 0.5  # Minimum 500ms between commands
        self.movement_threshold = 3  # Only move if angle changes by 3+ degrees
        
        # Debug
        self.last_pan = 90
        self.update_count = 0
        
        print("✓ StepperTracker initialized")
    
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
        
        import time  # ✅ ADD THIS
        
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
        
        # ✅ ADD THROTTLING - Only send if enough time passed AND significant movement
        current_time = time.time()
        angle_delta = abs(self.current_pan - self.last_pan)
        time_since_last = current_time - self.last_command_time
        
        if time_since_last >= self.min_command_interval and angle_delta >= self.movement_threshold:
            # DEBUG: Print every update that actually sends
            print(f"SERVO UPDATE | Face X: {face_center_x:4d}/{frame_width} | "
                f"Norm: {norm_x:6.2f} | Target: {target_pan:3.0f}° | "
                f"Current: {self.current_pan:3d}° | Delta: {angle_delta:+3d}° | "
                f"Sending command...")
            
            # Send to Arduino
            self._send_servo_command(self.current_pan)
            self.last_pan = self.current_pan
            self.last_command_time = current_time
        else:
            # Skip this update
            if self.update_count % 30 == 0:  # Print occasionally why we're skipping
                print(f"SKIP | Time since last: {time_since_last:.2f}s | Angle delta: {angle_delta}° (need {self.movement_threshold}°)")
    
    def _send_servo_command(self, pan: int):
        """Send servo angle to Arduino via serial"""
        if not self.is_connected:
            print("DEBUG: Not connected, skipping command")  # ✅ ADD THIS
            return
        
        try:
            # Format: "PAN:90\n"
            command = f"PAN:{pan}\n"
            self.serial_conn.write(command.encode())
            # DEBUG: uncomment to see every command
            print(f"  → Sent: {command.strip()}")  # ✅ UNCOMMENT THIS LINE
        except Exception as e:
            print(f"✗ Serial write error: {e}")
            self.is_connected = False
    
    def center_servos(self):
        """Center servo to neutral position"""
        self.current_pan = self.pan_center
        self._send_servo_command(self.pan_center)
        print(f"● Servo centered to 90°")
        
    def set_servo_limits(self, pan_min: int, pan_max: int):
        """Adjust servo angle limits"""
        self.pan_min = pan_min
        self.pan_max = pan_max
        print(f"✓ Servo limits updated: Pan({pan_min}-{pan_max})")
    
    def set_smoothing(self, pan_smoothing: float):
        """Adjust tracking smoothness (0.0-1.0, higher = more responsive)"""
        self.pan_smoothing = 0.1
        print(f"✓ Smoothing updated: {self.pan_smoothing}")