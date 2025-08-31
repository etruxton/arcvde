"""
Test script for detecting finger snapping motion using MediaPipe hand tracking.
This script analyzes the rapid motion between thumb and middle finger to detect snaps.
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


class SnapDetector:
    """Detects finger snapping motion by analyzing thumb-middle finger interactions"""

    def __init__(self):
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7, min_tracking_confidence=0.6, max_num_hands=1, model_complexity=1
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Snap detection parameters
        self.snap_distance_threshold = 0.03  # Maximum distance for "contact"
        self.snap_velocity_threshold = 2.0  # Minimum separation velocity after contact
        self.contact_frames_required = 2  # Frames to confirm contact
        self.cooldown_time = 0.5  # Seconds between snap detections

        # Tracking state
        self.finger_distances = deque(maxlen=10)  # Distance history
        self.finger_velocities = deque(maxlen=5)  # Velocity history
        self.contact_frames = 0
        self.in_contact = False
        self.last_snap_time = 0
        self.previous_distance = None
        self.previous_time = None

        # Statistics
        self.snap_count = 0
        self.false_positives = 0

        # Debug visualization
        self.debug_info = {"distance": 0, "velocity": 0, "in_contact": False, "contact_frames": 0, "last_snap": "Never"}

    def calculate_distance(self, point1, point2) -> float:
        """Calculate Euclidean distance between two 3D points"""
        return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2 + (point1.z - point2.z) ** 2)

    def detect_snap(self, hand_landmarks) -> bool:
        """
        Detect snapping motion by analyzing thumb-middle finger dynamics.

        Returns True if a snap is detected.
        """
        if hand_landmarks is None:
            self.reset_state()
            return False

        current_time = time.time()

        # Get thumb tip and middle finger tip landmarks
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

        # Calculate current distance
        current_distance = self.calculate_distance(thumb_tip, middle_tip)
        self.finger_distances.append(current_distance)

        # Calculate velocity if we have previous data
        velocity = 0
        if self.previous_distance is not None and self.previous_time is not None:
            dt = current_time - self.previous_time
            if dt > 0:
                velocity = (current_distance - self.previous_distance) / dt
                self.finger_velocities.append(velocity)

        # Update debug info
        self.debug_info.update({"distance": current_distance, "velocity": velocity, "contact_frames": self.contact_frames})

        # Check for contact (fingers close together)
        if current_distance < self.snap_distance_threshold:
            self.contact_frames += 1
            if self.contact_frames >= self.contact_frames_required and not self.in_contact:
                self.in_contact = True
                self.debug_info["in_contact"] = True
        else:
            # Check if we were in contact and now separating rapidly
            if self.in_contact and velocity > self.snap_velocity_threshold:
                # Cooldown check
                if current_time - self.last_snap_time > self.cooldown_time:
                    # Additional validation: check recent contact history
                    if self._validate_snap_pattern():
                        self.snap_count += 1
                        self.last_snap_time = current_time
                        self.debug_info["last_snap"] = f"{time.strftime('%H:%M:%S')}"
                        self._reset_contact_state()
                        self.previous_distance = current_distance
                        self.previous_time = current_time
                        return True

            # Reset contact if fingers move apart without snapping
            if current_distance > self.snap_distance_threshold * 2:
                self._reset_contact_state()

        self.previous_distance = current_distance
        self.previous_time = current_time
        return False

    def _validate_snap_pattern(self) -> bool:
        """
        Validate that the motion pattern looks like a real snap.
        Checks for: close contact followed by rapid separation.
        """
        if len(self.finger_distances) < 5 or len(self.finger_velocities) < 3:
            return False

        # Check that we had sustained close contact recently
        recent_distances = list(self.finger_distances)[-5:]
        close_contact_count = sum(1 for d in recent_distances if d < self.snap_distance_threshold * 1.5)

        # Check for rapid positive velocity (separation)
        recent_velocities = list(self.finger_velocities)[-3:]
        high_velocity_count = sum(1 for v in recent_velocities if v > self.snap_velocity_threshold * 0.7)

        return close_contact_count >= 2 and high_velocity_count >= 1

    def _reset_contact_state(self):
        """Reset contact tracking state"""
        self.in_contact = False
        self.contact_frames = 0
        self.debug_info["in_contact"] = False

    def reset_state(self):
        """Reset all tracking state"""
        self.finger_distances.clear()
        self.finger_velocities.clear()
        self._reset_contact_state()
        self.previous_distance = None
        self.previous_time = None

    def draw_debug_info(self, image: np.ndarray, hand_landmarks) -> np.ndarray:
        """Draw debug information on the image"""
        if hand_landmarks is None:
            return image

        h, w, _ = image.shape

        # Get landmark positions
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

        # Convert to pixel coordinates
        thumb_pos = (int(thumb_tip.x * w), int(thumb_tip.y * h))
        middle_pos = (int(middle_tip.x * w), int(middle_tip.y * h))

        # Draw connection line
        color = (0, 255, 0) if self.debug_info["in_contact"] else (255, 0, 0)
        thickness = 3 if self.debug_info["in_contact"] else 1
        cv2.line(image, thumb_pos, middle_pos, color, thickness)

        # Draw finger points
        cv2.circle(image, thumb_pos, 8, (255, 0, 255), -1)  # Magenta for thumb
        cv2.circle(image, middle_pos, 8, (0, 255, 255), -1)  # Cyan for middle

        # Draw debug text
        debug_text = [
            f"Snap Count: {self.snap_count}",
            f"Distance: {self.debug_info['distance']:.4f}",
            f"Velocity: {self.debug_info['velocity']:.2f}",
            f"Contact: {'YES' if self.debug_info['in_contact'] else 'NO'}",
            f"Contact Frames: {self.debug_info['contact_frames']}",
            f"Last Snap: {self.debug_info['last_snap']}",
        ]

        y_offset = 30
        for i, text in enumerate(debug_text):
            color = (0, 255, 0) if i == 0 else (255, 255, 255)  # Green for count, white for others
            cv2.putText(image, text, (10, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw instructions
        instructions = [
            "Instructions:",
            "- Position thumb and middle finger close together",
            "- Make a quick snapping motion",
            "- Press 'q' to quit, 'r' to reset count",
        ]

        start_y = h - 120
        for i, instruction in enumerate(instructions):
            color = (0, 255, 255) if i == 0 else (200, 200, 200)
            cv2.putText(image, instruction, (10, start_y + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return image


def main():
    """Main function to run snap detection test"""
    print("Snap Detection Test")
    print("==================")
    print("Position your hand in front of the camera and try snapping your fingers!")
    print("The algorithm looks for rapid thumb-middle finger contact and separation.")
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

    # Initialize snap detector
    detector = SnapDetector()

    # Performance tracking
    fps_counter = 0
    fps_start_time = time.time()

    print("Camera opened successfully. Press 'q' to quit, 'r' to reset snap count.")

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

        # Process frame with MediaPipe
        results = detector.hands.process(rgb_frame)

        # Convert back to BGR for OpenCV
        rgb_frame.flags.writeable = True
        frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        # Process hand landmarks
        hand_landmarks = None
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]  # Use first hand

            # Draw hand landmarks
            detector.mp_drawing.draw_landmarks(frame, hand_landmarks, detector.mp_hands.HAND_CONNECTIONS)

            # Detect snap
            if detector.detect_snap(hand_landmarks):
                print(f"SNAP DETECTED! Count: {detector.snap_count}")
                # Visual feedback for snap
                cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 10)

        # Draw debug information
        frame = detector.draw_debug_info(frame, hand_landmarks)

        # Calculate and display FPS
        fps_counter += 1
        if time.time() - fps_start_time >= 1.0:
            fps = fps_counter / (time.time() - fps_start_time)
            fps_counter = 0
            fps_start_time = time.time()
            cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Display frame
        cv2.imshow("Snap Detection Test", frame)

        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            detector.snap_count = 0
            detector.reset_state()
            print("Snap count reset to 0")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Print final statistics
    print("\nFinal Results:")
    print(f"Total snaps detected: {detector.snap_count}")
    print("Test completed.")


if __name__ == "__main__":
    main()
