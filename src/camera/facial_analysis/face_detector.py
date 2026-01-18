import cv2
import numpy as np
import time

class FacialAnalyzer:
    def __init__(self):
        """Initialize face detection - FAST and STABLE"""
        self.use_mediapipe = False
        self.face_detector = None
        
        # Try MediaPipe first
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.6
            )
            self.use_mediapipe = True
            print("✓ Using MediaPipe face detection")
        except (ImportError, AttributeError):
            print("⚠ MediaPipe not available, using OpenCV cascades")
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            print("✓ Using OpenCV Haar cascades")
        
        # Heavy smoothing for stability
        self.last_face = None
        self.smoothing = 0.85  # INCREASED: 0.85 = very smooth, stable
        self.frame_count = 0
        
        print("✓ Face detector initialized")
    
    def detect_faces_mediapipe(self, frame):
        """Detect faces using MediaPipe"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = frame.shape
        
        results = self.face_detector.process(rgb_frame)
        faces = []
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                box_w = int(bbox.width * w)
                box_h = int(bbox.height * h)
                
                x = max(0, x)
                y = max(0, y)
                box_w = min(box_w, w - x)
                box_h = min(box_h, h - y)
                
                confidence = detection.score[0]
                faces.append((x, y, box_w, box_h, confidence))
        
        return faces
    
    def detect_faces_cascade(self, frame):
        """Simple frontal-only detection for speed"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(80, 80),
            maxSize=(350, 350),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert to 5-tuple format
        return [(x, y, w, h, 0.9) for x, y, w, h in faces]
    
    def detect_faces(self, frame):
        """Detect faces with heavy smoothing"""
        self.frame_count += 1
        
        # Get detections
        if self.use_mediapipe:
            faces = self.detect_faces_mediapipe(frame)
        else:
            faces = self.detect_faces_cascade(frame)
        
        # If no faces, hold last position
        if len(faces) == 0:
            if self.last_face:
                return [self.last_face]
            return []
        
        # Take highest confidence face
        best_face = max(faces, key=lambda f: f[4])
        x, y, w, h, conf = best_face
        
        # STRONG smoothing: 85% old, 15% new
        if self.last_face:
            lx, ly, lw, lh, lconf = self.last_face
            x = int(lx * self.smoothing + x * (1 - self.smoothing))
            y = int(ly * self.smoothing + y * (1 - self.smoothing))
            w = int(lw * self.smoothing + w * (1 - self.smoothing))
            h = int(lh * self.smoothing + h * (1 - self.smoothing))
        
        self.last_face = (x, y, w, h, conf)
        return [self.last_face]
    
    def annotate_frame(self, frame):
        """Draw face rectangles"""
        faces = self.detect_faces(frame)
        
        for x, y, w, h, conf in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        return frame, len(faces)
    
    def get_face_info(self, frame):
        """Get face data"""
        faces = self.detect_faces(frame)
        face_data = []
        
        for x, y, w, h, conf in faces:
            face_data.append({
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'center_x': int(x + w / 2),
                'center_y': int(y + h / 2),
                'confidence': float(conf)
            })
        
        return face_data