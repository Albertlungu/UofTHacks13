import time
from collections import deque

class FaceTracker:
    """
    Tracks face position and determines camera movement needed
    to keep face centered in frame.
    """
    
    def __init__(self, frame_width=640, frame_height=480, 
                 center_threshold=0.15, history_size=5):
        """
        Initialize face tracker.
        
        Args:
            frame_width: Width of video frame in pixels
            frame_height: Height of video frame in pixels
            center_threshold: How far from center before triggering movement (0.0-1.0)
            history_size: Number of positions to track for smoothing
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.center_x = frame_width / 2
        self.center_y = frame_height / 2
        self.center_threshold = center_threshold
        
        # Track position history for smoothing
        self.position_history = deque(maxlen=history_size)
        self.last_known_position = None
        self.frames_without_face = 0
        
    def update(self, faces):
        """
        Update tracker with detected faces.
        
        Args:
            faces: List of face dictionaries with keys: x, y, width, height, center_x, center_y
            
        Returns:
            dict: Tracking information including movement direction and distance
        """
        if len(faces) == 0:
            self.frames_without_face += 1
            return {
                'face_detected': False,
                'frames_without_face': self.frames_without_face,
                'should_move': False,
                'direction': None,
                'distance_from_center': None
            }
        
        # Reset counter when face is found
        self.frames_without_face = 0
        
        # Use the largest face (closest to camera)
        primary_face = max(faces, key=lambda f: f['width'] * f['height'])
        face_center_x = primary_face['center_x']
        face_center_y = primary_face['center_y']
        
        # Add to history
        self.position_history.append((face_center_x, face_center_y))
        self.last_known_position = (face_center_x, face_center_y)
        
        # Calculate smoothed position (average of recent positions)
        avg_x = sum(p[0] for p in self.position_history) / len(self.position_history)
        
        # Calculate normalized distance from center (-1.0 to 1.0)
        distance_from_center = (avg_x - self.center_x) / self.center_x
        
        # Determine if movement is needed
        should_move = abs(distance_from_center) > self.center_threshold
        
        # Determine direction
        direction = None
        if should_move:
            if distance_from_center > 0:
                direction = 'right'
            else:
                direction = 'left'
        
        return {
            'face_detected': True,
            'face_position': (face_center_x, face_center_y),
            'smoothed_position': (avg_x, face_center_y),
            'distance_from_center': distance_from_center,
            'should_move': should_move,
            'direction': direction,
            'face_size': (primary_face['width'], primary_face['height']),
            'frames_without_face': 0
        }
    
    def calculate_movement_steps(self, tracking_info, sensitivity=50):
        """
        Calculate how many stepper motor steps to move.
        
        Args:
            tracking_info: Dictionary from update() method
            sensitivity: Steps per unit distance (higher = more responsive)
            
        Returns:
            int: Number of steps to move (positive = right, negative = left)
        """
        if not tracking_info['should_move']:
            return 0
        
        distance = tracking_info['distance_from_center']
        steps = int(distance * sensitivity)
        
        return steps
    
    def is_face_leaving_frame(self, threshold=0.8):
        """
        Check if face is near the edge of the frame.
        
        Args:
            threshold: How close to edge (0.0-1.0) triggers leaving detection
            
        Returns:
            bool: True if face is near edge
        """
        if not self.last_known_position:
            return False
        
        x, _ = self.last_known_position
        normalized_x = x / self.frame_width
        
        return normalized_x < (1 - threshold) or normalized_x > threshold
