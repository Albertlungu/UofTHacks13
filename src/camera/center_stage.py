import cv2
import time
import sys
import os

# Set OpenCV environment variables before importing anything else
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

from flask import Flask, Response, jsonify
from flask_cors import CORS

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facial_analysis.face_detector import FacialAnalyzer
from tracking.face_tracker import FaceTracker
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'hardware'))
from hardware.stepper_motors.stepper_controller import StepperMotor

app = Flask(__name__)
CORS(app)

# Global components
camera = None
face_analyzer = FacialAnalyzer()
face_tracker = FaceTracker(frame_width=640, frame_height=480, center_threshold=0.2)
stepper_motor = StepperMotor()  # Pan motor - auto-detects Arduino

# Tracking state
tracking_enabled = True
last_movement_time = 0
movement_cooldown = 0.5  # Minimum seconds between movements

def get_camera():
    global camera
    if camera is None:
        # Use different backends based on OS
        backends = [
            cv2.CAP_AVFOUNDATION,  # macOS
            cv2.CAP_ANY,           # Auto-detect
        ]
        
        for backend in backends:
            try:
                camera = cv2.VideoCapture(0, backend)
                if camera.isOpened():
                    print(f"Camera opened with backend: {backend}")
                    break
                camera.release()
                camera = None
            except Exception as e:
                print(f"Backend {backend} failed: {e}")
                continue
        
        if camera is None or not camera.isOpened():
            print("Error: Could not open camera with any backend")
            return None
        
        # Configure camera
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
        
        # Small delay to let camera initialize
        time.sleep(1)
        
        # Flush initial frames
        for _ in range(5):
            camera.read()
    
    return camera

def handle_face_tracking(face_info):
    """Process face tracking and control stepper motor."""
    global last_movement_time
    
    if not tracking_enabled:
        return
    
    # Update tracker with face information
    tracking_info = face_tracker.update(face_info)
    
    # Check if enough time has passed since last movement
    current_time = time.time()
    if current_time - last_movement_time < movement_cooldown:
        return
    
    # Calculate and execute movement if needed
    if tracking_info['should_move']:
        steps = face_tracker.calculate_movement_steps(tracking_info, sensitivity=30)
        
        if steps > 0:
            stepper_motor.step_forward(abs(steps))
        elif steps < 0:
            stepper_motor.step_backward(abs(steps))
        
        last_movement_time = current_time
        
        print(f"Face tracking: {tracking_info['direction']} by {abs(steps)} steps")

def generate_frames():
    camera = get_camera()
    if camera is None:
        print("Error: Camera not available")
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            print("Warning: Failed to read frame")
            time.sleep(0.1)
            continue
        
        try:
            # Apply facial analysis
            annotated_frame, face_count = face_analyzer.annotate_frame(frame)
            
            # Get face data for tracking
            face_info = face_analyzer.get_face_info(frame)
            
            # Handle face tracking and motor control
            handle_face_tracking(face_info)
            
            # Add tracking status overlay
            if tracking_enabled:
                cv2.putText(annotated_frame, "CENTER STAGE: ON", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error in frame generation: {e}")
            time.sleep(0.1)
            continue

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_data')
def face_data():
    """Get current face detection and tracking data."""
    camera = get_camera()
    success, frame = camera.read()
    
    if success:
        face_info = face_analyzer.get_face_info(frame)
        tracking_info = face_tracker.update(face_info)
        
        return jsonify({
            'faces': face_info,
            'count': len(face_info),
            'tracking': tracking_info,
            'motor_position': stepper_motor.get_position(),
            'tracking_enabled': tracking_enabled
        })
    
    return jsonify({'error': 'Could not read frame'}), 500

@app.route('/tracking/toggle', methods=['POST'])
def toggle_tracking():
    """Toggle center stage tracking on/off."""
    global tracking_enabled
    tracking_enabled = not tracking_enabled
    return jsonify({
        'tracking_enabled': tracking_enabled,
        'message': f"Center stage tracking {'enabled' if tracking_enabled else 'disabled'}"
    })

@app.route('/motor/calibrate', methods=['POST'])
def calibrate_motor():
    """Reset motor to center position."""
    current_pos = stepper_motor.get_position()
    if current_pos > 0:
        stepper_motor.step_backward(abs(current_pos))
    elif current_pos < 0:
        stepper_motor.step_forward(abs(current_pos))
    
    return jsonify({
        'message': 'Motor calibrated to center',
        'position': stepper_motor.get_position()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'tracking_enabled': tracking_enabled,
        'motor_position': stepper_motor.get_position()
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Cleanup and shutdown."""
    stepper_motor.cleanup()
    return jsonify({'message': 'Shutting down'})

if __name__ == '__main__':
    try:
        print("Starting Center Stage Camera System...")
        print("- Camera feed with facial recognition")
        print("- Automatic face tracking")
        print("- Stepper motor control")
        print(f"- Motor simulation mode: {stepper_motor.simulation_mode}")
        
        # Test camera before starting server
        print("\nTesting camera...")
        test_cam = get_camera()
        if test_cam is None:
            print("ERROR: Camera initialization failed!")
            print("Please check:")
            print("  1. Camera is connected")
            print("  2. No other app is using the camera")
            print("  3. Camera permissions are granted")
            exit(1)
        
        ret, frame = test_cam.read()
        if not ret:
            print("ERROR: Could not read from camera!")
            exit(1)
        
        print(f"✓ Camera working: {frame.shape}")
        print("\nStarting Flask server...")
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        stepper_motor.cleanup()
        if camera:
            camera.release()
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        stepper_motor.cleanup()
        if camera:
            camera.release()
