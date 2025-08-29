"""
Kalman Filter for hand position tracking
Smooths hand positions and predicts movement for better clap detection
"""

import numpy as np
from typing import Tuple, Optional


class KalmanTracker:
    """2D Kalman filter for tracking hand positions"""
    
    def __init__(self, process_noise: float = 1e-3, measurement_noise: float = 1e-1):
        """
        Initialize Kalman filter for 2D position tracking
        
        Args:
            process_noise: How much we expect the true position to change
            measurement_noise: How much noise we expect in measurements
        """
        # State vector: [x, y, vx, vy] (position and velocity)
        self.state = np.zeros(4)
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, 1, 0],  # x = x + vx*dt
            [0, 1, 0, 1],  # y = y + vy*dt  
            [0, 0, 1, 0],  # vx = vx
            [0, 0, 0, 1]   # vy = vy
        ])
        
        # Measurement matrix (we observe position only)
        self.H = np.array([
            [1, 0, 0, 0],  # measure x
            [0, 1, 0, 0]   # measure y
        ])
        
        # Process noise covariance
        self.Q = np.eye(4) * process_noise
        
        # Measurement noise covariance  
        self.R = np.eye(2) * measurement_noise
        
        # Error covariance matrix
        self.P = np.eye(4) * 1000  # Start with high uncertainty
        
        # Track if initialized
        self.initialized = False
    
    def predict(self, dt: float = 1.0) -> np.ndarray:
        """
        Predict next state
        
        Args:
            dt: Time step
            
        Returns:
            Predicted state [x, y, vx, vy]
        """
        if not self.initialized:
            return self.state
            
        # Update time step in transition matrix
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        
        # Predict state
        self.state = self.F @ self.state
        
        # Predict error covariance
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.state
    
    def update(self, measurement: Tuple[float, float]) -> np.ndarray:
        """
        Update with new measurement
        
        Args:
            measurement: (x, y) position measurement
            
        Returns:
            Updated state [x, y, vx, vy]
        """
        z = np.array([measurement[0], measurement[1]])
        
        if not self.initialized:
            # Initialize state with first measurement
            self.state[0:2] = z
            self.state[2:4] = 0  # Zero initial velocity
            self.initialized = True
            return self.state
        
        # Innovation (measurement residual)
        y = z - self.H @ self.state
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update error covariance
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
        return self.state
    
    def get_position(self) -> Tuple[float, float]:
        """Get current estimated position"""
        return (self.state[0], self.state[1])
    
    def get_velocity(self) -> Tuple[float, float]:
        """Get current estimated velocity"""
        return (self.state[2], self.state[3])
    
    def get_speed(self) -> float:
        """Get current speed magnitude"""
        vx, vy = self.get_velocity()
        return np.sqrt(vx**2 + vy**2)


class HandTracker:
    """Tracks both hands using Kalman filters"""
    
    def __init__(self):
        self.left_hand_tracker = KalmanTracker()
        self.right_hand_tracker = KalmanTracker()
        self.last_update_time = None
    
    def update(self, left_hand_pos: Optional[Tuple[float, float]], 
               right_hand_pos: Optional[Tuple[float, float]], 
               current_time: float) -> dict:
        """
        Update hand tracking
        
        Args:
            left_hand_pos: (x, y) position of left hand, None if not detected
            right_hand_pos: (x, y) position of right hand, None if not detected
            current_time: Current timestamp
            
        Returns:
            Dictionary with tracking info
        """
        dt = 1.0
        if self.last_update_time is not None:
            dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Predict next positions
        self.left_hand_tracker.predict(dt)
        self.right_hand_tracker.predict(dt)
        
        tracking_info = {
            'left_hand_detected': left_hand_pos is not None,
            'right_hand_detected': right_hand_pos is not None,
            'left_hand_predicted': False,
            'right_hand_predicted': False
        }
        
        # Update with measurements if available
        if left_hand_pos is not None:
            self.left_hand_tracker.update(left_hand_pos)
        else:
            tracking_info['left_hand_predicted'] = True
            
        if right_hand_pos is not None:
            self.right_hand_tracker.update(right_hand_pos)
        else:
            tracking_info['right_hand_predicted'] = True
        
        # Get current estimates
        tracking_info['left_hand_pos'] = self.left_hand_tracker.get_position()
        tracking_info['right_hand_pos'] = self.right_hand_tracker.get_position()
        tracking_info['left_hand_velocity'] = self.left_hand_tracker.get_velocity()
        tracking_info['right_hand_velocity'] = self.right_hand_tracker.get_velocity()
        tracking_info['left_hand_speed'] = self.left_hand_tracker.get_speed()
        tracking_info['right_hand_speed'] = self.right_hand_tracker.get_speed()
        
        return tracking_info
    
    def get_hand_distance(self) -> float:
        """Get distance between tracked hand positions"""
        left_pos = self.left_hand_tracker.get_position()
        right_pos = self.right_hand_tracker.get_position()
        
        return np.sqrt((left_pos[0] - right_pos[0])**2 + (left_pos[1] - right_pos[1])**2)
    
    def get_approach_velocity(self) -> float:
        """Get velocity of hands approaching each other (positive = approaching)"""
        left_pos = self.left_hand_tracker.get_position()
        right_pos = self.right_hand_tracker.get_position()
        left_vel = self.left_hand_tracker.get_velocity()
        right_vel = self.right_hand_tracker.get_velocity()
        
        # Vector from left to right hand
        hand_vector = np.array([right_pos[0] - left_pos[0], right_pos[1] - left_pos[1]])
        hand_distance = np.linalg.norm(hand_vector)
        
        if hand_distance < 1e-6:
            return 0.0
        
        # Unit vector pointing from left to right
        hand_unit = hand_vector / hand_distance
        
        # Relative velocity of right hand with respect to left hand
        relative_vel = np.array([right_vel[0] - left_vel[0], right_vel[1] - left_vel[1]])
        
        # Project relative velocity onto hand direction
        # Negative means hands are approaching
        approach_velocity = -np.dot(relative_vel, hand_unit)
        
        return approach_velocity