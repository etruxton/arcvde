"""
Test script for detecting blinking motion using MediaPipe Face Mesh.
This script analyzes eye aspect ratios and blink patterns to detect deliberate blinks (both eyes closing simultaneously).
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


class FramePreprocessor:
    """Handles frame preprocessing for better blink detection in various lighting conditions"""

    def __init__(self):
        # CLAHE for adaptive histogram equalization
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

        # Cache for performance
        self.gamma_table_cache = {}

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to improve eye detection in various lighting conditions

        Args:
            frame: Input BGR frame
        """
        # Create a copy to avoid modifying original
        processed = frame.copy()

        # Step 1: Convert to LAB color space for better lighting control
        lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Step 2: Apply adaptive histogram equalization to L channel
        l_channel = self.clahe.apply(l_channel)

        # Step 3: Merge channels back
        enhanced_lab = cv2.merge([l_channel, a_channel, b_channel])
        processed = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # Step 4: Apply bilateral filter to reduce noise while preserving edges
        processed = cv2.bilateralFilter(processed, 5, 50, 50)

        # Step 5: Adaptive gamma correction
        processed = self._apply_adaptive_gamma(processed)

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


class BlinkDetector:
    """Detects blinking motion by analyzing eye aspect ratios for both eyes closing simultaneously"""

    def __init__(self, enable_preprocessing=True):
        # Configuration
        self.enable_preprocessing = enable_preprocessing
        self.use_relative_detection = True  # Prefer relative detection

        # Initialize preprocessor
        self.preprocessor = FramePreprocessor() if enable_preprocessing else None

        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Eye landmark indices (MediaPipe Face Mesh)
        # Note: MediaPipe uses person's perspective, but with mirrored camera
        # Left eye landmarks (from person's perspective, appears on right side of mirrored image)
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        # Right eye landmarks (from person's perspective, appears on left side of mirrored image)
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

        # Key points for eye aspect ratio calculation
        self.LEFT_EYE_KEY = [33, 160, 158, 133, 153, 144]  # corners + top/bottom
        self.RIGHT_EYE_KEY = [362, 385, 387, 263, 373, 380]  # corners + top/bottom

        # Blink detection parameters - tuned for deliberate blinks vs automatic blinks
        self.ear_threshold = 0.25  # Fallback threshold for detecting closed eyes during blinks
        self.blink_frames_min = 2  # Minimum frames for a valid blink
        self.blink_frames_max = 15  # Maximum frames for a valid blink (deliberate blinks are usually quick)
        self.cooldown_time = 0.3  # Seconds between blink detections
        self.ear_history_size = 3  # Frames to keep for smoothing (less smoothing for quick response)

        # Relative blink detection parameters
        self.relative_threshold = 0.25  # Percentage drop from baseline to detect blink (25%)
        self.baseline_window = 15  # Frames to calculate running baseline
        self.min_baseline_frames = 10  # Minimum frames before relative detection kicks in

        # Glasses detection and adaptive thresholds
        self.glasses_mode = False
        self.baseline_ear_left = None
        self.baseline_ear_right = None
        self.adaptive_threshold_left = 0.25
        self.adaptive_threshold_right = 0.25
        self.calibration_frames = 0
        self.max_calibration_frames = 60  # 2 seconds at 30fps

        # Tracking state
        self.left_ear_history = deque(maxlen=self.ear_history_size)
        self.right_ear_history = deque(maxlen=self.ear_history_size)

        # Baseline tracking for relative blink detection
        self.left_ear_baseline_history = deque(maxlen=self.baseline_window)
        self.right_ear_baseline_history = deque(maxlen=self.baseline_window)

        self.both_closed_frames = 0
        self.both_open_frames = 0

        self.last_blink_time = 0
        self.blink_count = 0

        # Debug information
        self.debug_info = {
            "left_ear": 0,
            "right_ear": 0,
            "left_closed": False,
            "right_closed": False,
            "both_closed": False,
            "blink_detected": False,
            "last_blink": "Never",
            "glasses_mode": False,
            "calibrating": True,
            "left_threshold": 0.22,
            "right_threshold": 0.22,
        }

    def calculate_ear(self, eye_landmarks: List[Tuple[float, float]]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for given eye landmarks.
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        Where p1,p4 are horizontal corners and p2,p3,p5,p6 are vertical points
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
        """Extract eye landmark coordinates"""
        eye_points = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            eye_points.append((landmark.x, landmark.y))
        return eye_points

    def calibrate_baseline(self, left_ear: float, right_ear: float) -> bool:
        """Calibrate baseline EAR values for adaptive thresholds.

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

                # Update debug info
                self.debug_info["glasses_mode"] = self.glasses_mode
                self.debug_info["calibrating"] = False
                self.debug_info["left_threshold"] = self.adaptive_threshold_left
                self.debug_info["right_threshold"] = self.adaptive_threshold_right

                print("Calibration complete!")
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

    def detect_blink(self, face_landmarks) -> Tuple[bool, str]:
        """
        Detect blinking motion by analyzing eye aspect ratios for both eyes closing simultaneously.
        Returns (blink_detected, blink_type)
        """
        if face_landmarks is None:
            self.reset_state()
            return False, "None"

        current_time = time.time()

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

        # Update baseline history for relative detection (only when eyes are likely open)
        self.left_ear_baseline_history.append(left_ear_smooth)
        self.right_ear_baseline_history.append(right_ear_smooth)

        # Try relative blink detection first (better for angled faces)
        relative_blink_detected = self.detect_relative_blink(left_ear_smooth, right_ear_smooth)

        # Fallback to absolute threshold detection
        left_closed = left_ear_smooth < self.adaptive_threshold_left
        right_closed = right_ear_smooth < self.adaptive_threshold_right
        both_closed = left_closed and right_closed
        both_open = not left_closed and not right_closed

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

        # Track blink state - detect blinks immediately when condition is met
        if blink_condition:
            # Check if this is the START of a blink (transition from open to closed)
            if self.both_closed_frames == 0 and current_time - self.last_blink_time > self.cooldown_time:

                # Blink detected immediately!
                self.blink_count += 1
                self.last_blink_time = current_time
                self.debug_info["blink_detected"] = True
                self.debug_info["last_blink"] = f"{time.strftime('%H:%M:%S')} (Blink #{self.blink_count})"

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

    def reset_state(self):
        """Reset all tracking state"""
        self.left_ear_history.clear()
        self.right_ear_history.clear()
        self.left_ear_baseline_history.clear()
        self.right_ear_baseline_history.clear()
        self.both_closed_frames = 0
        self.both_open_frames = 0

    def recalibrate(self):
        """Reset calibration to start over"""
        self.baseline_ear_left = None
        self.baseline_ear_right = None
        self.calibration_frames = 0
        self.glasses_mode = False
        self.adaptive_threshold_left = 0.25
        self.adaptive_threshold_right = 0.25
        self.debug_info["calibrating"] = True
        self.debug_info["glasses_mode"] = False
        self.reset_state()
        print("Recalibration started - look directly at camera with both eyes open!")

    def draw_debug_info(self, image: np.ndarray, face_landmarks) -> np.ndarray:
        """Draw debug information on the image"""
        h, w, _ = image.shape

        # Draw calibration overlay if still calibrating
        if self.debug_info["calibrating"]:
            # Semi-transparent overlay
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 100, 255), -1)
            cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)

            # Calibration progress bar
            progress = self.calibration_frames / self.max_calibration_frames
            bar_width = w - 100
            bar_height = 20
            bar_x = 50
            bar_y = h // 2 - 60

            # Progress bar background
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
            # Progress bar fill
            fill_width = int(bar_width * progress)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), (0, 255, 0), -1)

            # Calibration text
            cv2.putText(
                image,
                "CALIBRATING - Look directly at camera",
                (w // 2 - 200, h // 2 - 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                image,
                f"Progress: {progress*100:.0f}%",
                (w // 2 - 50, h // 2 - 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            return image

        if face_landmarks is None:
            return image

        # Draw eye landmarks
        for idx in self.LEFT_EYE_KEY:
            landmark = face_landmarks.landmark[idx]
            x, y = int(landmark.x * w), int(landmark.y * h)
            color = (0, 255, 0) if not self.debug_info["left_closed"] else (0, 0, 255)
            cv2.circle(image, (x, y), 2, color, -1)

        for idx in self.RIGHT_EYE_KEY:
            landmark = face_landmarks.landmark[idx]
            x, y = int(landmark.x * w), int(landmark.y * h)
            color = (0, 255, 0) if not self.debug_info["right_closed"] else (0, 0, 255)
            cv2.circle(image, (x, y), 2, color, -1)

        # Draw eye bounding boxes
        self._draw_eye_box(image, face_landmarks, self.LEFT_EYE_KEY, self.debug_info["left_closed"])
        self._draw_eye_box(image, face_landmarks, self.RIGHT_EYE_KEY, self.debug_info["right_closed"])

        # Draw debug text
        debug_text = [
            f"Total Blinks: {self.blink_count}",
            f"Both Eyes Closed Frames: {self.both_closed_frames}",
            f"Detection Method: {self.debug_info.get('detection_method', 'absolute').upper()}",
            f"Left EAR: {self.debug_info['left_ear']:.3f} (Threshold: {self.debug_info['left_threshold']:.3f})",
            f"Right EAR: {self.debug_info['right_ear']:.3f} (Threshold: {self.debug_info['right_threshold']:.3f})",
            f"Left Eye: {'CLOSED' if self.debug_info['left_closed'] else 'OPEN'}",
            f"Right Eye: {'CLOSED' if self.debug_info['right_closed'] else 'OPEN'}",
            f"Both Eyes: {'CLOSED' if self.debug_info['both_closed'] else 'OPEN'} (Need both for blink!)",
        ]

        # Add relative detection info if available
        if "left_baseline" in self.debug_info:
            debug_text.extend(
                [
                    f"--- RELATIVE DETECTION ---",
                    f"Left Baseline: {self.debug_info['left_baseline']:.3f} | Drop: {self.debug_info['left_relative_drop']:.1%}",
                    f"Right Baseline: {self.debug_info['right_baseline']:.3f} | Drop: {self.debug_info['right_relative_drop']:.1%}",
                    f"Relative Blink: {'YES' if self.debug_info.get('relative_blink_detected', False) else 'NO'}",
                ]
            )

        debug_text.extend(
            [
                f"Glasses Mode: {'YES' if self.debug_info['glasses_mode'] else 'NO'} | Calibrating: {'YES' if self.debug_info['calibrating'] else 'NO'}",
                f"Last Blink: {self.debug_info['last_blink']}",
            ]
        )

        y_offset = 100  # Start below the status indicators
        for i, text in enumerate(debug_text):
            if i == 0:  # Total count
                color = (0, 255, 0)
            elif "CLOSED" in text and "Both Eyes: CLOSED" in text:  # Both eyes closed
                color = (255, 0, 255)  # Magenta for both closed
            elif "CLOSED" in text:  # Individual eye closed
                color = (0, 0, 255)
            elif "RELATIVE DETECTION" in text:  # Section header
                color = (255, 255, 0)  # Yellow for section headers
            else:
                color = (255, 255, 255)

            cv2.putText(image, text, (10, y_offset + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw instructions
        instructions = [
            "Controls:",
            "q: Quit | r: Reset | c: Recalibrate",
            "p: Toggle Preprocessing | s: Show Comparison",
            "m: Toggle Detection Method (Relative/Absolute)",
            "",
            "Tips:",
            "- Look at camera for 2 seconds to calibrate",
            "- Try looking left/right with relative detection",
        ]

        start_y = h - 180
        start_x = w - 300
        for i, instruction in enumerate(instructions):
            if instruction == "":  # Skip empty lines
                continue
            if instruction in ["Controls:", "Tips:"]:
                color = (0, 255, 255)  # Cyan for headers
            else:
                color = (200, 200, 200)  # Light gray for text
            cv2.putText(image, instruction, (start_x, start_y + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        return image

    def _draw_eye_box(self, image: np.ndarray, face_landmarks, eye_indices: List[int], is_closed: bool):
        """Draw bounding box around eye"""
        h, w, _ = image.shape

        # Get all eye points
        eye_points = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            eye_points.append([int(landmark.x * w), int(landmark.y * h)])

        eye_points = np.array(eye_points, dtype=np.int32)

        # Get bounding box
        x, y, box_w, box_h = cv2.boundingRect(eye_points)

        # Draw box
        color = (0, 0, 255) if is_closed else (0, 255, 0)
        thickness = 3 if is_closed else 1
        cv2.rectangle(image, (x - 5, y - 5), (x + box_w + 5, y + box_h + 5), color, thickness)


def main():
    """Main function to run blink detection test"""
    print("Blink Detection Test with Image Preprocessing")
    print("==============================================")
    print("Testing enhanced blink detection with image preprocessing for better reliability.")
    print("Preprocessing includes: brightness/contrast adjustment, sharpening, and noise reduction.")
    print("")
    print("Look directly at the camera and try blinking deliberately (both eyes at once)!")
    print("The algorithm detects when both eyes close and open simultaneously.")
    print("This should be more comfortable than winking for extended gameplay.")
    print()

    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Initialize blink detector with and without preprocessing for comparison
    print("Testing with image preprocessing enabled...")
    detector = BlinkDetector(enable_preprocessing=True)

    # Performance tracking
    fps_counter = 0
    fps_start_time = time.time()

    print("Camera opened successfully.")
    print("Controls:")
    print("- 'q': Quit")
    print("- 'r': Reset counts")
    print("- 'p': Toggle preprocessing on/off")
    print("- 's': Show/hide original vs processed frames")
    print("- 'm': Toggle detection method (relative/absolute)")
    print("- 'c': Recalibrate")

    show_comparison = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera")
            break

        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)

        # Apply preprocessing if enabled
        processed_frame = frame
        if detector.enable_preprocessing:
            processed_frame = detector.preprocessor.preprocess_frame(frame)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Process frame with MediaPipe Face Mesh
        results = detector.face_mesh.process(rgb_frame)

        # Convert back to BGR for OpenCV
        rgb_frame.flags.writeable = True
        frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        # Process face landmarks
        face_landmarks = None
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]  # Use first face

            # Detect blink
            blink_detected, blink_type = detector.detect_blink(face_landmarks)

            if blink_detected:
                print(f"BLINK DETECTED! Total: {detector.blink_count}")

                # Visual feedback for blink - green flash
                color = (0, 255, 0)  # Green for successful blink
                cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), color, 8)

                # Add text overlay
                cv2.putText(
                    frame,
                    f"BLINK #{detector.blink_count}!",
                    (frame.shape[1] // 2 - 150, frame.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    color,
                    3,
                )

        # Draw debug information
        frame = detector.draw_debug_info(frame, face_landmarks)

        # Calculate and display FPS
        fps_counter += 1
        if time.time() - fps_start_time >= 1.0:
            fps = fps_counter / (time.time() - fps_start_time)
            fps_counter = 0
            fps_start_time = time.time()
            cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Add preprocessing status indicator
        preprocess_status = "ON" if detector.enable_preprocessing else "OFF"
        preprocess_color = (0, 255, 0) if detector.enable_preprocessing else (0, 0, 255)
        cv2.putText(frame, f"Preprocess: {preprocess_status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, preprocess_color, 2)

        # Add detection method indicator
        method_status = "RELATIVE" if detector.use_relative_detection else "ABSOLUTE"
        method_color = (255, 255, 0) if detector.use_relative_detection else (255, 0, 255)
        cv2.putText(frame, f"Method: {method_status}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, method_color, 2)

        # Display frame(s)
        if show_comparison and detector.enable_preprocessing:
            # Show side-by-side comparison of original vs processed
            # Resize frames to fit side by side
            h, w = frame.shape[:2]
            display_width = w // 2
            display_height = int(h * (display_width / w))

            original_resized = cv2.resize(frame, (display_width, display_height))
            processed_resized = cv2.resize(processed_frame, (display_width, display_height))

            # Create comparison image
            comparison = np.hstack([original_resized, processed_resized])

            # Add labels
            cv2.putText(comparison, "Original", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(comparison, "Processed", (display_width + 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("Blink Detection Test - Comparison", comparison)
            cv2.imshow("Blink Detection Test", frame)
        else:
            cv2.imshow("Blink Detection Test", frame)

        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            detector.blink_count = 0
            detector.reset_state()
            print("Blink counts reset to 0")
        elif key == ord("c"):
            detector.recalibrate()
            print("Recalibrating thresholds...")
        elif key == ord("p"):
            detector.enable_preprocessing = not detector.enable_preprocessing
            status = "ENABLED" if detector.enable_preprocessing else "DISABLED"
            print(f"Preprocessing {status}")
        elif key == ord("s"):
            show_comparison = not show_comparison
            print(f"Frame comparison view: {'ON' if show_comparison else 'OFF'}")
        elif key == ord("m"):
            detector.use_relative_detection = not detector.use_relative_detection
            method = "RELATIVE" if detector.use_relative_detection else "ABSOLUTE"
            print(f"Detection method: {method}")
            detector.reset_state()  # Reset state when changing methods

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Print final statistics
    print("\nFinal Results:")
    print(f"Total blinks detected: {detector.blink_count}")
    print("Test completed.")


if __name__ == "__main__":
    main()
