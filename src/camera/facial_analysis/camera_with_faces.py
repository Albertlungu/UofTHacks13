import cv2
from flask import Flask, Response, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import numpy as np
import threading
import time
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from facial_analysis.face_detector import FacialAnalyzer

app = Flask(__name__)
CORS(app)

# Global speech detection state
is_speaking = False
current_volume = 0.0
speech_lock = threading.Lock()

# Global camera state - OPTIMIZED
camera = None
latest_frame = None
frame_lock = threading.Lock()
camera_thread = None
camera_running = False

# Frame buffer for smooth streaming
frame_buffer = deque(maxlen=3)
buffer_lock = threading.Lock()

class CameraThread(threading.Thread):
    """HIGH PERFORMANCE camera thread with frame buffering"""
    def __init__(self):
        super().__init__(daemon=True)
        self.face_analyzer = FacialAnalyzer()
        self.frame_count = 0
        
    def run(self):
        global camera, latest_frame, camera_running, frame_buffer
        
        # Try multiple camera backends for best performance
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            camera = cv2.VideoCapture(0, backend)
            if camera.isOpened():
                print(f"✓ Camera opened with backend: {backend}")
                break
        
        if not camera.isOpened():
            print("✗ Failed to open camera")
            return
        
        # OPTIMIZED settings for speed and quality
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera.set(cv2.CAP_PROP_FPS, 60)  # Request higher FPS
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
        
        # Enhanced image quality
        camera.set(cv2.CAP_PROP_BRIGHTNESS, 130)
        camera.set(cv2.CAP_PROP_CONTRAST, 160)  # Increased from 140
        camera.set(cv2.CAP_PROP_SATURATION, 120)
        camera.set(cv2.CAP_PROP_SHARPNESS, 255)  # Max sharpness
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        
        # Verify actual settings
        actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(camera.get(cv2.CAP_PROP_FPS))
        
        print(f"✓ Camera: {actual_width}x{actual_height} @ {actual_fps}fps")
        
        # Warm up camera
        for _ in range(10):
            camera.read()
        
        last_time = time.time()
        fps_counter = 0
        
        while camera_running:
            success, frame = camera.read()
            
            if success:
                self.frame_count += 1
                
                # Store latest frame with minimal processing
                with frame_lock:
                    latest_frame = frame.copy()
                
                # Add to buffer for streaming
                with buffer_lock:
                    frame_buffer.append(frame.copy())
                
                # FPS monitoring
                fps_counter += 1
                if time.time() - last_time > 5.0:
                    fps = fps_counter / (time.time() - last_time)
                    print(f"Camera FPS: {fps:.1f}")
                    last_time = time.time()
                    fps_counter = 0
                    
            else:
                print("✗ Frame read failed")
                time.sleep(0.01)
            
            # No sleep - run as fast as possible
        
        camera.release()
        print("● Camera released")

def start_camera_thread():
    global camera_thread, camera_running
    camera_running = True
    camera_thread = CameraThread()
    camera_thread.start()

def stop_camera_thread():
    global camera_running
    camera_running = False
    if camera_thread:
        camera_thread.join(timeout=2.0)

class SpeechDetector:
    def __init__(self, threshold=5, chunk_size=1024):
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.is_running = False
        self.thread = None
        self.audio_available = False
        
    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._detect_speech, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
    
    def _detect_speech(self):
        global is_speaking, current_volume
        
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.audio_available = True
            print(f"✓ Speech detection active")
            
            while self.is_running:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = float(np.abs(audio_data).mean())
                    
                    with speech_lock:
                        current_volume = volume
                        is_speaking = bool(volume > self.threshold)
                        
                except Exception as e:
                    print(f"Audio error: {e}")
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except ImportError:
            print("✗ PyAudio not available - using manual mode")
        except Exception as e:
            print(f"✗ Audio initialization failed: {e}")

speech_detector = SpeechDetector()
face_analyzer = FacialAnalyzer()

def get_assets_path():
    current_file = os.path.abspath(__file__)
    camera_folder = os.path.dirname(current_file)
    camera_parent = os.path.dirname(camera_folder)
    src_folder = os.path.dirname(camera_parent)
    root_folder = os.path.dirname(src_folder)
    return os.path.join(root_folder, 'assets')

@app.route('/assets/avatar/<filename>')
def avatar_images(filename):
    assets_path = get_assets_path()
    avatar_path = os.path.join(assets_path, 'avatar')
    
    if not os.path.exists(os.path.join(avatar_path, filename)):
        return f"File {filename} not found", 404
    
    return send_from_directory(avatar_path, filename)

@app.route('/assets/models/<filename>')
def model_files(filename):
    assets_path = get_assets_path()
    models_path = os.path.join(assets_path, 'models')
    
    file_path = os.path.join(models_path, filename)
    
    if not os.path.exists(file_path):
        return f"Model file {filename} not found", 404
    
    if filename.endswith('.glb'):
        mimetype = 'model/gltf-binary'
    elif filename.endswith('.gltf'):
        mimetype = 'model/gltf+json'
    else:
        mimetype = 'application/octet-stream'
    
    return send_from_directory(models_path, filename, mimetype=mimetype)

def generate_frames():
    """OPTIMIZED frame generator - minimal processing"""
    last_frame_time = time.time()
    target_interval = 1.0 / 30.0  # 30 FPS target
    
    while True:
        # Get frame from buffer
        with buffer_lock:
            if len(frame_buffer) == 0:
                time.sleep(0.01)
                continue
            frame = frame_buffer[-1].copy()
        
        # Flip frame horizontally (mirror effect - natural for camera feed)
        frame = cv2.flip(frame, 1)
        
        # Face detection (lightweight annotations only)
        annotated_frame, face_count = face_analyzer.annotate_frame(frame)
        
        # HIGH QUALITY JPEG encoding (no sharpening - causes artifacts)
        encode_param = [
            int(cv2.IMWRITE_JPEG_QUALITY), 95,
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1
        ]
        ret, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
        
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
               b'\r\n' + frame_bytes + b'\r\n')
        
        # Rate limiting to prevent overwhelming client
        elapsed = time.time() - last_frame_time
        if elapsed < target_interval:
            time.sleep(target_interval - elapsed)
        last_frame_time = time.time()

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

@app.route('/face_data')
def face_data():
    """Fast face data endpoint"""
    with frame_lock:
        if latest_frame is None:
            return jsonify({'error': 'No frame available'}), 503
        frame = latest_frame.copy()
    
    face_info = face_analyzer.get_face_info(frame)
    return jsonify({
        'faces': face_info,
        'count': len(face_info)
    })

@app.route('/speaking_status')
def speaking_status():
    with speech_lock:
        speaking_state = bool(is_speaking)
        vol = float(current_volume)
    
    return jsonify({
        'is_speaking': speaking_state,
        'audio_available': speech_detector.audio_available,
        'current_volume': vol,
        'threshold': speech_detector.threshold
    })

@app.route('/toggle_speaking', methods=['POST'])
def toggle_speaking():
    global is_speaking
    with speech_lock:
        is_speaking = not is_speaking
    return jsonify({'is_speaking': bool(is_speaking)})

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    print("\n" + "="*50)
    print("● GOONVENGERS AI Server - High Performance Mode")
    print("="*50 + "\n")
    
    assets_path = get_assets_path()
    models_path = os.path.join(assets_path, 'models')
    avatar_glb = os.path.join(models_path, 'chibi.glb')
    
    if os.path.exists(avatar_glb):
        print(f"✓ Found chibi.glb")
    else:
        print(f"⚠ chibi.glb not found")
    
    print()
    
    start_camera_thread()
    time.sleep(2)  # Allow camera to stabilize
    
    speech_detector.start()
    
    try:
        # Production mode - no debug, no reloader
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        print("\n● Shutting down...")
        speech_detector.stop()
        stop_camera_thread()
        print("✓ Complete")