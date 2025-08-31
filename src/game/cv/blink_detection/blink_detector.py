"""
Blink detection using MediaPipe Face Mesh with adaptive thresholds.
Optimized for gameplay with glasses support and personal calibration.
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


class BlinkDetector:
    """
    Detects blinking motion by analyzing eye aspect ratios with adaptive thresholds.

    Features:
    - Auto-calibration for personalized thresholds
    - Glasses detection and compensation
    - Individual eye threshold adaptation
    - Temporal smoothing for stability
    - Quick response for gaming
    """

    def __init__(self, calibration_time: float = 2.0, sensitivity: float = 1.0):
        """
        Initialize blink detector.

        Args:
            calibration_time: Seconds to spend calibrating (default 2.0)
            sensitivity: Detection sensitivity multiplier (default 1.0, higher = more sensitive)
        """
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.5
        )

        # Eye landmark indices (MediaPipe Face Mesh)
        self.LEFT_EYE_KEY = [33, 160, 158, 133, 153, 144]  # corners + top/bottom
        self.RIGHT_EYE_KEY = [362, 385, 387, 263, 373, 380]  # corners + top/bottom

        # Detection parameters - tuned for deliberate blinks vs automatic blinks
        self.ear_threshold = 0.25  # Threshold for detecting closed eyes during blinks
        self.blink_frames_min = 2  # Minimum frames for a valid blink
        self.blink_frames_max = 15  # Maximum frames for a valid blink (deliberate blinks are usually quick)
        self.cooldown_time = 0.1  # Seconds between blink detections (faster for rapid blinking)
        self.ear_history_size = 3  # Frames to keep for smoothing (less smoothing for quick response)

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

        self.both_closed_frames = 0
        self.both_open_frames = 0

        self.last_blink_time = 0
        self.blink_count = 0

        # Performance tracking
        self.last_detection_time = 0

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

        # Calculate EAR
        if horizontal == 0:
            return 0.3

        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    def extract_eye_landmarks(self, face_landmarks, eye_indices: List[int]) -> List[Tuple[float, float]]:
        """Extract eye landmark coordinates from face landmarks."""
        eye_points = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            eye_points.append((landmark.x, landmark.y))
        return eye_points

    def calibrate_baseline(self, left_ear: float, right_ear: float) -> bool:
        """
        Calibrate baseline EAR values for adaptive thresholds.

        Args:
            left_ear: Current left eye EAR value
            right_ear: Current right eye EAR value

        Returns:
            True if calibration is complete, False if still calibrating
        """
        if self.calibration_frames < self.max_calibration_frames:
            if self.baseline_ear_left is None:
                self.baseline_ear_left = left_ear
                self.baseline_ear_right = right_ear
            else:
                # Running average
                alpha = 0.1
                self.baseline_ear_left = alpha * left_ear + (1 - alpha) * self.baseline_ear_left
                self.baseline_ear_right = alpha * right_ear + (1 - alpha) * self.baseline_ear_right

            self.calibration_frames += 1

            if self.calibration_frames >= self.max_calibration_frames:
                # Set adaptive thresholds based on baseline - more sensitive for blinks
                self.adaptive_threshold_left = self.baseline_ear_left * 0.75  # 75% of baseline for deliberate blinks
                self.adaptive_threshold_right = self.baseline_ear_right * 0.75

                # Detect glasses mode if baseline EAR is unusually low
                avg_baseline = (self.baseline_ear_left + self.baseline_ear_right) / 2
                if avg_baseline < 0.22:
                    self.glasses_mode = True
                    # More lenient thresholds for glasses
                    self.adaptive_threshold_left = self.baseline_ear_left * 0.8
                    self.adaptive_threshold_right = self.baseline_ear_right * 0.8

                self.is_calibrated = True
                return True

        return False

    def detect_blink(self, face_landmarks) -> Tuple[bool, str]:
        """
        Detect blinking motion by analyzing eye aspect ratios with adaptive thresholds.

        Args:
            face_landmarks: MediaPipe face landmarks

        Returns:
            Tuple of (blink_detected: bool, blink_type: str)
            blink_type can be "Blink", "Calibrating", or "None"
        """
        if face_landmarks is None:
            return False, "None"

        current_time = time.time()
        self.last_detection_time = current_time

        # Extract eye landmarks
        left_eye_points = self.extract_eye_landmarks(face_landmarks, self.LEFT_EYE_KEY)
        right_eye_points = self.extract_eye_landmarks(face_landmarks, self.RIGHT_EYE_KEY)

        # Calculate Eye Aspect Ratios
        left_ear = self.calculate_ear(left_eye_points)
        right_ear = self.calculate_ear(right_eye_points)

        # Calibrate if still in calibration phase
        if self.calibration_frames < self.max_calibration_frames:
            self.calibrate_baseline(left_ear, right_ear)
            return False, "Calibrating"

        # Add to history for smoothing
        self.left_ear_history.append(left_ear)
        self.right_ear_history.append(right_ear)

        # Use smoothed values
        left_ear_smooth = np.mean(self.left_ear_history) if self.left_ear_history else left_ear
        right_ear_smooth = np.mean(self.right_ear_history) if self.right_ear_history else right_ear

        # Determine eye states using adaptive thresholds
        left_closed = left_ear_smooth < self.adaptive_threshold_left
        right_closed = right_ear_smooth < self.adaptive_threshold_right
        both_closed = left_closed and right_closed
        both_open = not left_closed and not right_closed

        # Track blink state - detect blinks immediately when both eyes close
        if both_closed:
            # Check if this is the START of a blink (transition from open to closed)
            if self.both_closed_frames == 0 and current_time - self.last_blink_time > self.cooldown_time:

                # Blink detected immediately!
                self.blink_count += 1
                self.last_blink_time = current_time

                self.both_closed_frames += 1
                self.both_open_frames = 0

                return True, "Blink"
            else:
                # Continue counting closed frames
                self.both_closed_frames += 1
                self.both_open_frames = 0

        elif both_open:
            # Eyes are open - reset closed counter but don't need to wait
            self.both_closed_frames = 0
            self.both_open_frames += 1

        else:
            # One eye open, one closed (partial blink or wink) - reset blink tracking
            self.both_closed_frames = 0
            self.both_open_frames = 0

        return False, "None"

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Process a frame for blink detection.

        Args:
            frame: Input BGR frame from camera

        Returns:
            Tuple of (blink_detected: bool, blink_type: str)
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Process frame with MediaPipe Face Mesh
        results = self.face_mesh.process(rgb_frame)

        # Process face landmarks
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]  # Use first face
            return self.detect_blink(face_landmarks)

        return False, "None"

    def recalibrate(self):
        """Reset calibration to start over."""
        self.baseline_ear_left = None
        self.baseline_ear_right = None
        self.calibration_frames = 0
        self.glasses_mode = False
        self.adaptive_threshold_left = 0.25
        self.adaptive_threshold_right = 0.25
        self.is_calibrated = False
        self.reset_tracking()

    def reset_tracking(self):
        """Reset tracking state without affecting calibration."""
        self.left_ear_history.clear()
        self.right_ear_history.clear()
        self.both_closed_frames = 0
        self.both_open_frames = 0

    def reset_counters(self):
        """Reset blink counters."""
        self.blink_count = 0

    def get_calibration_progress(self) -> float:
        """
        Get calibration progress as a percentage.

        Returns:
            Progress from 0.0 to 1.0
        """
        if self.is_calibrated:
            return 1.0
        return min(1.0, self.calibration_frames / self.max_calibration_frames)

    def get_status(self) -> dict:
        """
        Get current detector status and statistics.

        Returns:
            Dictionary with detector status information
        """
        return {
            "calibrated": self.is_calibrated,
            "calibration_progress": self.get_calibration_progress(),
            "glasses_mode": self.glasses_mode,
            "sensitivity": self.sensitivity,
            "blink_count": self.blink_count,
            "adaptive_threshold_left": self.adaptive_threshold_left,
            "adaptive_threshold_right": self.adaptive_threshold_right,
            "baseline_ear_left": self.baseline_ear_left,
            "baseline_ear_right": self.baseline_ear_right,
            "last_detection_time": self.last_detection_time,
        }
