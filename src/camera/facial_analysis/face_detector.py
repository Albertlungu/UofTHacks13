import cv2
import numpy as np

class FacialAnalyzer:
    def __init__(self):
        # Load pre-trained face detection model
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
    def detect_faces(self, frame):
        """
        Detect faces in a frame and return coordinates
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        return faces
    
    def detect_eyes(self, frame, face_roi):
        """
        Detect eyes within a face region
        """
        x, y, w, h = face_roi
        roi_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(roi_gray)
        return eyes
    
    def annotate_frame(self, frame):
        """
        Annotate frame with face and eye detection
        """
        faces = self.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Detect and draw eyes
            eyes = self.detect_eyes(frame, (x, y, w, h))
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 255, 0), 2)
        
        return frame, len(faces)
    
    def get_face_info(self, frame):
        """
        Get detailed information about detected faces
        """
        faces = self.detect_faces(frame)
        face_data = []
        
        for (x, y, w, h) in faces:
            face_info = {
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h),
                'center_x': int(x + w/2),
                'center_y': int(y + h/2)
            }
            face_data.append(face_info)
        
        return face_data
