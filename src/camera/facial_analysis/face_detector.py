import cv2
import numpy as np
import time

class FacialAnalyzer:
    def __init__(self):
        """Initialize face detector with optimized cascade classifiers"""
        # Load cascade classifiers (lightweight and fast)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Simple exponential smoothing instead of Kalman (much faster)
        self.prev_faces = None
        self.smoothing_factor = 0.6
        self.min_confidence = 0.7
        
        # Frame skipping for performance
        self.frame_count = 0
        self.detect_every_n_frames = 1  # Detect every frame, skip disabled for best accuracy
        self.last_detection_time = 0
        
        print("✓ Face detector initialized (optimized for real-time)")
    
    def detect_faces_cascade(self, frame):
        """Fast cascade-based face detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with optimized parameters
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,      # Faster than 1.05
            minNeighbors=5,       # Good balance: faster + accurate
            minSize=(40, 40),     # Minimum face size
            maxSize=(400, 400),   # Maximum face size (skip huge detections)
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert to (x, y, w, h, confidence) format
        faces_with_conf = [(x, y, w, h, 0.95) for x, y, w, h in faces]
        
        return faces_with_conf
    
    def smooth_detections(self, current_faces):
        """Simple exponential smoothing for smooth motion (faster than Kalman)"""
        if current_faces is None or len(current_faces) == 0:
            self.prev_faces = None
            return []
        
        if self.prev_faces is None or len(self.prev_faces) == 0:
            self.prev_faces = current_faces
            return current_faces
        
        # Match current faces with previous faces (simple greedy matching)
        smoothed = []
        
        for curr_x, curr_y, curr_w, curr_h, curr_conf in current_faces:
            if self.prev_faces:
                # Find closest previous face
                best_idx = 0
                best_distance = float('inf')
                curr_center = (curr_x + curr_w/2, curr_y + curr_h/2)
                
                for i, (prev_x, prev_y, prev_w, prev_h, prev_conf) in enumerate(self.prev_faces):
                    prev_center = (prev_x + prev_w/2, prev_y + prev_h/2)
                    distance = (curr_center[0] - prev_center[0])**2 + (curr_center[1] - prev_center[1])**2
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_idx = i
                
                # Apply exponential smoothing
                if best_distance < 10000:  # Reasonable distance threshold
                    prev_x, prev_y, prev_w, prev_h, prev_conf = self.prev_faces[best_idx]
                    smooth_x = int(prev_x * (1 - self.smoothing_factor) + curr_x * self.smoothing_factor)
                    smooth_y = int(prev_y * (1 - self.smoothing_factor) + curr_y * self.smoothing_factor)
                    smooth_w = int(prev_w * (1 - self.smoothing_factor) + curr_w * self.smoothing_factor)
                    smooth_h = int(prev_h * (1 - self.smoothing_factor) + curr_h * self.smoothing_factor)
                    smooth_conf = (prev_conf + curr_conf) / 2
                else:
                    smooth_x, smooth_y, smooth_w, smooth_h = curr_x, curr_y, curr_w, curr_h
                    smooth_conf = curr_conf
            else:
                smooth_x, smooth_y, smooth_w, smooth_h = curr_x, curr_y, curr_w, curr_h
                smooth_conf = curr_conf
            
            smoothed.append((smooth_x, smooth_y, smooth_w, smooth_h, smooth_conf))
        
        self.prev_faces = current_faces
        return smoothed
    
    def detect_faces(self, frame):
        """Main detection method - optimized for real-time"""
        self.frame_count += 1
        
        # Detect faces using cascade classifier
        faces = self.detect_faces_cascade(frame)
        
        # Apply smoothing for stable output
        if len(faces) > 0:
            faces = self.smooth_detections(faces)
        else:
            # No faces detected, clear previous
            self.prev_faces = None
        
        return faces
    
    def annotate_frame(self, frame):
        """Draw face rectangles on frame with minimal overhead"""
        faces = self.detect_faces(frame)
        
        for x, y, w, h, conf in faces:
            # Draw rectangle
            color = (0, 255, 0)  # Green for detected faces
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw confidence score
            text = f"{conf:.2f}"
            cv2.putText(frame, text, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame, len(faces)
    
    def get_face_info(self, frame):
        """Get face data for avatar positioning"""
        faces = self.detect_faces(frame)
        face_data = []
        
        for x, y, w, h, conf in faces:
            face_info = {
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'center_x': int(x + w / 2),
                'center_y': int(y + h / 2),
                'confidence': float(conf)
            }
            face_data.append(face_info)
        
        return face_data