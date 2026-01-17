"""
Center Stage Camera System Test

Tests the face tracking and motor control without Flask server.
"""

import cv2
import time
import sys
import os

# Add to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera.facial_analysis.face_detector import FacialAnalyzer
from camera.tracking.face_tracker import FaceTracker
from hardware.stepper_motors.stepper_controller import StepperMotor

def test_center_stage():
    """Test the center stage system with live camera feed."""
    
    print("Initializing Center Stage System...")
    
    # Initialize components
    face_analyzer = FacialAnalyzer()
    face_tracker = FaceTracker(frame_width=640, frame_height=480, center_threshold=0.2)
    stepper_motor = StepperMotor()  # Auto-detects Arduino
    
    print(f"Motor simulation mode: {stepper_motor.simulation_mode}")
    
    # Open camera
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Press 'q' to quit, 't' to toggle tracking, 'c' to calibrate motor")
    
    tracking_enabled = True
    last_movement_time = 0
    movement_cooldown = 0.5
    
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                break
            
            # Detect faces
            annotated_frame, face_count = face_analyzer.annotate_frame(frame)
            face_info = face_analyzer.get_face_info(frame)
            
            # Track faces
            tracking_info = face_tracker.update(face_info)
            
            # Handle motor movement if tracking enabled
            if tracking_enabled and tracking_info['should_move']:
                current_time = time.time()
                if current_time - last_movement_time >= movement_cooldown:
                    steps = face_tracker.calculate_movement_steps(tracking_info, sensitivity=30)
                    
                    if steps > 0:
                        stepper_motor.step_forward(abs(steps))
                    elif steps < 0:
                        stepper_motor.step_backward(abs(steps))
                    
                    last_movement_time = current_time
                    print(f"Moving {tracking_info['direction']}: {abs(steps)} steps")
            
            # Add overlays
            if tracking_enabled:
                cv2.putText(annotated_frame, "TRACKING: ON", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(annotated_frame, "TRACKING: OFF", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.putText(annotated_frame, f"Motor Pos: {stepper_motor.get_position()}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(annotated_frame, f"Faces: {face_count}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display
            cv2.imshow('Center Stage Camera', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('t'):
                tracking_enabled = not tracking_enabled
                print(f"Tracking: {'ON' if tracking_enabled else 'OFF'}")
            elif key == ord('c'):
                pos = stepper_motor.get_position()
                if pos > 0:
                    stepper_motor.step_backward(abs(pos))
                elif pos < 0:
                    stepper_motor.step_forward(abs(pos))
                print("Motor calibrated to center")
    
    finally:
        print("\nCleaning up...")
        camera.release()
        cv2.destroyAllWindows()
        stepper_motor.cleanup()
        print("Done!")

if __name__ == '__main__':
    test_center_stage()
