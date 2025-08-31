"""
Kalman filter implementation for smooth hand landmark tracking
"""

# Standard library imports
from typing import Dict, Optional, Tuple

# Third-party imports
import cv2
import numpy as np


class LandmarkKalmanFilter:
    """Kalman filter for a single 3D landmark"""

    def __init__(self, process_noise=0.03, measurement_noise=0.1):
        # State vector: [x, y, z, vx, vy, vz] (position and velocity)
        self.kalman = cv2.KalmanFilter(6, 3)

        # Assuming ~30 FPS, dt = 0.033 seconds
        dt = 0.033

        # Transition matrix (constant velocity model)
        self.kalman.transitionMatrix = np.array(
            [
                [1, 0, 0, dt, 0, 0],
                [0, 1, 0, 0, dt, 0],
                [0, 0, 1, 0, 0, dt],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ],
            dtype=np.float32,
        )

        # Measurement matrix (we only measure position)
        self.kalman.measurementMatrix = np.array(
            [[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]], dtype=np.float32
        )

        # Process noise covariance
        self.kalman.processNoiseCov = np.eye(6, dtype=np.float32) * process_noise

        # Measurement noise covariance
        self.kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * measurement_noise

        # Initial state covariance
        self.kalman.errorCovPost = np.eye(6, dtype=np.float32)

        # Track if filter is initialized
        self.initialized = False
        self.lost_frames = 0
        self.max_lost_frames = 3

    def update(self, measurement: np.ndarray, confidence: float = 1.0) -> np.ndarray:
        """
        Update Kalman filter with new measurement

        Args:
            measurement: [x, y, z] position
            confidence: Detection confidence (0-1), affects noise parameters

        Returns:
            Filtered [x, y, z] position
        """
        if not self.initialized:
            # Initialize state with first measurement
            self.kalman.statePre = np.array(
                [measurement[0], measurement[1], measurement[2], 0, 0, 0], dtype=np.float32  # Initial velocity is zero
            )
            self.kalman.statePost = self.kalman.statePre.copy()
            self.initialized = True
            self.lost_frames = 0
            return measurement

        # Adjust measurement noise based on confidence
        # Lower confidence = higher noise
        adaptive_noise = 0.1 / max(confidence, 0.1)
        self.kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * adaptive_noise

        # Predict next state
        prediction = self.kalman.predict()

        # Correct with measurement
        measurement_mat = np.array(measurement, dtype=np.float32).reshape(3, 1)
        self.kalman.correct(measurement_mat)

        # Return filtered position
        state = self.kalman.statePost
        self.lost_frames = 0
        return np.array([state[0], state[1], state[2]]).flatten()

    def predict_only(self) -> Optional[np.ndarray]:
        """
        Predict position without measurement (when landmark is lost)

        Returns:
            Predicted [x, y, z] position or None if lost for too long
        """
        if not self.initialized:
            return None

        self.lost_frames += 1
        if self.lost_frames > self.max_lost_frames:
            # Lost for too long, reset filter
            self.initialized = False
            return None

        # Predict next state without correction
        prediction = self.kalman.predict()

        # Return predicted position
        return np.array([prediction[0], prediction[1], prediction[2]]).flatten()

    def reset(self):
        """Reset the Kalman filter"""
        self.initialized = False
        self.lost_frames = 0
        self.kalman.errorCovPost = np.eye(6, dtype=np.float32)


class HandKalmanTracker:
    """Manages Kalman filters for all hand landmarks"""

    def __init__(self, process_noise=0.03, measurement_noise=0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        # Dictionary to store Kalman filters for each landmark
        self.filters: Dict[int, LandmarkKalmanFilter] = {}

        # Key landmarks to track (optimize by only tracking important ones)
        self.key_landmarks = [
            0,  # WRIST
            4,  # THUMB_TIP
            8,  # INDEX_FINGER_TIP
            12,  # MIDDLE_FINGER_TIP
            16,  # RING_FINGER_TIP
            20,  # PINKY_TIP
            5,  # INDEX_FINGER_MCP
            9,  # MIDDLE_FINGER_MCP
            13,  # RING_FINGER_MCP
            17,  # PINKY_MCP
            6,  # INDEX_FINGER_PIP
            10,  # MIDDLE_FINGER_PIP
            14,  # RING_FINGER_PIP
            18,  # PINKY_PIP
        ]

        # Initialize filters for key landmarks
        for landmark_id in self.key_landmarks:
            self.filters[landmark_id] = LandmarkKalmanFilter(process_noise, measurement_noise)

        # Store last known good hand landmarks
        self.last_landmarks = None
        self.tracking_confidence = 1.0

    def update_landmarks(self, hand_landmarks, detection_confidence: float = 1.0):
        """
        Update all landmark positions with Kalman filtering

        Args:
            hand_landmarks: MediaPipe hand landmarks
            detection_confidence: Overall hand detection confidence

        Returns:
            Smoothed hand landmarks
        """
        if hand_landmarks is None:
            # No detection, use prediction only
            return self.predict_landmarks()

        self.tracking_confidence = detection_confidence

        # Update each tracked landmark
        for landmark_id in self.key_landmarks:
            if landmark_id >= len(hand_landmarks.landmark):
                continue

            landmark = hand_landmarks.landmark[landmark_id]
            measurement = np.array([landmark.x, landmark.y, landmark.z])

            # Update Kalman filter
            if landmark_id in self.filters:
                filtered_pos = self.filters[landmark_id].update(measurement, detection_confidence)

                # Apply smoothed position back to landmark
                hand_landmarks.landmark[landmark_id].x = filtered_pos[0]
                hand_landmarks.landmark[landmark_id].y = filtered_pos[1]
                hand_landmarks.landmark[landmark_id].z = filtered_pos[2]

        self.last_landmarks = hand_landmarks
        return hand_landmarks

    def predict_landmarks(self):
        """
        Predict landmark positions when hand is temporarily lost

        Returns:
            Predicted hand landmarks or None if lost for too long
        """
        if self.last_landmarks is None:
            return None

        # Check if we can still predict
        can_predict = False
        for filter in self.filters.values():
            if filter.initialized and filter.lost_frames < filter.max_lost_frames:
                can_predict = True
                break

        if not can_predict:
            self.reset()
            return None

        # Create predicted landmarks from last known positions
        predicted_landmarks = self.last_landmarks

        # Update positions with predictions
        for landmark_id, filter in self.filters.items():
            if landmark_id >= len(predicted_landmarks.landmark):
                continue

            predicted_pos = filter.predict_only()
            if predicted_pos is not None:
                predicted_landmarks.landmark[landmark_id].x = predicted_pos[0]
                predicted_landmarks.landmark[landmark_id].y = predicted_pos[1]
                predicted_landmarks.landmark[landmark_id].z = predicted_pos[2]

        # Reduce tracking confidence for predictions
        self.tracking_confidence *= 0.8

        return predicted_landmarks

    def reset(self):
        """Reset all Kalman filters"""
        for filter in self.filters.values():
            filter.reset()
        self.last_landmarks = None
        self.tracking_confidence = 1.0

    def get_smoothness_factor(self) -> float:
        """
        Get current smoothness factor based on tracking quality

        Returns:
            Smoothness factor (0-1) where 1 is maximum smoothing
        """
        # More smoothing when confidence is low
        return 1.0 - self.tracking_confidence

    def adaptive_update(self, hand_landmarks, detection_confidence: float, detection_mode: str = "standard"):
        """
        Adaptively update filters based on detection mode and confidence

        Args:
            hand_landmarks: MediaPipe hand landmarks
            detection_confidence: Overall detection confidence
            detection_mode: Current detection mode (affects filter parameters)

        Returns:
            Smoothed hand landmarks
        """
        # Adjust filter parameters based on detection mode
        if detection_mode == "angles" or detection_mode == "angles_only":
            # More aggressive filtering for angle-based detection
            process_noise = 0.02
            measurement_noise = 0.15
        elif detection_mode == "depth" or detection_mode == "wrist_angle":
            # Moderate filtering for alternative detection modes
            process_noise = 0.03
            measurement_noise = 0.12
        else:  # standard or none
            # Conservative filtering for standard detection
            process_noise = 0.04
            measurement_noise = 0.08

        # Update filter parameters if they've changed significantly
        if abs(self.process_noise - process_noise) > 0.01:
            self.process_noise = process_noise
            self.measurement_noise = measurement_noise
            # Update all filters with new parameters
            for filter in self.filters.values():
                filter.kalman.processNoiseCov = np.eye(6, dtype=np.float32) * process_noise
                filter.kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * measurement_noise

        # Perform update
        return self.update_landmarks(hand_landmarks, detection_confidence)
