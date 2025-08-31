"""
Enhanced blink detection using MediaPipe Face Mesh with face region processing.

This module provides improved blink detection with:
- Face region cropping for better accuracy and performance
- Coordinate transformation for accurate eye highlighting on original camera view
- Adaptive thresholds with personal calibration
- Relative detection for angled faces
- Optional preprocessing for challenging lighting conditions

The face region processing approach:
1. Detects face in full frame using MediaPipe Face Detection
2. Crops face region with padding for focused processing  
3. Applies preprocessing only to the smaller face region (faster)
4. Runs blink detection on face region (more accurate)
5. Transforms landmarks back to full frame coordinates for display

This provides significant performance and accuracy improvements over full-frame processing.
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
from .face_region_detector import FaceRegionDetector


class EnhancedBlinkDetector:
    """
    Enhanced blink detection with face region processing and adaptive thresholds.

    Features:
    - Face region cropping for improved accuracy and performance  
    - Coordinate transformation for accurate eye highlighting
    - Auto-calibration for personalized thresholds
    - Glasses detection and compensation
    - Individual eye threshold adaptation
    - Relative blink detection for angled faces
    - Optional frame preprocessing for challenging lighting
    - Temporal smoothing for stability
    - Quick response optimized for gaming
    
    Face Region Processing Benefits:
    - Faster processing (smaller region to analyze)
    - Better accuracy (reduces false positives from background)
    - Improved lighting handling (focused preprocessing)
    - Maintains display accuracy via coordinate transformation
    """

    def __init__(self, calibration_time: float = 1.0, sensitivity: float = 1.0, enable_preprocessing: bool = False, enable_face_cropping: bool = True):
        """
        Initialize enhanced blink detector.

        Args:
            calibration_time: Seconds to spend calibrating (default 1.0)
            sensitivity: Detection sensitivity multiplier (default 1.0, higher = more sensitive)
            enable_preprocessing: Enable frame preprocessing for better detection (default False)
            enable_face_cropping: Enable face region cropping for improved accuracy (default True)
        """
        # Configuration
        self.enable_preprocessing = enable_preprocessing
        self.enable_face_cropping = enable_face_cropping
        self.use_relative_detection = True  # Prefer relative detection for angled faces

        # Initialize preprocessor (needed for face cropping or preprocessing)
        self.preprocessor = FramePreprocessor() if (enable_preprocessing or enable_face_cropping) else None
        self.face_detector = FaceRegionDetector() if enable_face_cropping else None
        
        # Current face region tracking for display purposes
        self.current_face_bbox = None
        self.current_face_shape = None

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

        # Calibration settings - use frame-based like the working test
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
        Calibrate baseline EAR values and adaptive thresholds using frame-based calibration.
        Uses the same logic as the working test file.

        Returns True when calibration is complete.
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
                # Set adaptive thresholds based on baseline - same as test file
                self.adaptive_threshold_left = self.baseline_ear_left * 0.75  # 75% of baseline
                self.adaptive_threshold_right = self.baseline_ear_right * 0.75

                # Detect glasses mode if baseline EAR is unusually low
                avg_baseline = (self.baseline_ear_left + self.baseline_ear_right) / 2
                if avg_baseline < 0.22:
                    self.glasses_mode = True
                    # More lenient thresholds for glasses
                    self.adaptive_threshold_left = self.baseline_ear_left * 0.8
                    self.adaptive_threshold_right = self.baseline_ear_right * 0.8

                # Update debug info
                self.debug_info["glasses_mode"] = self.glasses_mode
                self.debug_info["calibrating"] = False
                self.is_calibrated = True

                processing_mode = "face_region" if self.current_face_bbox else "full_frame"
                print(f"Calibration complete! Processing mode: {processing_mode}")
                print(f"Baseline - Left: {self.baseline_ear_left:.3f}, Right: {self.baseline_ear_right:.3f}")
                print(f"Thresholds - Left: {self.adaptive_threshold_left:.3f}, Right: {self.adaptive_threshold_right:.3f}")
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
        Process frame and detect blinks with optional face region cropping and preprocessing.
        
        Face region cropping improves accuracy by:
        1. Processing only the relevant face area (faster and more focused)
        2. Reducing false positives from background elements
        3. Better handling of lighting variations across the frame

        Args:
            frame: Input BGR frame from camera

        Returns:
            Tuple of (blink_detected: bool, blink_type: str)
        """
        self.last_detection_time = time.time()

        # Smart Face Region Processing (like the working test)
        # Try face region first, fall back to full frame if it fails
        face_region = None
        face_bbox = None
        face_landmarks = None
        processing_mode = "full_frame"
        
        if self.enable_face_cropping and self.preprocessor:
            face_region, face_bbox = self.preprocessor.extract_face_region(frame)
            
        if face_region is not None:
            # Try face region processing first
            self.current_face_bbox = face_bbox
            
            # Apply preprocessing to face region if enabled
            if self.enable_preprocessing:
                processed_face = self.preprocessor.preprocess_face_region(face_region)
            else:
                processed_face = face_region
                
            # Convert face region BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(processed_face, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # Try Face Mesh on face region
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                processing_mode = "face_region"
                # Debug: Show success
                if self.calibration_frames == 0:
                    print("Face region processing successful!")
        
        if face_landmarks is None:
            # Fallback to full frame processing (like the test)
            self.current_face_bbox = None
            
            # Apply preprocessing to full frame if enabled
            if self.enable_preprocessing and self.preprocessor:
                processed_frame = self.preprocessor.preprocess_frame(frame)
            else:
                processed_frame = frame
            
            # Convert full frame BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # Process full frame with MediaPipe Face Mesh
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                processing_mode = "full_frame"
            else:
                self.reset_tracking()
                return False, "None"
        
        # Debug: Print when we first detect face landmarks for calibration
        if self.calibration_frames == 0:
            print("Face landmarks detected! Starting calibration...")

        # Extract eye landmarks
        left_eye_points = self.extract_eye_landmarks(face_landmarks, self.LEFT_EYE_KEY)
        right_eye_points = self.extract_eye_landmarks(face_landmarks, self.RIGHT_EYE_KEY)

        # Calculate Eye Aspect Ratios
        left_ear = self.calculate_ear(left_eye_points)
        right_ear = self.calculate_ear(right_eye_points)

        # Calibrate if still in calibration phase
        if self.calibration_frames < self.max_calibration_frames:
            calibration_complete = self.calibrate_baseline(left_ear, right_ear)
            self.debug_info["calibrating"] = not calibration_complete
            return False, "Calibrating"
        else:
            # Ensure calibrating flag is off after calibration
            self.debug_info["calibrating"] = False

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

        # Consistent detection method - stick to one approach to prevent double bouncing
        if self.use_relative_detection and relative_blink_detected:
            blink_condition = True
            detection_method = "relative"
        elif not self.use_relative_detection and both_closed:
            blink_condition = True
            detection_method = "absolute"
        else:
            blink_condition = False
            detection_method = "none"

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
            
            # Debug: Show detection method and processing mode (less verbose)
            if self.blink_count <= 5:  # Only show first 5 blinks
                print(f"BLINK DETECTED #{self.blink_count}! Method: {detection_method}, Processing: {processing_mode}")
            
            return True, "Blink"

        return False, "None"

    def get_status(self) -> dict:
        """
        Get current detection status and statistics.

        Returns:
            Dictionary with detection status, calibration info, and statistics
        """
        if self.calibration_frames < self.max_calibration_frames:
            calibration_progress = self.calibration_frames / self.max_calibration_frames
        else:
            calibration_progress = 1.0

        status = {
            "calibrated": self.is_calibrated,
            "calibration_progress": calibration_progress,
            "glasses_mode": self.glasses_mode,
            "blink_count": self.blink_count,
            "adaptive_threshold_left": self.adaptive_threshold_left,
            "adaptive_threshold_right": self.adaptive_threshold_right,
            "detection_method": self.debug_info.get("detection_method", "absolute"),
            "preprocessing_enabled": self.enable_preprocessing,
            "face_cropping_enabled": self.enable_face_cropping,
            "relative_detection_enabled": self.use_relative_detection,
        }
        
        # Add face detection statistics if available
        if self.face_detector:
            face_stats = self.face_detector.get_statistics()
            status["face_detection_stats"] = face_stats
            
        return status

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
        Get face landmarks for display overlay with proper coordinate transformation.
        
        When face region cropping is enabled, landmarks are detected on the cropped face
        region but need to be transformed back to full frame coordinates for accurate
        display overlay on the original camera view.

        Args:
            frame: Original BGR frame

        Returns:
            Face landmarks transformed to full frame coordinates, or None if no face detected
        """
        # Smart approach: Try face region first, fall back to full frame (independent of detection)
        if self.enable_face_cropping and self.preprocessor:
            face_region, face_bbox = self.preprocessor.extract_face_region(frame)
            
            if face_region is not None:
                # Try face region processing for display
                if self.enable_preprocessing:
                    processing_frame = self.preprocessor.preprocess_face_region(face_region)
                else:
                    processing_frame = face_region
                    
                rgb_face = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB)
                rgb_face.flags.writeable = False
                results = self.face_mesh.process(rgb_face)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # Transform landmarks from face region coordinates to full frame
                    if not self.face_detector:
                        self.face_detector = FaceRegionDetector()
                    transformed_landmarks = self.face_detector.transform_landmarks_to_full_frame(
                        face_landmarks, face_bbox, face_region.shape, frame.shape
                    )
                    return transformed_landmarks
        
        # Fallback to full frame processing for display
        if self.enable_preprocessing and self.preprocessor:
            processing_frame = self.preprocessor.preprocess_frame(frame)
        else:
            processing_frame = frame
            
        rgb_frame = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0]
            
        return None
    
    def get_eye_landmarks_for_display(self, face_landmarks, frame_shape):
        """
        Extract eye landmark points for display overlay in pixel coordinates.
        
        Args:
            face_landmarks: MediaPipe face landmarks (from get_face_landmarks_for_display)
            frame_shape: (height, width) of the display frame
            
        Returns:
            Tuple of (left_eye_points, right_eye_points) as lists of (x, y) pixel coordinates
        """
        if face_landmarks is None:
            return [], []
            
        h, w = frame_shape[:2]
            
        # Convert normalized coordinates to pixel coordinates
        left_eye_points = []
        for idx in self.LEFT_EYE_KEY:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                left_eye_points.append((int(landmark.x * w), int(landmark.y * h)))
        
        right_eye_points = []
        for idx in self.RIGHT_EYE_KEY:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                right_eye_points.append((int(landmark.x * w), int(landmark.y * h)))
        
        return left_eye_points, right_eye_points
    
    def draw_eye_overlay(self, frame, face_landmarks):
        """
        Draw eye landmark overlay on frame (for compatibility with existing game code).
        
        Args:
            frame: BGR frame to draw on
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            Frame with eye overlay drawn
        """
        if face_landmarks is None:
            return frame
            
        h, w = frame.shape[:2]
        debug_info = self.get_debug_info()
        
        # Draw eye landmarks
        for idx in self.LEFT_EYE_KEY:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                x, y = int(landmark.x * w), int(landmark.y * h)
                color = (0, 255, 0) if not debug_info.get("left_closed", False) else (0, 0, 255)
                cv2.circle(frame, (x, y), 2, color, -1)

        for idx in self.RIGHT_EYE_KEY:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                x, y = int(landmark.x * w), int(landmark.y * h)
                color = (0, 255, 0) if not debug_info.get("right_closed", False) else (0, 0, 255)
                cv2.circle(frame, (x, y), 2, color, -1)
                
        return frame
    
    def get_debug_info(self) -> dict:
        """
        Get current debug information for display.
        
        Returns:
            Dictionary with current EAR values, thresholds, and detection state
        """
        return self.debug_info.copy()
    
    def get_face_region_info(self) -> dict:
        """
        Get current face region information for display purposes.
        
        Returns:
            Dictionary with face region bbox and statistics
        """
        info = {
            "face_bbox": self.current_face_bbox,
            "face_cropping_enabled": self.enable_face_cropping
        }
        
        if self.face_detector:
            stats = self.face_detector.get_statistics()
            info.update(stats)
            
        return info
