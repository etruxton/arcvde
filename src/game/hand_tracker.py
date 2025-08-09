"""
Enhanced hand tracking with finger gun detection
"""

import cv2
import mediapipe as mp
import math
import numpy as np
import time
from typing import Tuple, Optional
from utils.constants import *

class HandTracker:
    """Enhanced hand tracking for finger gun detection"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
            max_num_hands=1,
            model_complexity=1
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Tracking state
        self.detection_mode = "standard"
        self.confidence_score = 0
        self.shooting_detected = False
        self.last_shoot_time = 0
        self.previous_thumb_y = None
        self.previous_time = 0
        self.thumb_reset = True  # Track if thumb has been reset after shooting
    
    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate 2D distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def calculate_3d_distance(self, point1: Tuple[float, float, float], point2: Tuple[float, float, float]) -> float:
        """Calculate 3D distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)
    
    def get_wrist_angle(self, hand_landmarks) -> float:
        """Calculate the angle of the hand based on wrist and middle finger MCP"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        middle_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        
        # Calculate angle from horizontal
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        angle = math.atan2(dy, dx) * 180 / math.pi
        
        return angle
    
    def get_palm_normal(self, hand_landmarks) -> np.ndarray:
        """Calculate palm normal vector using wrist, index MCP, and pinky MCP"""
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        pinky_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_MCP]
        
        # Create vectors
        v1 = np.array([index_mcp.x - wrist.x, index_mcp.y - wrist.y, index_mcp.z - wrist.z])
        v2 = np.array([pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y, pinky_mcp.z - wrist.z])
        
        # Cross product gives normal
        normal = np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal)  # Normalize
        
        return normal
    
    def is_pointing_at_camera(self, hand_landmarks) -> bool:
        """Check if hand is pointing toward camera using Z-coordinates"""
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        
        # If index tip Z is less than wrist Z, finger is pointing at camera
        z_diff = wrist.z - index_tip.z
        return z_diff > 0.02  # Even more sensitive threshold
    
    def detect_finger_gun(self, hand_landmarks, frame_width: int, frame_height: int) -> Tuple[bool, Optional[Tuple[int, int]], Optional[object], Optional[object], Optional[float], float]:
        """Enhanced finger gun detection with multiple methods"""
        if hand_landmarks is None:
            return False, None, None, None, None, 0
        
        # Get all necessary landmarks
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]
        index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        
        # Method 1: Standard detection
        thumb_index_dist = self.calculate_distance((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
        middle_ring_dist = self.calculate_distance((middle_tip.x, middle_tip.y), (ring_tip.x, ring_tip.y))
        ring_pinky_dist = self.calculate_distance((ring_tip.x, ring_tip.y), (pinky_tip.x, pinky_tip.y))
        index_wrist_dist = self.calculate_distance((index_tip.x, index_tip.y), (wrist.x, wrist.y))
        thumb_middle_dist = self.calculate_distance((thumb_tip.x, thumb_tip.y), (middle_pip.x, middle_pip.y))
        
        scaled_thumb_index = THUMB_INDEX_THRESHOLD / 100.0
        scaled_middle_ring = MIDDLE_RING_THRESHOLD / 100.0
        scaled_ring_pinky = RING_PINKY_THRESHOLD / 100.0
        scaled_index_wrist = INDEX_WRIST_THRESHOLD / 100.0
        
        standard_checks = {
            'thumb_near_index': thumb_index_dist < scaled_thumb_index,
            'middle_ring_close': middle_ring_dist < scaled_middle_ring,
            'ring_pinky_close': ring_pinky_dist < scaled_ring_pinky,
            'index_extended': index_wrist_dist > scaled_index_wrist
        }
        
        standard_score = sum(standard_checks.values()) / len(standard_checks)
        
        # Method 2: Enhanced detection methods
        wrist_angle = self.get_wrist_angle(hand_landmarks)
        pointing_forward = self.is_pointing_at_camera(hand_landmarks)
        
        # Method 3: Enhanced finger curl detection using 3D coordinates
        middle_curl = middle_tip.z > middle_pip.z
        ring_curl = ring_tip.z > ring_pip.z
        pinky_curl = pinky_tip.z > pinky_pip.z
        
        # Method 4: Index finger extension check
        index_vector = np.array([index_tip.x - index_mcp.x, index_tip.y - index_mcp.y])
        index_length = np.linalg.norm(index_vector)
        index_extended_alt = index_length > 0.12  # More lenient
        
        # Combine detection methods with cascading logic (more lenient)
        if standard_score >= 0.6:  # Lower threshold for standard method
            self.detection_mode = "standard"
            self.confidence_score = standard_score
            is_gun = all(standard_checks.values())
        elif standard_score >= 0.3:  # Much lower threshold for partial detection
            if pointing_forward and index_extended_alt:
                self.detection_mode = "depth"
                self.confidence_score = 0.7
                is_gun = True
            elif abs(wrist_angle) < 75 and index_extended_alt:  # More lenient angle
                self.detection_mode = "wrist_angle"
                self.confidence_score = 0.6
                is_gun = middle_ring_dist < scaled_middle_ring * 2.5  # Much more lenient
            else:
                self.detection_mode = "none"
                self.confidence_score = standard_score
                is_gun = False
        elif pointing_forward and index_extended_alt:  # Removed finger curl requirement
            # Hand detected, try depth mode even without partial standard detection
            self.detection_mode = "depth"
            self.confidence_score = 0.6
            is_gun = True
        elif index_extended_alt:  # Much more lenient fallback
            # Fallback to wrist angle mode
            self.detection_mode = "wrist_angle"
            self.confidence_score = 0.4
            is_gun = True
        else:
            self.detection_mode = "none"
            self.confidence_score = 0
            is_gun = False
        
        if is_gun:
            index_coords = (int(index_tip.x * frame_width), int(index_tip.y * frame_height))
            return True, index_coords, thumb_tip, middle_pip, thumb_middle_dist, self.confidence_score
        else:
            return False, None, None, None, None, self.confidence_score
    
    def detect_shooting_gesture(self, thumb_tip, thumb_middle_dist: float) -> bool:
        """Detect shooting gesture (thumb flick) - requires thumb reset between shots"""
        current_time = time.time()
        current_thumb_y = thumb_tip.y
        
        if self.previous_thumb_y is not None:
            delta_time = current_time - self.previous_time
            if delta_time != 0:
                thumb_velocity = (current_thumb_y - self.previous_thumb_y) / delta_time
            else:
                thumb_velocity = 0
            
            # More lenient shooting detection for different modes
            velocity_threshold = SHOOT_VELOCITY_THRESHOLD * (1.5 if self.detection_mode != "standard" else 1.0)
            distance_threshold = SHOOT_DISTANCE_THRESHOLD * (1.5 if self.detection_mode != "standard" else 1.0)
            
            # Check for thumb reset - MUCH stricter thresholds
            # Require significant upward movement OR significant distance from middle finger
            reset_velocity_threshold = -velocity_threshold * 2.0  # Need strong upward movement
            reset_distance_threshold = distance_threshold * 2.5   # Need thumb far from middle finger
            
            if thumb_velocity < reset_velocity_threshold or thumb_middle_dist > reset_distance_threshold:
                # Only reset if we haven't just shot (prevents immediate reset from recoil)
                if current_time - self.last_shoot_time > 0.1:
                    self.thumb_reset = True
                    self.shooting_detected = False
            
            # Detect shooting only if thumb was reset
            # Also require minimum time between thumb movements to prevent hand shake triggering
            if thumb_velocity > velocity_threshold and thumb_middle_dist < distance_threshold:
                if self.thumb_reset and not self.shooting_detected and delta_time > 0.02:
                    self.shooting_detected = True
                    self.thumb_reset = False  # Require reset for next shot
                    self.last_shoot_time = current_time
                    self.previous_thumb_y = current_thumb_y
                    self.previous_time = current_time
                    return True
        
        self.previous_thumb_y = current_thumb_y
        self.previous_time = current_time
        return False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[object]]:
        """Process frame for hand detection"""
        # Convert BGR to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        return image, results
    
    def draw_landmarks(self, image: np.ndarray, hand_landmarks) -> None:
        """Draw hand landmarks on image"""
        self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
    
    def reset_tracking_state(self) -> None:
        """Reset tracking state when hand is lost"""
        self.shooting_detected = False
        self.previous_thumb_y = None
        self.previous_time = 0
        self.detection_mode = "none"
        self.confidence_score = 0
        self.thumb_reset = True