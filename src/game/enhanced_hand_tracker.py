"""
Enhanced hand tracking with preprocessing, joint angles, and Kalman filtering
"""

# Standard library imports
import math
import time
from collections import deque
from typing import Optional, Tuple

# Third-party imports
import cv2
import mediapipe as mp
import numpy as np

try:
    # Local application imports
    from utils.constants import (
        INDEX_WRIST_THRESHOLD,
        MIDDLE_RING_THRESHOLD,
        RING_PINKY_THRESHOLD,
        SHOOT_DISTANCE_THRESHOLD,
        SHOOT_VELOCITY_THRESHOLD,
        THUMB_INDEX_THRESHOLD,
    )
except ImportError:
    # Fallback constants if not in proper package structure
    INDEX_WRIST_THRESHOLD = 10
    MIDDLE_RING_THRESHOLD = 8
    RING_PINKY_THRESHOLD = 8
    SHOOT_DISTANCE_THRESHOLD = 0.1
    SHOOT_VELOCITY_THRESHOLD = 0.1
    THUMB_INDEX_THRESHOLD = 35

try:
    from .kalman_tracker import HandKalmanTracker
except ImportError:
    # Third-party imports
    from kalman_tracker import HandKalmanTracker

try:
    from .region_adaptive_detector import RegionAdaptiveDetector
except ImportError:
    # Third-party imports
    from region_adaptive_detector import RegionAdaptiveDetector


class FramePreprocessor:
    """Handles frame preprocessing for better hand detection in various lighting conditions"""

    def __init__(self):
        # CLAHE for adaptive histogram equalization
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

        # Cache for performance
        self.last_hand_region = None
        self.gamma_table_cache = {}

    def preprocess_frame(self, frame: np.ndarray, hand_roi: Optional[Tuple] = None) -> np.ndarray:
        """
        Apply preprocessing to improve hand detection in various lighting conditions

        Args:
            frame: Input BGR frame
            hand_roi: Optional region of interest (x, y, width, height) for targeted preprocessing
        """
        # Create a copy to avoid modifying original
        processed = frame.copy()

        # Step 1: Convert to LAB color space for better lighting control
        lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Step 2: Apply CLAHE to the L channel
        l_channel = self.clahe.apply(l_channel)

        # Step 3: Merge channels back
        enhanced_lab = cv2.merge([l_channel, a_channel, b_channel])
        processed = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # Step 4: Apply bilateral filter to reduce noise while preserving edges
        # Use smaller kernel for faster processing
        processed = cv2.bilateralFilter(processed, 5, 50, 50)

        # Step 5: Adaptive gamma correction
        processed = self._apply_adaptive_gamma(processed)

        # Step 6: Optional shadow reduction for hand region
        if hand_roi is not None:
            processed = self._reduce_shadows_in_roi(processed, hand_roi)

        return processed

    def _apply_adaptive_gamma(self, image: np.ndarray) -> np.ndarray:
        """Apply gamma correction based on image brightness"""
        # Calculate mean brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)

        # Determine gamma value
        if mean_brightness < 80:  # Very dark
            gamma = 1.8
        elif mean_brightness < 100:  # Dark
            gamma = 1.5
        elif mean_brightness > 170:  # Very bright
            gamma = 0.6
        elif mean_brightness > 150:  # Bright
            gamma = 0.8
        else:  # Normal
            gamma = 1.0

        # Use cached gamma table if available
        gamma_key = round(gamma, 1)
        if gamma_key not in self.gamma_table_cache:
            inv_gamma = 1.0 / gamma
            self.gamma_table_cache[gamma_key] = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype(
                "uint8"
            )

        # Apply gamma correction using lookup table
        return cv2.LUT(image, self.gamma_table_cache[gamma_key])

    def _reduce_shadows_in_roi(self, image: np.ndarray, roi: Tuple) -> np.ndarray:
        """Reduce shadows in the region of interest"""
        x, y, w, h = roi
        # Ensure integer coordinates
        x, y, w, h = int(x), int(y), int(w), int(h)

        # Check if ROI is valid
        if w <= 0 or h <= 0:
            return image

        # Ensure ROI is within image bounds
        img_h, img_w = image.shape[:2]
        if x >= img_w or y >= img_h:
            return image

        # Clip ROI to image bounds
        x = max(0, x)
        y = max(0, y)
        x_end = min(x + w, img_w)
        y_end = min(y + h, img_h)

        if x_end <= x or y_end <= y:
            return image

        # Extract ROI
        roi_img = image[y:y_end, x:x_end]

        if roi_img.size == 0:
            return image

        # Convert to HSV for shadow detection
        hsv = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Enhance value channel to reduce shadows
        v_enhanced = cv2.add(v, 30)  # Brighten shadows
        v_enhanced = np.clip(v_enhanced, 0, 255).astype(np.uint8)

        # Merge back
        hsv_enhanced = cv2.merge([h, s, v_enhanced])
        roi_enhanced = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)

        # Blend enhanced ROI back into image
        image[y:y_end, x:x_end] = roi_enhanced

        return image

    def get_hand_roi(self, hand_landmarks, frame_shape: Tuple) -> Optional[Tuple]:
        """Calculate bounding box for hand with padding"""
        if hand_landmarks is None:
            return None

        h, w = frame_shape[:2]

        # Get all x and y coordinates
        xs = [lm.x * w for lm in hand_landmarks.landmark]
        ys = [lm.y * h for lm in hand_landmarks.landmark]

        # Calculate bounding box with padding
        padding = 50  # pixels
        x_min = max(0, int(min(xs) - padding))
        y_min = max(0, int(min(ys) - padding))
        x_max = min(w, int(max(xs) + padding))
        y_max = min(h, int(max(ys) + padding))

        return (x_min, y_min, x_max - x_min, y_max - y_min)


class EnhancedHandTracker:
    """Enhanced hand tracking with preprocessing, joint angles, and temporal smoothing"""

    def __init__(self, enable_preprocessing=True, enable_angles=True, enable_kalman=True):
        # Configuration
        self.enable_preprocessing = enable_preprocessing
        self.enable_angles = enable_angles
        self.enable_kalman = enable_kalman

        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.6,  # Slightly lower for preprocessed frames
            min_tracking_confidence=0.5,
            max_num_hands=1,
            model_complexity=1,
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Initialize preprocessor
        self.preprocessor = FramePreprocessor() if enable_preprocessing else None

        # Initialize Kalman tracker
        self.kalman_tracker = HandKalmanTracker() if enable_kalman else None

        # Initialize region adaptive detector (640x480 default camera size)
        self.region_detector = RegionAdaptiveDetector(640, 480)

        # Tracking state
        self.detection_mode = "standard"
        self.confidence_score = 0
        self.shooting_detected = False
        self.last_shoot_time = 0
        self.previous_thumb_y = None
        self.previous_time = 0
        self.thumb_reset = True

        # Performance monitoring
        self.preprocessing_time = 0
        self.detection_time = 0

        # Gesture validation buffer
        self.gesture_buffer = deque(maxlen=5)

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate 2D distance between two points"""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def calculate_3d_distance(self, point1: Tuple[float, float, float], point2: Tuple[float, float, float]) -> float:
        """Calculate 3D distance between two points"""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2)

    def calculate_angle_3points(self, p1, p2, p3) -> float:
        """Calculate angle at p2 formed by p1-p2-p3"""
        # Convert landmarks to numpy arrays
        a = np.array([p1.x, p1.y, p1.z])
        b = np.array([p2.x, p2.y, p2.z])
        c = np.array([p3.x, p3.y, p3.z])

        # Calculate vectors
        ba = a - b
        bc = c - b

        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def calculate_finger_curl(self, mcp, pip, dip, tip) -> float:
        """Calculate finger curl ratio (0 = straight, 1 = fully curled)"""
        # Calculate angles at each joint
        angle_pip = self.calculate_angle_3points(mcp, pip, dip)
        angle_dip = self.calculate_angle_3points(pip, dip, tip)

        # Normalize angles (180° = straight, 0° = fully bent)
        curl_pip = 1.0 - (angle_pip / 180.0)
        curl_dip = 1.0 - (angle_dip / 180.0)

        # Average curl across joints
        return (curl_pip + curl_dip) / 2.0

    def calculate_finger_angles(self, hand_landmarks) -> dict:
        """Calculate angles for all fingers"""
        if not self.enable_angles:
            return {}

        angles = {}

        # Define finger indices
        finger_indices = {
            "INDEX": [
                self.mp_hands.HandLandmark.INDEX_FINGER_MCP,
                self.mp_hands.HandLandmark.INDEX_FINGER_PIP,
                self.mp_hands.HandLandmark.INDEX_FINGER_DIP,
                self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
            ],
            "MIDDLE": [
                self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
                self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
                self.mp_hands.HandLandmark.MIDDLE_FINGER_DIP,
                self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            ],
            "RING": [
                self.mp_hands.HandLandmark.RING_FINGER_MCP,
                self.mp_hands.HandLandmark.RING_FINGER_PIP,
                self.mp_hands.HandLandmark.RING_FINGER_DIP,
                self.mp_hands.HandLandmark.RING_FINGER_TIP,
            ],
            "PINKY": [
                self.mp_hands.HandLandmark.PINKY_MCP,
                self.mp_hands.HandLandmark.PINKY_PIP,
                self.mp_hands.HandLandmark.PINKY_DIP,
                self.mp_hands.HandLandmark.PINKY_TIP,
            ],
        }

        # Calculate curl for each finger
        for finger_name, indices in finger_indices.items():
            mcp = hand_landmarks.landmark[indices[0]]
            pip = hand_landmarks.landmark[indices[1]]
            dip = hand_landmarks.landmark[indices[2]]
            tip = hand_landmarks.landmark[indices[3]]

            angles[f"{finger_name}_curl"] = self.calculate_finger_curl(mcp, pip, dip, tip)

        return angles

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
        return z_diff > 0.02

    def detect_finger_gun_with_angles(self, hand_landmarks, angles: dict) -> Tuple[bool, float]:
        """Detect finger gun using joint angles"""
        if not angles:
            return False, 0

        # Check if index is extended
        index_extended = angles.get("INDEX_curl", 1.0) < 0.35

        # Check if other fingers are curled
        middle_curled = angles.get("MIDDLE_curl", 0) > 0.55
        ring_curled = angles.get("RING_curl", 0) > 0.55
        pinky_curled = angles.get("PINKY_curl", 0) > 0.55

        # Calculate confidence based on how well conditions are met
        confidence = 0
        if index_extended:
            confidence += 0.3
        if middle_curled:
            confidence += 0.2
        if ring_curled:
            confidence += 0.2
        if pinky_curled:
            confidence += 0.2

        # Check thumb position (should be up or to the side)
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_IP]
        thumb_up = thumb_tip.y < thumb_ip.y
        if thumb_up:
            confidence += 0.1

        return confidence > 0.7, confidence

    def detect_finger_gun(
        self, hand_landmarks, frame_width: int, frame_height: int
    ) -> Tuple[bool, Optional[Tuple[int, int]], Optional[object], Optional[object], Optional[float], float]:
        """Enhanced finger gun detection with region-adaptive parameters"""
        if hand_landmarks is None:
            return False, None, None, None, None, 0

        # Get hand position category and adaptive parameters
        position_category = self.region_detector.get_hand_position_category(hand_landmarks)
        adaptive_params = self.region_detector.get_adaptive_thresholds(position_category)
        position_hints = self.region_detector.adjust_detection_for_problem_zone(hand_landmarks)

        # Store for debug display
        self.last_position_category = position_category
        self.last_position_hints = position_hints

        # Get all necessary landmarks
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]

        # Calculate finger angles if enabled
        angles = self.calculate_finger_angles(hand_landmarks)

        # Method 1: Standard detection
        thumb_index_dist = self.calculate_distance((thumb_tip.x, thumb_tip.y), (index_tip.x, index_tip.y))
        middle_ring_dist = self.calculate_distance((middle_tip.x, middle_tip.y), (ring_tip.x, ring_tip.y))
        ring_pinky_dist = self.calculate_distance((ring_tip.x, ring_tip.y), (pinky_tip.x, pinky_tip.y))
        index_wrist_dist = self.calculate_distance((index_tip.x, index_tip.y), (wrist.x, wrist.y))
        thumb_middle_dist = self.calculate_distance((thumb_tip.x, thumb_tip.y), (middle_pip.x, middle_pip.y))

        # Apply adaptive multipliers to thresholds
        scaled_thumb_index = (THUMB_INDEX_THRESHOLD / 100.0) * adaptive_params["thumb_index_multiplier"]
        scaled_middle_ring = (MIDDLE_RING_THRESHOLD / 100.0) * adaptive_params["middle_ring_multiplier"]
        scaled_ring_pinky = (RING_PINKY_THRESHOLD / 100.0) * adaptive_params["ring_pinky_multiplier"]
        scaled_index_wrist = (INDEX_WRIST_THRESHOLD / 100.0) * adaptive_params["index_wrist_multiplier"]

        standard_checks = {
            "thumb_near_index": thumb_index_dist < scaled_thumb_index,
            "middle_ring_close": middle_ring_dist < scaled_middle_ring,
            "ring_pinky_close": ring_pinky_dist < scaled_ring_pinky,
            "index_extended": index_wrist_dist > scaled_index_wrist,
        }

        # In problem zone, don't require all checks
        if position_category == "problem_zone":
            # Count how many checks pass
            checks_passed = sum(standard_checks.values())
            # Need at least 3 out of 4 in problem zone
            standard_score = checks_passed / len(standard_checks)
            if checks_passed >= 3:
                standard_score = max(standard_score, 0.75)  # Boost score if most checks pass
        else:
            standard_score = sum(standard_checks.values()) / len(standard_checks)

        # Method 2: Angle-based detection
        angle_detected = False
        angle_confidence = 0
        if self.enable_angles and angles:
            angle_detected, angle_confidence = self.detect_finger_gun_with_angles(hand_landmarks, angles)

        # Method 3: Enhanced detection methods
        wrist_angle = self.get_wrist_angle(hand_landmarks)
        pointing_forward = self.is_pointing_at_camera(hand_landmarks)

        # Method 4: Index finger extension check
        index_vector = np.array([index_tip.x - index_mcp.x, index_tip.y - index_mcp.y])
        index_length = np.linalg.norm(index_vector)
        index_extended_alt = index_length > 0.12

        # Combine detection methods with improved logic
        is_gun = False
        final_confidence = 0

        # Apply region-specific confidence calculation
        if position_category == "problem_zone":
            # Use special logic for problem zone
            region_confidence = self.region_detector.calculate_region_specific_confidence(
                standard_score, angle_confidence if angle_detected else 0, position_category, position_hints
            )

            # Lower thresholds for problem zone
            if region_confidence > adaptive_params["min_confidence"]:
                self.detection_mode = f"region_{position_category}"
                self.confidence_score = region_confidence
                is_gun = True
                final_confidence = region_confidence
            elif standard_score >= 0.5 and checks_passed >= 3:  # Fallback for problem zone
                self.detection_mode = "standard_adaptive"
                self.confidence_score = standard_score
                is_gun = True
                final_confidence = standard_score
        # Normal detection for non-problem zones
        elif angle_detected and angle_confidence > 0.75:
            self.detection_mode = "angles"
            self.confidence_score = angle_confidence
            is_gun = True
            final_confidence = angle_confidence
        elif standard_score >= 0.6:  # Lower threshold for standard method
            self.detection_mode = "standard"
            self.confidence_score = standard_score
            is_gun = all(standard_checks.values())
            final_confidence = standard_score
        elif standard_score >= 0.3:  # Much lower threshold for partial detection
            if pointing_forward and index_extended_alt:
                self.detection_mode = "depth"
                self.confidence_score = 0.7
                is_gun = True
                final_confidence = 0.7
            elif abs(wrist_angle) < 75 and index_extended_alt:
                self.detection_mode = "wrist_angle"
                self.confidence_score = 0.6
                is_gun = middle_ring_dist < scaled_middle_ring * 2.5
                final_confidence = 0.6
            elif angle_confidence > 0.5:  # Use angles as fallback
                self.detection_mode = "angles_fallback"
                self.confidence_score = angle_confidence
                is_gun = angle_detected
                final_confidence = angle_confidence
            else:
                self.detection_mode = "none"
                self.confidence_score = standard_score
                is_gun = False
                final_confidence = standard_score
        elif pointing_forward and index_extended_alt:
            # Hand detected, try depth mode even without partial standard detection
            self.detection_mode = "depth"
            self.confidence_score = 0.6
            is_gun = True
            final_confidence = 0.6
        elif angle_confidence > 0.6:  # Angle detection as last resort
            self.detection_mode = "angles_only"
            self.confidence_score = angle_confidence
            is_gun = angle_detected
            final_confidence = angle_confidence
        elif index_extended_alt:
            self.detection_mode = "wrist_angle"
            self.confidence_score = 0.4
            is_gun = True
            final_confidence = 0.4
        else:
            self.detection_mode = "none"
            self.confidence_score = 0
            is_gun = False
            final_confidence = 0

        # Add to gesture buffer for validation
        self.gesture_buffer.append((is_gun, final_confidence))

        # Validate gesture over multiple frames
        if len(self.gesture_buffer) >= 3:
            detections = sum(1 for g, _ in self.gesture_buffer if g)
            avg_confidence = np.mean([c for _, c in self.gesture_buffer])

            # Require consistent detection
            if detections < len(self.gesture_buffer) * 0.5:
                is_gun = False
                final_confidence = avg_confidence * 0.5

        if is_gun:
            index_coords = (int(index_tip.x * frame_width), int(index_tip.y * frame_height))
            return True, index_coords, thumb_tip, middle_pip, thumb_middle_dist, final_confidence
        else:
            return False, None, None, None, None, final_confidence

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

            # Check for thumb reset
            reset_velocity_threshold = -velocity_threshold * 2.0
            reset_distance_threshold = distance_threshold * 2.5

            if thumb_velocity < reset_velocity_threshold or thumb_middle_dist > reset_distance_threshold:
                if current_time - self.last_shoot_time > 0.1:
                    self.thumb_reset = True
                    self.shooting_detected = False

            # Detect shooting only if thumb was reset
            if thumb_velocity > velocity_threshold and thumb_middle_dist < distance_threshold:
                if self.thumb_reset and not self.shooting_detected and delta_time > 0.02:
                    self.shooting_detected = True
                    self.thumb_reset = False
                    self.last_shoot_time = current_time
                    self.previous_thumb_y = current_thumb_y
                    self.previous_time = current_time
                    return True

        self.previous_thumb_y = current_thumb_y
        self.previous_time = current_time
        return False

    def process_frame(self, frame: np.ndarray, debug_mode: bool = False) -> Tuple[np.ndarray, Optional[object], dict]:
        """Process frame for hand detection with optional preprocessing

        Args:
            frame: Input frame
            debug_mode: If True, return preprocessed frame for display
        """
        start_time = time.time()

        # Only copy frame if we need both versions
        if self.enable_preprocessing and not debug_mode:
            original_frame = frame.copy()
        else:
            original_frame = frame

        # Apply preprocessing if enabled
        if self.enable_preprocessing and self.preprocessor:
            # Get hand ROI from previous frame if available
            hand_roi = None
            if hasattr(self, "last_hand_landmarks") and self.last_hand_landmarks:
                hand_roi = self.preprocessor.get_hand_roi(self.last_hand_landmarks, frame.shape)

            # Preprocess frame
            preprocessed_frame = self.preprocessor.preprocess_frame(frame, hand_roi)
            self.preprocessing_time = (time.time() - start_time) * 1000  # ms

            # Use preprocessed frame for detection
            detection_frame = preprocessed_frame
        else:
            detection_frame = frame
            self.preprocessing_time = 0

        # Convert preprocessed frame to RGB for detection
        detection_start = time.time()
        detection_rgb = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)
        detection_rgb.flags.writeable = False
        results = self.hands.process(detection_rgb)

        # Choose which frame to return for display
        if debug_mode and self.enable_preprocessing:
            # In debug mode, show the preprocessed frame
            display_frame = detection_frame
        else:
            # Normal mode, show original frame
            display_frame = original_frame

        # Convert chosen frame for display
        image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        self.detection_time = (time.time() - detection_start) * 1000  # ms

        # Apply Kalman filtering if enabled
        if results.multi_hand_landmarks and self.enable_kalman and self.kalman_tracker:
            # Apply Kalman filtering to smooth landmarks
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                smoothed_landmarks = self.kalman_tracker.adaptive_update(
                    hand_landmarks, self.confidence_score, self.detection_mode
                )
                results.multi_hand_landmarks[i] = smoothed_landmarks
            self.last_hand_landmarks = results.multi_hand_landmarks[0]
        elif results.multi_hand_landmarks:
            self.last_hand_landmarks = results.multi_hand_landmarks[0]
        else:
            # Try to predict landmarks if Kalman is enabled and hand was recently lost
            if self.enable_kalman and self.kalman_tracker:
                predicted_landmarks = self.kalman_tracker.predict_landmarks()
                if predicted_landmarks:
                    # Create a results-like structure with predicted landmarks
                    if not results.multi_hand_landmarks:
                        results.multi_hand_landmarks = []
                    results.multi_hand_landmarks.append(predicted_landmarks)
                    self.last_hand_landmarks = predicted_landmarks
                else:
                    self.last_hand_landmarks = None
            else:
                self.last_hand_landmarks = None

        # Performance stats
        stats = {
            "preprocessing_ms": self.preprocessing_time,
            "detection_ms": self.detection_time,
            "total_ms": (time.time() - start_time) * 1000,
            "detection_mode": self.detection_mode,
            "confidence": self.confidence_score,
            "kalman_active": self.enable_kalman and self.kalman_tracker is not None,
            "kalman_tracking_confidence": self.kalman_tracker.tracking_confidence if self.kalman_tracker else 0,
        }

        return image, results, stats

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
        self.gesture_buffer.clear()
        self.last_hand_landmarks = None
        if self.kalman_tracker:
            self.kalman_tracker.reset()
