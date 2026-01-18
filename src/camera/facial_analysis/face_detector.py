import cv2
import numpy as np

class FacialAnalyzer:
    def __init__(self):
        """Initialize face detection - EXACTLY like reference"""
        self.use_mediapipe = False
        self.face_detector = None
        
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            # EXACTLY like reference - model 1, confidence 0.5
            self.face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )
            self.use_mediapipe = True
            print("✓ Using MediaPipe face detection")
        except (ImportError, AttributeError):
            print("⚠ MediaPipe not available, using OpenCV cascades")
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            print("✓ Using OpenCV Haar cascades")
        
        print("✓ Face detector initialized")
    
    def detect_faces_mediapipe(self, frame):
        """EXACTLY like reference code - simple and direct"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = frame.shape
        
        results = self.face_detector.process(rgb_frame)
        faces = []
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                
                # EXACTLY like reference - multiply by dimensions
                face_rect = np.multiply(
                    [bbox.xmin, bbox.ymin, bbox.width, bbox.height],
                    [w, h, w, h]
                ).astype(int)
                
                x, y, box_w, box_h = face_rect
                
                # Simple validation only
                if box_w > 30 and box_h > 30:
                    confidence = detection.score[0]
                    faces.append((x, y, box_w, box_h, confidence))
        
        return faces
    
    def detect_faces_cascade(self, frame):
        """Simple cascade detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        return [(x, y, w, h, 0.9) for x, y, w, h in faces]
    
    def detect_faces(self, frame):
        """Simple detection - return ALL faces found"""
        if self.use_mediapipe:
            return self.detect_faces_mediapipe(frame)
        else:
            return self.detect_faces_cascade(frame)
    
    def annotate_frame(self, frame):
        """Draw face rectangles"""
        faces = self.detect_faces(frame)
        
        for x, y, w, h, conf in faces:
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        return frame, len(faces)
    
    def get_face_info(self, frame):
        """Get face data - return first face only"""
        faces = self.detect_faces(frame)
        face_data = []
        
        # Only return the first (best) face
        if len(faces) > 0:
            x, y, w, h, conf = faces[0]
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