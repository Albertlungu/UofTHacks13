"""
Clean hand tracking implementation with MediaPipe.
Focuses on accurate gesture detection and sends raw landmarks to frontend.
"""

from typing import Dict, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np
from loguru import logger


class HandTracker:
    """Tracks hands and detects gestures for 3D block building."""

    def __init__(self):
        """Initialize MediaPipe Hands with optimal settings."""
        try:
            self.mp_hands = mp.solutions.hands
        except AttributeError as exc:
            try:
                from mediapipe.python import solutions as mp_solutions

                self.mp_hands = mp_solutions.hands
            except Exception as inner_exc:
                raise RuntimeError(
                    "MediaPipe is not available or incompatible. "
                    "Install mediapipe on Python 3.10 or 3.11 (Apple Silicon supported), "
                    "then retry running run_hand_tracker.py."
                ) from inner_exc
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.prev_gestures = {}
        logger.info("HandTracker initialized with MediaPipe")

    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a video frame and detect hands + gestures.

        Args:
            frame: BGR image from camera

        Returns:
            {
                'hands': [
                    {
                        'landmarks': [...],  # 21 3D points (x, y, z) normalized
                        'handedness': 'Left' or 'Right',
                        'is_pinching': bool,
                        'is_fist': bool,
                        'pinch_strength': float (0-1)
                    }
                ],
                'timestamp': float
            }
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        hand_data = {
            "hands": [],
            "timestamp": cv2.getTickCount() / cv2.getTickFrequency(),
        }

        if not results.multi_hand_landmarks:
            return hand_data

        # Process each detected hand
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = results.multi_handedness[idx].classification[0].label
            confidence = results.multi_handedness[idx].classification[0].score

            # Filter low confidence detections
            if confidence < 0.7:
                continue

            # Extract normalized 3D landmarks
            landmarks = [
                {"x": lm.x, "y": lm.y, "z": lm.z}
                for lm in hand_landmarks.landmark
            ]

            # Detect gestures
            is_pinching, pinch_strength = self._detect_pinch(landmarks)
            is_fist = self._detect_fist(landmarks)

            hand_data["hands"].append(
                {
                    "landmarks": landmarks,
                    "handedness": handedness,  # MediaPipe gives camera view
                    "is_pinching": is_pinching,
                    "is_fist": is_fist,
                    "pinch_strength": pinch_strength,
                }
            )

        return hand_data

    def _detect_pinch(self, landmarks: List[Dict]) -> Tuple[bool, float]:
        """
        Detect pinch gesture (thumb tip + index tip close together).

        Returns:
            (is_pinching, pinch_strength) where pinch_strength is 0-1
        """
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]

        # Calculate 3D distance
        distance = np.sqrt(
            (thumb_tip["x"] - index_tip["x"]) ** 2
            + (thumb_tip["y"] - index_tip["y"]) ** 2
            + (thumb_tip["z"] - index_tip["z"]) ** 2
        )

        # Normalize distance to pinch strength (0 = far, 1 = touching)
        # Typical pinch distance ranges from 0.02 (touching) to 0.15 (open)
        pinch_strength = 1.0 - np.clip((distance - 0.02) / 0.13, 0, 1)

        # Consider it a pinch if strength > 0.7
        is_pinching = pinch_strength > 0.7

        return is_pinching, float(pinch_strength)

    def _detect_fist(self, landmarks: List[Dict]) -> bool:
        """
        Detect fist gesture (all fingers curled).

        Returns:
            True if hand is making a fist
        """
        # Check if fingertips are curled (below their PIP joints in Y)
        # Landmarks: 8=index tip, 6=index PIP, 12=middle tip, 10=middle PIP, etc.
        finger_checks = [
            (8, 6),  # Index
            (12, 10),  # Middle
            (16, 14),  # Ring
            (20, 18),  # Pinky
        ]

        curled_count = 0
        for tip_idx, pip_idx in finger_checks:
            # In normalized coords, lower Y = higher on screen
            # If tip Y >= PIP Y, finger is curled
            if landmarks[tip_idx]["y"] >= landmarks[pip_idx]["y"]:
                curled_count += 1

        # Also check thumb is not extended
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        index_mcp = landmarks[5]

        # Thumb should be close to hand center
        thumb_distance = np.sqrt(
            (thumb_tip["x"] - index_mcp["x"]) ** 2
            + (thumb_tip["y"] - index_mcp["y"]) ** 2
        )

        thumb_curled = thumb_distance < 0.15

        # Fist if 3+ fingers curled and thumb not extended
        return curled_count >= 3 and thumb_curled

    def cleanup(self):
        """Release MediaPipe resources."""
        self.hands.close()
        logger.info("HandTracker cleaned up")
