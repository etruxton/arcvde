"""
Test script for detecting winking motion using MediaPipe Face Mesh.
This script analyzes eye aspect ratios and blink patterns to detect deliberate winks.
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


class WinkDetector:
    """Detects winking motion by analyzing eye aspect ratios and blink patterns"""

    def __init__(self):
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Eye landmark indices (MediaPipe Face Mesh)
        # Left eye landmarks (from person's perspective)
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        # Right eye landmarks (from person's perspective)
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

        # Key points for eye aspect ratio calculation
        self.LEFT_EYE_KEY = [33, 160, 158, 133, 153, 144]  # corners + top/bottom
        self.RIGHT_EYE_KEY = [362, 385, 387, 263, 373, 380]  # corners + top/bottom

        # Wink detection parameters
        self.ear_threshold = 0.25  # Eye Aspect Ratio threshold for closed eye (raised for easier detection)
        self.wink_frames_min = 2  # Minimum frames for a valid wink (reduced for quicker detection)
        self.wink_frames_max = 20  # Maximum frames for a valid wink (increased for glasses)
        self.cooldown_time = 0.25  # Seconds between wink detections (reduced)
        self.ear_history_size = 8  # Frames to keep for smoothing (reduced for responsiveness)

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

        self.left_closed_frames = 0
        self.right_closed_frames = 0
        self.both_closed_frames = 0

        self.last_wink_time = 0
        self.wink_count = 0
        self.left_wink_count = 0
        self.right_wink_count = 0

        # Debug information
        self.debug_info = {
            "left_ear": 0,
            "right_ear": 0,
            "left_closed": False,
            "right_closed": False,
            "wink_type": "None",
            "last_wink": "Never",
            "glasses_mode": False,
            "calibrating": True,
            "left_threshold": 0.25,
            "right_threshold": 0.25,
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

    def calibrate_baseline(self, left_ear: float, right_ear: float):
        """Calibrate baseline EAR values for adaptive thresholds"""
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
                # Set adaptive thresholds based on baseline
                # For glasses, people tend to have lower baseline EAR
                self.adaptive_threshold_left = self.baseline_ear_left * 0.7  # 70% of baseline
                self.adaptive_threshold_right = self.baseline_ear_right * 0.7

                # Detect glasses mode if baseline EAR is unusually low
                avg_baseline = (self.baseline_ear_left + self.baseline_ear_right) / 2
                if avg_baseline < 0.22:
                    self.glasses_mode = True
                    # Even more lenient thresholds for glasses
                    self.adaptive_threshold_left = self.baseline_ear_left * 0.75
                    self.adaptive_threshold_right = self.baseline_ear_right * 0.75

                # Update debug info
                self.debug_info["glasses_mode"] = self.glasses_mode
                self.debug_info["calibrating"] = False
                self.debug_info["left_threshold"] = self.adaptive_threshold_left
                self.debug_info["right_threshold"] = self.adaptive_threshold_right

                print(f"Calibration complete! Glasses mode: {self.glasses_mode}")
                print(f"Baseline EAR - Left: {self.baseline_ear_left:.3f}, Right: {self.baseline_ear_right:.3f}")
                print(
                    f"Adaptive thresholds - Left: {self.adaptive_threshold_left:.3f}, Right: {self.adaptive_threshold_right:.3f}"
                )

    def detect_wink(self, face_landmarks) -> Tuple[bool, str]:
        """
        Detect winking motion by analyzing eye aspect ratios with adaptive thresholds.
        Returns (wink_detected, wink_type)
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
            self.calibrate_baseline(left_ear, right_ear)
            self.debug_info["calibrating"] = True
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
        both_open = not left_closed and not right_closed
        both_closed = left_closed and right_closed

        # Update debug info
        self.debug_info.update(
            {
                "left_ear": left_ear_smooth,
                "right_ear": right_ear_smooth,
                "left_closed": left_closed,
                "right_closed": right_closed,
            }
        )

        # Track closed frame counts
        if left_closed and not right_closed:  # Left wink
            self.left_closed_frames += 1
            self.right_closed_frames = 0
            self.both_closed_frames = 0
        elif right_closed and not left_closed:  # Right wink
            self.right_closed_frames += 1
            self.left_closed_frames = 0
            self.both_closed_frames = 0
        elif both_closed:  # Both eyes closed (blink)
            self.both_closed_frames += 1
            self.left_closed_frames = 0
            self.right_closed_frames = 0
        else:  # Both eyes open
            # Check if we just completed a wink
            wink_detected = False
            wink_type = "None"

            # Check for left wink completion
            if (
                self.left_closed_frames >= self.wink_frames_min
                and self.left_closed_frames <= self.wink_frames_max
                and current_time - self.last_wink_time > self.cooldown_time
            ):
                wink_detected = True
                wink_type = "Left"
                self.left_wink_count += 1

            # Check for right wink completion
            elif (
                self.right_closed_frames >= self.wink_frames_min
                and self.right_closed_frames <= self.wink_frames_max
                and current_time - self.last_wink_time > self.cooldown_time
            ):
                wink_detected = True
                wink_type = "Right"
                self.right_wink_count += 1

            # Reset frame counters
            self.left_closed_frames = 0
            self.right_closed_frames = 0
            self.both_closed_frames = 0

            if wink_detected:
                self.wink_count += 1
                self.last_wink_time = current_time
                self.debug_info["wink_type"] = wink_type
                self.debug_info["last_wink"] = f"{time.strftime('%H:%M:%S')} ({wink_type})"
                return True, wink_type

        return False, "None"

    def reset_state(self):
        """Reset all tracking state"""
        self.left_ear_history.clear()
        self.right_ear_history.clear()
        self.left_closed_frames = 0
        self.right_closed_frames = 0
        self.both_closed_frames = 0

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
        if face_landmarks is None:
            return image

        h, w, _ = image.shape

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
            f"Total Winks: {self.wink_count}",
            f"Left Winks: {self.left_wink_count} | Right Winks: {self.right_wink_count}",
            f"Left EAR: {self.debug_info['left_ear']:.3f} (Threshold: {self.debug_info['left_threshold']:.3f})",
            f"Right EAR: {self.debug_info['right_ear']:.3f} (Threshold: {self.debug_info['right_threshold']:.3f})",
            f"Left Eye: {'CLOSED' if self.debug_info['left_closed'] else 'OPEN'}",
            f"Right Eye: {'CLOSED' if self.debug_info['right_closed'] else 'OPEN'}",
            f"Glasses Mode: {'YES' if self.debug_info['glasses_mode'] else 'NO'} | Calibrating: {'YES' if self.debug_info['calibrating'] else 'NO'}",
            f"Last Wink: {self.debug_info['last_wink']}",
        ]

        y_offset = 30
        for i, text in enumerate(debug_text):
            if i == 0:  # Total count
                color = (0, 255, 0)
            elif i == 1:  # Left/Right counts
                color = (255, 255, 0)
            elif "CLOSED" in text:  # Eye status
                color = (0, 0, 255)
            else:
                color = (255, 255, 255)

            cv2.putText(image, text, (10, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw instructions
        instructions = [
            "Instructions:",
            "- Look directly at camera for 2 seconds to calibrate",
            "- Wink left or right eye (gentle winks work better now!)",
            "- Glasses wearers: automatic detection & adaptive thresholds",
            "- Press 'q' to quit, 'r' to reset, 'c' to recalibrate",
        ]

        start_y = h - 140
        for i, instruction in enumerate(instructions):
            color = (0, 255, 255) if i == 0 else (200, 200, 200)
            cv2.putText(image, instruction, (10, start_y + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

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
    """Main function to run wink detection test"""
    print("Wink Detection Test")
    print("==================")
    print("Look directly at the camera and try winking your left or right eye!")
    print("The algorithm uses Eye Aspect Ratio (EAR) to detect when one eye closes while the other stays open.")
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

    # Initialize wink detector
    detector = WinkDetector()

    # Performance tracking
    fps_counter = 0
    fps_start_time = time.time()

    print("Camera opened successfully. Press 'q' to quit, 'r' to reset counts.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera")
            break

        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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

            # Detect wink
            wink_detected, wink_type = detector.detect_wink(face_landmarks)

            if wink_detected:
                print(f"{wink_type.upper()} WINK DETECTED! Total: {detector.wink_count}")

                # Visual feedback for wink
                color = (255, 0, 0) if wink_type == "Left" else (0, 0, 255)  # Blue for left, Red for right
                cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), color, 8)

                # Add text overlay
                cv2.putText(
                    frame,
                    f"{wink_type.upper()} WINK!",
                    (frame.shape[1] // 2 - 100, frame.shape[0] // 2),
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

        # Display frame
        cv2.imshow("Wink Detection Test", frame)

        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            detector.wink_count = 0
            detector.left_wink_count = 0
            detector.right_wink_count = 0
            detector.reset_state()
            print("Wink counts reset to 0")
        elif key == ord("c"):
            detector.recalibrate()
            print("Recalibrating thresholds...")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Print final statistics
    print(f"\nFinal Results:")
    print(f"Total winks detected: {detector.wink_count}")
    print(f"Left winks: {detector.left_wink_count}")
    print(f"Right winks: {detector.right_wink_count}")
    print("Test completed.")


if __name__ == "__main__":
    main()
