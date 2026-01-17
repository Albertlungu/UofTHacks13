import cv2
from flask import Flask, Response, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facial_analysis.face_detector import FacialAnalyzer

app = Flask(__name__)
CORS(app)

camera = None
face_analyzer = FacialAnalyzer()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return camera

def generate_frames():
    camera = get_camera()
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Apply facial analysis
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
    """Get current face detection data"""
    camera = get_camera()
    success, frame = camera.read()
    
    if success:
        face_info = face_analyzer.get_face_info(frame)
        return jsonify({
            'faces': face_info,
            'count': len(face_info)
        })
    
    return jsonify({'error': 'Could not read frame'}), 500

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
