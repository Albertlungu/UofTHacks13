import cv2
from flask import Flask, Response, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import numpy as np
import threading

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from facial_analysis.face_detector import FacialAnalyzer

app = Flask(__name__)
CORS(app)

# Global speech detection state
is_speaking = False
current_volume = 0.0  # NEW: Track current volume
speech_lock = threading.Lock()

# Speech detection using microphone
class SpeechDetector:
    def __init__(self, threshold=5, chunk_size=1024):  # Even lower threshold
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
            
            # Print available audio devices for debugging
            print("\n=== Available Audio Devices ===")
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                print(f"Device {i}: {info['name']} (inputs: {info['maxInputChannels']})")
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.audio_available = True
            print(f"\n✅ Speech detection started! Threshold: {self.threshold}")
            print("🎤 Start speaking to test...")
            print("📊 Volume will be displayed live...\n")
            
            while self.is_running:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = float(np.abs(audio_data).mean())
                    
                    with speech_lock:
                        current_volume = volume
                        is_speaking = bool(volume > self.threshold)
                    
                    # Print EVERY volume reading with visual indicator
                    status = "🔴 SPEAKING" if volume > self.threshold else "⚪ silent"
                    bar = "█" * int(volume / 2)  # Visual bar
                    print(f"{status} | Vol: {volume:6.1f} | {bar}", end='\r')
                        
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except ImportError:
            print("❌ PyAudio not installed. Install with: pip install pyaudio")
            print("Speech detection disabled - using manual button instead")
        except Exception as e:
            print(f"❌ Could not initialize audio: {e}")
            print("Speech detection disabled - using manual button instead")

speech_detector = SpeechDetector()

# Serve avatar images
@app.route('/assets/avatar/<filename>')
def avatar_images(filename):
    current_file = os.path.abspath(__file__)
    camera_folder = os.path.dirname(current_file)
    camera_parent = os.path.dirname(camera_folder)
    src_folder = os.path.dirname(camera_parent)
    root_folder = os.path.dirname(src_folder)
    
    assets_path = os.path.join(root_folder, 'assets', 'avatar')
    
    if not os.path.exists(os.path.join(assets_path, filename)):
        print(f"❌ File does not exist: {filename}")
        return f"File {filename} not found", 404
    
    return send_from_directory(assets_path, filename)

camera = None
face_analyzer = FacialAnalyzer()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera

def generate_frames():
    camera = get_camera()
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            annotated_frame, face_count = face_analyzer.annotate_frame(frame)
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_data')
def face_data():
    camera = get_camera()
    success, frame = camera.read()
    if success:
        face_info = face_analyzer.get_face_info(frame)
        return jsonify({
            'faces': face_info,
            'count': len(face_info)
        })
    return jsonify({'error': 'Could not read frame'}), 500

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

@app.route('/generate_response', methods=['POST'])
def generate_response():
    return jsonify({
        'status': 'not_implemented',
        'message': 'Response generation disabled to save TTS credits'
    }), 501

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Camera + Avatar Server")
    print("="*50 + "\n")
    
    speech_detector.start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        speech_detector.stop()