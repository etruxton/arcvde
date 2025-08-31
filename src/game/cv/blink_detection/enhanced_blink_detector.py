"""
Enhanced blink detection using MediaPipe Face Mesh with adaptive thresholds and relative detection.

This module provides improved blink detection that works better at angles and in various
lighting conditions using preprocessing and relative detection algorithms.
"""

# Standard library imports
import math
import time
from collections import deque
from typing import List, Optional, Tuple

# Third-party imports
import cv2
import mediapipe as mp
import numpy as np

# Local imports
from .frame_preprocessor import FramePreprocessor


class EnhancedBlinkDetector:
    """
    Enhanced blink detection with relative detection and preprocessing support.

    Features:
    - Auto-calibration for personalized thresholds
    - Glasses detection and compensation
    - Individual eye threshold adaptation
    - Relative blink detection for angled faces
    - Optional frame preprocessing for challenging lighting
    - Temporal smoothing for stability
    - Quick response optimized for gaming
    """

    def __init__(self, calibration_time: float = 2.0, sensitivity: float = 1.0, enable_preprocessing: bool = False):
        """
        Initialize enhanced blink detector.

        Args:
            calibration_time: Seconds to spend calibrating (default 2.0)
            sensitivity: Detection sensitivity multiplier (default 1.0, higher = more sensitive)
            enable_preprocessing: Enable frame preprocessing for better detection (default False)
        """
        # Configuration
        self.enable_preprocessing = enable_preprocessing
        self.use_relative_detection = True  # Prefer relative detection for angled faces

        # Initialize preprocessor if enabled
        self.preprocessor = FramePreprocessor() if enable_preprocessing else None

        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.5
        )

        # Eye landmark indices (MediaPipe Face Mesh)
        self.LEFT_EYE_KEY = [33, 160, 158, 133, 153, 144]  # corners + top/bottom
        self.RIGHT_EYE_KEY = [362, 385, 387, 263, 373, 380]  # corners + top/bottom

        # Detection parameters
        self.ear_threshold = 0.25  # Fallback threshold for absolute detection
        self.blink_frames_min = 2  # Minimum frames for a valid blink
        self.blink_frames_max = 15  # Maximum frames for a valid blink
        self.cooldown_time = 0.1  # Seconds between blink detections
        self.ear_history_size = 3  # Frames to keep for smoothing

        # Relative detection parameters
        self.relative_threshold = 0.25  # Percentage drop from baseline to detect blink (25%)
        self.baseline_window = 15  # Frames to calculate running baseline
        self.min_baseline_frames = 10  # Minimum frames before relative detection kicks in

        # Calibration settings
        self.max_calibration_frames = int(30 * calibration_time)  # 30 FPS assumption
        self.sensitivity = sensitivity

        # Adaptive thresholds
        self.glasses_mode = False
        self.baseline_ear_left = None
        self.baseline_ear_right = None
        self.adaptive_threshold_left = 0.25
        self.adaptive_threshold_right = 0.25
        self.calibration_frames = 0
        self.is_calibrated = False

        # Tracking state
        self.left_ear_history = deque(maxlen=self.ear_history_size)
        self.right_ear_history = deque(maxlen=self.ear_history_size)

        # Baseline tracking for relative detection
        self.left_ear_baseline_history = deque(maxlen=self.baseline_window)
        self.right_ear_baseline_history = deque(maxlen=self.baseline_window)

        self.both_closed_frames = 0
        self.both_open_frames = 0
        self.last_blink_time = 0
        self.blink_count = 0

        # Performance tracking
        self.last_detection_time = 0

        # Debug information for status
        self.debug_info = {
            "left_ear": 0,
            "right_ear": 0,
            "left_closed": False,
            "right_closed": False,
            "both_closed": False,
            "blink_detected": False,
            "detection_method": "absolute",
            "glasses_mode": False,
            "calibrating": True,
        }

    def calculate_ear(self, eye_landmarks: List[Tuple[float, float]]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for given eye landmarks.

        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        Where p1,p4 are horizontal corners and p2,p3,p5,p6 are vertical points

        Args:
            eye_landmarks: List of (x, y) coordinates for eye landmarks

        Returns:
            Eye aspect ratio (higher = more open, lower = more closed)
        """
        if len(eye_landmarks) < 6:
            return 0.3  # Default "open" value

        # Calculate vertical distances
        vertical_1 = math.sqrt(
            (eye_landmarks[1][0] - eye_landmarks[5][0]) ** 2 + (eye_landmarks[1][1] - eye_landmarks[5][1]) ** 2
        )
        vertical_2 = math.sqrt(
            (eye_landmarks[2][0] - eye_landmarks[4][0]) ** 2 + (eye_landmarks[2][1] - eye_landmarks[4][1]) ** 2
        )

        # Calculate horizontal distance
        horizontal = math.sqrt(
            (eye_landmarks[0][0] - eye_landmarks[3][0]) ** 2 + (eye_landmarks[0][1] - eye_landmarks[3][1]) ** 2
        )

        if horizontal == 0:
            return 0.3

        # Calculate EAR
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    def extract_eye_landmarks(self, face_landmarks, eye_indices: List[int]) -> List[Tuple[float, float]]:
        """Extract eye landmark coordinates from face landmarks."""
        eye_points = []
        for idx in eye_indices:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                eye_points.append((landmark.x, landmark.y))
        return eye_points

    def calibrate_baseline(self, left_ear: float, right_ear: float) -> bool:
        """
        Calibrate baseline EAR values and adaptive thresholds.

        Returns True when calibration is complete.
        """
        self.calibration_frames += 1

        # Initialize baseline values
        if self.baseline_ear_left is None:
            self.baseline_ear_left = left_ear
            self.baseline_ear_right = right_ear
        else:
            # Running average for more stable baseline
            alpha = 0.1
            self.baseline_ear_left = alpha * left_ear + (1 - alpha) * self.baseline_ear_left
            self.baseline_ear_right = alpha * right_ear + (1 - alpha) * self.baseline_ear_right

        # Check for glasses (different EAR patterns)
        if self.calibration_frames > 30:  # After some samples
            # Glasses typically show lower and more variable EAR values
            if self.baseline_ear_left < 0.23 or self.baseline_ear_right < 0.23:
                self.glasses_mode = True

        # Complete calibration
        if self.calibration_frames >= self.max_calibration_frames:
            self.is_calibrated = True

            # Set adaptive thresholds based on baseline and sensitivity
            base_threshold = 0.7 if self.glasses_mode else 0.8
            self.adaptive_threshold_left = self.baseline_ear_left * base_threshold * self.sensitivity
            self.adaptive_threshold_right = self.baseline_ear_right * base_threshold * self.sensitivity

            # Ensure thresholds are reasonable
            self.adaptive_threshold_left = max(0.15, min(0.35, self.adaptive_threshold_left))
            self.adaptive_threshold_right = max(0.15, min(0.35, self.adaptive_threshold_right))

            # Update debug info
            self.debug_info["glasses_mode"] = self.glasses_mode
            self.debug_info["calibrating"] = False

            return True

        return False

    def detect_relative_blink(self, left_ear: float, right_ear: float) -> bool:
        """
        Detect blinks using relative changes from baseline EAR values.
        This works better when face is at an angle to the camera.

        Returns True if both eyes show relative drop indicating a blink.
        """
        # Need sufficient baseline data
        if len(self.left_ear_baseline_history) < self.min_baseline_frames:
            return False

        if len(self.right_ear_baseline_history) < self.min_baseline_frames:
            return False

        # Calculate current baseline (average of recent open-eye values)
        # Exclude the lowest values to avoid including blinks in baseline
        left_baseline_values = sorted(list(self.left_ear_baseline_history))
        right_baseline_values = sorted(list(self.right_ear_baseline_history))

        # Use top 60% of values for baseline (exclude potential blinks)
        baseline_start_idx = int(len(left_baseline_values) * 0.4)
        left_baseline = np.mean(left_baseline_values[baseline_start_idx:])
        right_baseline = np.mean(right_baseline_values[baseline_start_idx:])

        # Calculate relative drops from baseline
        left_drop = (left_baseline - left_ear) / left_baseline if left_baseline > 0 else 0
        right_drop = (right_baseline - right_ear) / right_baseline if right_baseline > 0 else 0

        # Both eyes must show significant relative drop
        left_blink = left_drop > self.relative_threshold
        right_blink = right_drop > self.relative_threshold

        # Store debug info
        self.debug_info["left_baseline"] = left_baseline
        self.debug_info["right_baseline"] = right_baseline
        self.debug_info["left_relative_drop"] = left_drop
        self.debug_info["right_relative_drop"] = right_drop
        self.debug_info["relative_blink_detected"] = left_blink and right_blink

        return left_blink and right_blink

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Process frame and detect blinks with optional preprocessing.

        Args:
            frame: Input BGR frame from camera

        Returns:
            Tuple of (blink_detected: bool, blink_type: str)
        """
        self.last_detection_time = time.time()

        # Apply preprocessing if enabled (for detection only, not display)
        processed_frame = frame
        if self.enable_preprocessing and self.preprocessor:
            processed_frame = self.preprocessor.preprocess_frame(frame)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Process frame with MediaPipe Face Mesh
        results = self.face_mesh.process(rgb_frame)

        # Process face landmarks
        if not results.multi_face_landmarks:
            self.reset_tracking()
            return False, "None"

        face_landmarks = results.multi_face_landmarks[0]  # Use first face

        # Extract eye landmarks
        left_eye_points = self.extract_eye_landmarks(face_landmarks, self.LEFT_EYE_KEY)
        right_eye_points = self.extract_eye_landmarks(face_landmarks, self.RIGHT_EYE_KEY)

        # Calculate Eye Aspect Ratios
        left_ear = self.calculate_ear(left_eye_points)
        right_ear = self.calculate_ear(right_eye_points)

        # Calibrate if still in calibration phase
        if not self.is_calibrated:
            self.calibrate_baseline(left_ear, right_ear)
            self.debug_info["calibrating"] = True
            return False, "Calibrating"

        # Add to history for smoothing
        self.left_ear_history.append(left_ear)
        self.right_ear_history.append(right_ear)

        # Use smoothed values
        left_ear_smooth = np.mean(self.left_ear_history) if self.left_ear_history else left_ear
        right_ear_smooth = np.mean(self.right_ear_history) if self.right_ear_history else right_ear

        # Update baseline history for relative detection
        self.left_ear_baseline_history.append(left_ear_smooth)
        self.right_ear_baseline_history.append(right_ear_smooth)

        # Try relative blink detection first (better for angled faces)
        relative_blink_detected = self.detect_relative_blink(left_ear_smooth, right_ear_smooth)

        # Fallback to absolute threshold detection
        left_closed = left_ear_smooth < self.adaptive_threshold_left
        right_closed = right_ear_smooth < self.adaptive_threshold_right
        both_closed = left_closed and right_closed

        # Use detection method based on settings
        if self.use_relative_detection and relative_blink_detected:
            blink_condition = True
            detection_method = "relative"
        else:
            blink_condition = both_closed
            detection_method = "absolute"

        # Update debug info
        self.debug_info.update(
            {
                "left_ear": left_ear_smooth,
                "right_ear": right_ear_smooth,
                "left_closed": left_closed,
                "right_closed": right_closed,
                "both_closed": both_closed,
                "blink_detected": False,
                "detection_method": detection_method,
            }
        )

        # Detect blinks with cooldown
        current_time = time.time()
        if blink_condition and current_time - self.last_blink_time > self.cooldown_time:
            self.blink_count += 1
            self.last_blink_time = current_time
            self.debug_info["blink_detected"] = True
            return True, "Blink"

        return False, "None"

    def get_status(self) -> dict:
        """
        Get current detection status and statistics.

        Returns:
            Dictionary with detection status, calibration info, and statistics
        """
        if not self.is_calibrated:
            calibration_progress = min(1.0, self.calibration_frames / self.max_calibration_frames)
        else:
            calibration_progress = 1.0

        return {
            "calibrated": self.is_calibrated,
            "calibration_progress": calibration_progress,
            "glasses_mode": self.glasses_mode,
            "blink_count": self.blink_count,
            "adaptive_threshold_left": self.adaptive_threshold_left,
            "adaptive_threshold_right": self.adaptive_threshold_right,
            "detection_method": self.debug_info.get("detection_method", "absolute"),
            "preprocessing_enabled": self.enable_preprocessing,
            "relative_detection_enabled": self.use_relative_detection,
        }

    def reset_counters(self):
        """Reset blink counters."""
        self.blink_count = 0
        self.last_blink_time = 0

    def reset_tracking(self):
        """Reset all tracking state."""
        self.left_ear_history.clear()
        self.right_ear_history.clear()
        self.left_ear_baseline_history.clear()
        self.right_ear_baseline_history.clear()
        self.both_closed_frames = 0
        self.both_open_frames = 0

    def recalibrate(self):
        """Reset calibration to start over."""
        self.baseline_ear_left = None
        self.baseline_ear_right = None
        self.calibration_frames = 0
        self.is_calibrated = False
        self.glasses_mode = False
        self.adaptive_threshold_left = 0.25
        self.adaptive_threshold_right = 0.25
        self.debug_info["calibrating"] = True
        self.debug_info["glasses_mode"] = False
        self.reset_tracking()

    def get_face_landmarks_for_display(self, frame: np.ndarray):
        """
        Get face landmarks for display overlay (uses original frame, not preprocessed).

        Args:
            frame: Original BGR frame

        Returns:
            Face landmarks or None if no face detected
        """
        # Convert BGR to RGB for MediaPipe (use original frame for display)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Process frame with MediaPipe Face Mesh
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0]
        return None
