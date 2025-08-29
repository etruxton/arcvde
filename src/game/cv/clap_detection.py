"""
Clap detection using MediaPipe hand tracking
Detects when both hands come together in a clapping motion
"""

import math
import time
from collections import deque
from typing import Optional, Tuple, List

import cv2
import mediapipe as mp
import numpy as np

from .kalman_tracker import HandTracker

try:
    from utils.constants import (
        DEFAULT_CAMERA_ID,
    )
except ImportError:
    DEFAULT_CAMERA_ID = 0


class ClapDetector:
    """Detects clapping gestures using both hands"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5,  # Lower for better detection of side profiles
            min_tracking_confidence=0.3,   # Lower for more consistent tracking
            max_num_hands=2,  # We need both hands for clapping
            model_complexity=0,  # Use lighter model for better performance
            static_image_mode=False,
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Clap detection state
        self.clap_detected = False
        self.last_clap_time = 0
        self.clap_cooldown = 0.3  # Minimum time between claps
        self.hands_apart = True  # Track if hands were apart (required before detecting clap)
        
        # Distance tracking for clap detection
        self.hand_distances = deque(maxlen=10)  # Store recent hand distances
        self.velocity_buffer = deque(maxlen=5)  # Store hand velocity data
        
        # Thresholds for clap detection (more forgiving for natural clapping)
        self.clap_distance_threshold = 0.12  # Hands closer than this = potential clap (increased)
        self.apart_distance_threshold = 0.3   # Hands farther than this = definitely apart (increased)  
        self.velocity_threshold = 0.5  # Minimum velocity for clap detection (lowered)
        
        # Add temporal smoothing for hand loss
        self.last_hand_positions = None
        self.hand_loss_frames = 0
        self.max_hand_loss_frames = 5  # Allow brief hand loss
        
        # Initialize Kalman tracking for smoother hand tracking
        self.hand_tracker = HandTracker()
        
        # No need for own camera - will use frames from camera manager
        self.cap = None
        self.camera_initialized = False
        
    def calculate_hand_distance(self, left_hand, right_hand) -> float:
        """Calculate distance between the centers of both hands"""
        # Use wrist positions as hand centers
        left_wrist = left_hand.landmark[self.mp_hands.HandLandmark.WRIST]
        right_wrist = right_hand.landmark[self.mp_hands.HandLandmark.WRIST]
        
        distance = math.sqrt(
            (left_wrist.x - right_wrist.x) ** 2 + 
            (left_wrist.y - right_wrist.y) ** 2
        )
        return distance
    
    def calculate_palm_distance(self, left_hand, right_hand) -> float:
        """Calculate distance between palm centers for more accurate clap detection"""
        # Use middle finger MCP (metacarpophalangeal) joints as palm centers
        left_palm = left_hand.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        right_palm = right_hand.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        
        distance = math.sqrt(
            (left_palm.x - right_palm.x) ** 2 + 
            (left_palm.y - right_palm.y) ** 2
        )
        return distance
    
    def calculate_multi_point_distance(self, left_hand, right_hand) -> float:
        """Calculate minimum distance using multiple hand landmarks for better close detection"""
        # Try multiple landmark pairs - use the minimum distance found
        landmark_pairs = [
            # Wrists (most stable but furthest apart)
            (self.mp_hands.HandLandmark.WRIST, self.mp_hands.HandLandmark.WRIST),
            # Palm centers
            (self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP, self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP),
            # Index finger bases (closer to palm edge)
            (self.mp_hands.HandLandmark.INDEX_FINGER_MCP, self.mp_hands.HandLandmark.INDEX_FINGER_MCP),
            # Ring finger bases 
            (self.mp_hands.HandLandmark.RING_FINGER_MCP, self.mp_hands.HandLandmark.RING_FINGER_MCP),
            # Thumb bases (often stay visible)
            (self.mp_hands.HandLandmark.THUMB_CMC, self.mp_hands.HandLandmark.THUMB_CMC),
            # Pinky bases (outer edges)
            (self.mp_hands.HandLandmark.PINKY_MCP, self.mp_hands.HandLandmark.PINKY_MCP),
        ]
        
        min_distance = float('inf')
        
        for left_landmark, right_landmark in landmark_pairs:
            try:
                left_point = left_hand.landmark[left_landmark]
                right_point = right_hand.landmark[right_landmark]
                
                distance = math.sqrt(
                    (left_point.x - right_point.x) ** 2 + 
                    (left_point.y - right_point.y) ** 2
                )
                min_distance = min(min_distance, distance)
            except:
                # Skip if landmark not available
                continue
        
        return min_distance if min_distance != float('inf') else 1.0
    
    def are_hands_facing_each_other(self, left_hand, right_hand) -> bool:
        """Check if hands are oriented to face each other (palms facing)"""
        # Get thumb and pinky positions to determine hand orientation
        left_thumb = left_hand.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        left_pinky = left_hand.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        right_thumb = right_hand.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        right_pinky = right_hand.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        
        # Calculate hand orientations
        left_orientation = left_thumb.x - left_pinky.x
        right_orientation = right_thumb.x - right_pinky.x
        
        # For clapping, hands should have opposite orientations
        # Left hand thumb should be right of pinky, right hand thumb should be left of pinky
        return (left_orientation > 0 and right_orientation < 0) or \
               (left_orientation < 0 and right_orientation > 0)
    
    def detect_clap_motion(self, current_distance: float) -> bool:
        """Detect clapping motion based on hand distance changes (simplified)"""
        current_time = time.time()
        
        # Add current distance to buffer
        self.hand_distances.append((current_distance, current_time))
        
        # Set hands_apart when they're in red zone (far apart)
        if current_distance > self.apart_distance_threshold:
            self.hands_apart = True
            return False
        
        # Also set hands_apart when they're in yellow zone (medium distance)
        # This allows clapping from yellow→green, not just red→green
        if current_distance > self.clap_distance_threshold:
            self.hands_apart = True
        
        # Detect clap when hands come into green zone after being apart (red OR yellow)
        if current_distance < self.clap_distance_threshold and self.hands_apart:
            # Check cooldown to prevent multiple triggers
            if current_time - self.last_clap_time > self.clap_cooldown:
                self.hands_apart = False  # Reset apart state
                self.last_clap_time = current_time
                print(f"[DEBUG] CLAP DETECTED! Distance: {current_distance:.3f}")
                return True
        
        return False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool, dict]:
        """
        Process frame for clap detection
        
        Returns:
            tuple: (processed_frame, clap_detected, debug_info)
        """
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        
        # Convert back to BGR for display
        image = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        image.flags.writeable = True
        
        clap_detected = False
        current_time = time.time()
        
        debug_info = {
            "hands_detected": 0,
            "hand_distance": 0,
            "hands_apart": self.hands_apart,
            "velocity": 0,
            "facing_each_other": False,
            "kalman_tracking": False
        }
        
        # Extract hand positions for Kalman tracking
        left_hand_pos = None
        right_hand_pos = None
        
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
            debug_info["hands_detected"] = 2
            
            # We have both hands
            left_hand = results.multi_hand_landmarks[0]
            right_hand = results.multi_hand_landmarks[1]
            
            # Determine which hand is which based on x position
            left_wrist = left_hand.landmark[self.mp_hands.HandLandmark.WRIST]
            right_wrist = right_hand.landmark[self.mp_hands.HandLandmark.WRIST]
            
            if left_wrist.x > right_wrist.x:
                left_hand, right_hand = right_hand, left_hand
                left_wrist, right_wrist = right_wrist, left_wrist
            
            # Extract positions for Kalman tracking (use wrists as primary tracking points)
            left_hand_pos = (left_wrist.x, left_wrist.y)
            right_hand_pos = (right_wrist.x, right_wrist.y)
            
            # Calculate distances using multiple strategies
            palm_distance = self.calculate_palm_distance(left_hand, right_hand)
            wrist_distance = self.calculate_hand_distance(left_hand, right_hand)
            multi_point_distance = self.calculate_multi_point_distance(left_hand, right_hand)
            
            # Use the minimum distance from all methods for better close detection
            current_distance = min(palm_distance, wrist_distance, multi_point_distance)
            debug_info["hand_distance"] = current_distance
            debug_info["palm_distance"] = palm_distance
            debug_info["wrist_distance"] = wrist_distance
            debug_info["multi_point_distance"] = multi_point_distance
            
            # Check if hands are facing each other
            facing_each_other = self.are_hands_facing_each_other(left_hand, right_hand)
            debug_info["facing_each_other"] = facing_each_other
            
            # Detect claps regardless of hand orientation (removed facing_each_other requirement)
            # This allows for natural clapping with palms perpendicular to camera
            clap_detected = self.detect_clap_motion(current_distance)
            
            # Store hand positions for temporal smoothing
            self.last_hand_positions = (left_hand, right_hand)
            self.hand_loss_frames = 0
            
            # Draw hand landmarks
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Draw connection line between hands
            h, w, _ = image.shape
            left_palm = left_hand.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
            right_palm = right_hand.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
            
            left_pos = (int(left_palm.x * w), int(left_palm.y * h))
            right_pos = (int(right_palm.x * w), int(right_palm.y * h))
            
            # Color based on distance
            if current_distance < self.clap_distance_threshold:
                color = (0, 255, 0)  # Green when close
            elif current_distance < self.apart_distance_threshold:
                color = (0, 255, 255)  # Yellow when medium
            else:
                color = (0, 0, 255)  # Red when apart
            
            cv2.line(image, left_pos, right_pos, color, 3)
            
            # Draw distance text
            mid_point = ((left_pos[0] + right_pos[0]) // 2, (left_pos[1] + right_pos[1]) // 2)
            cv2.putText(image, f"{current_distance:.3f}", mid_point, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        elif results.multi_hand_landmarks:
            debug_info["hands_detected"] = len(results.multi_hand_landmarks)
            # Draw single hand
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Handle temporal smoothing when we only have one hand
            if self.last_hand_positions and self.hand_loss_frames < self.max_hand_loss_frames:
                self.hand_loss_frames += 1
                # Continue clap detection using last known positions with multi-point distance
                left_hand, right_hand = self.last_hand_positions
                palm_distance = self.calculate_palm_distance(left_hand, right_hand)
                multi_point_distance = self.calculate_multi_point_distance(left_hand, right_hand)
                current_distance = min(palm_distance, multi_point_distance)
                clap_detected = self.detect_clap_motion(current_distance)
                debug_info["hand_distance"] = current_distance
                debug_info["temporal_smoothing"] = True
        else:
            # No hands detected
            debug_info["hands_detected"] = 0
            if self.last_hand_positions and self.hand_loss_frames < self.max_hand_loss_frames:
                self.hand_loss_frames += 1
                # Continue clap detection using last known positions briefly with multi-point distance
                left_hand, right_hand = self.last_hand_positions
                palm_distance = self.calculate_palm_distance(left_hand, right_hand)
                multi_point_distance = self.calculate_multi_point_distance(left_hand, right_hand)
                current_distance = min(palm_distance, multi_point_distance)
                clap_detected = self.detect_clap_motion(current_distance)
                debug_info["hand_distance"] = current_distance
                debug_info["temporal_smoothing"] = True
            else:
                # Reset state when hands are truly gone
                self.last_hand_positions = None
                self.hand_loss_frames = 0
        
        # Update Kalman tracking with hand positions (or None if not detected)
        tracking_info = self.hand_tracker.update(left_hand_pos, right_hand_pos, current_time)
        
        # Use Kalman-tracked distance and velocity for improved clap detection
        if tracking_info['left_hand_detected'] and tracking_info['right_hand_detected']:
            # Both hands detected - use original detection
            pass  # current_distance already calculated above
        elif tracking_info['left_hand_detected'] or tracking_info['right_hand_detected']:
            # One hand lost - use Kalman prediction
            kalman_distance = self.hand_tracker.get_hand_distance()
            current_distance = min(current_distance, kalman_distance)
            debug_info["kalman_tracking"] = True
            debug_info["kalman_distance"] = kalman_distance
        else:
            # Both hands lost - use Kalman prediction if recently tracking
            if self.hand_tracker.left_hand_tracker.initialized and self.hand_tracker.right_hand_tracker.initialized:
                kalman_distance = self.hand_tracker.get_hand_distance()
                current_distance = kalman_distance
                debug_info["kalman_tracking"] = True
                debug_info["kalman_distance"] = kalman_distance
                
                # Use Kalman tracking for clap detection when hands are lost
                clap_detected = self.detect_clap_motion(current_distance)
        
        # Add velocity information from Kalman tracking
        if tracking_info['left_hand_detected'] or tracking_info['right_hand_detected']:
            approach_velocity = self.hand_tracker.get_approach_velocity()
            debug_info["approach_velocity"] = approach_velocity
            debug_info["left_hand_speed"] = tracking_info['left_hand_speed']
            debug_info["right_hand_speed"] = tracking_info['right_hand_speed']
        
        # Draw clap detection status (only show when clap is detected)
        if clap_detected:
            status_text = "CLAP!"
            status_color = (0, 255, 0)
            cv2.putText(image, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        return image, clap_detected, debug_info
    
    def _initialize_camera(self):
        """Initialize camera for standalone clap detection"""
        try:
            self.cap = cv2.VideoCapture(DEFAULT_CAMERA_ID)
            if self.cap.isOpened():
                # Set camera properties for faster initialization
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print("Clap detection camera initialized successfully")
            else:
                print("Warning: Could not open camera for clap detection")
                self.cap = None
        except Exception as e:
            print(f"Error initializing camera for clap detection: {e}")
            self.cap = None
    
    def check_clap(self) -> bool:
        """Check if a clap was detected (simplified interface)"""
        # Lazy camera initialization
        if not self.camera_initialized:
            self._initialize_camera()
            self.camera_initialized = True
        
        if self.cap is None:
            return False
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                return False
            
            # Process the frame to detect claps
            _, clap_detected, _ = self.process_frame(frame)
            return clap_detected
        except Exception as e:
            print(f"Error during clap detection: {e}")
            return False
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def reset_state(self):
        """Reset clap detection state"""
        self.hands_apart = True
        self.hand_distances.clear()
        self.velocity_buffer.clear()
        self.clap_detected = False