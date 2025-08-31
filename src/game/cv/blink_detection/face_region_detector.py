"""
Face region detection module for focused blink detection preprocessing.

Provides face detection and region extraction functionality to improve 
blink detection accuracy by processing only the face region.
"""

# Standard library imports
from typing import Optional, Tuple

# Third-party imports
import cv2
import mediapipe as mp
import numpy as np


class FaceRegionDetector:
    """
    Detects and extracts face regions from frames for focused processing.
    
    Features:
    - MediaPipe face detection with confidence filtering
    - Face region tracking with temporal stability
    - Configurable padding around detected faces
    - Fallback to previous face position when detection fails
    - Coordinate transformation utilities for landmarks
    """
    
    def __init__(self, confidence_threshold: float = 0.5, max_lost_frames: int = 5):
        """
        Initialize face region detector.
        
        Args:
            confidence_threshold: Minimum confidence for face detection (0.0-1.0)
            max_lost_frames: Maximum frames to use cached face position when detection fails
        """
        # Face detection setup
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=confidence_threshold
        )
        
        # Tracking parameters
        self.max_lost_frames = max_lost_frames
        
        # Face region tracking state
        self.last_face_bbox = None
        self.face_not_found_frames = 0
        
        # Statistics for performance monitoring
        self.stats = {
            "regions_processed": 0,
            "full_frame_fallbacks": 0,
            "detection_success_rate": 0.0,
            "avg_region_size_percentage": 0.0
        }
    
    def extract_face_region(self, frame: np.ndarray, padding_factor: float = 0.3) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """
        Extract face region from frame for focused processing.
        
        Args:
            frame: Input BGR frame
            padding_factor: Factor to expand face bounding box (0.3 = 30% padding)
            
        Returns:
            Tuple of:
            - face_region: Cropped face image (None if no face found)
            - face_bbox: (x, y, width, height) for coordinate transformation (None if no face found)
        """
        h, w = frame.shape[:2]
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Detect faces
        results = self.face_detection.process(rgb_frame)
        
        if results.detections:
            # Use first detection (highest confidence)
            detection = results.detections[0]
            confidence = detection.score[0] if detection.score else 0.0
            
            # Debug: Print face detection success (first few times)
            if self.stats["regions_processed"] < 3:  # First few times
                print(f"Face region processing active! Confidence: {confidence:.2f}")
            
            # Get relative bounding box
            bbox = detection.location_data.relative_bounding_box
            
            # Convert to pixel coordinates
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            # Add padding around face region
            padding_x = int(width * padding_factor)
            padding_y = int(height * padding_factor)
            
            # Expand bounding box with padding, ensuring it stays within frame bounds
            x_padded = max(0, x - padding_x)
            y_padded = max(0, y - padding_y)
            width_padded = min(w - x_padded, width + 2 * padding_x)
            height_padded = min(h - y_padded, height + 2 * padding_y)
            
            # Extract face region
            face_region = frame[y_padded:y_padded + height_padded, x_padded:x_padded + width_padded]
            
            # Update tracking state
            self.last_face_bbox = (x_padded, y_padded, width_padded, height_padded)
            self.face_not_found_frames = 0
            
            # Update statistics
            self.stats["regions_processed"] += 1
            region_pixels = width_padded * height_padded
            total_pixels = w * h
            self.stats["avg_region_size_percentage"] = (region_pixels / total_pixels) * 100
            
            return face_region, self.last_face_bbox
        else:
            # No face detected - use last known position if recent enough
            self.face_not_found_frames += 1
            
            if self.last_face_bbox and self.face_not_found_frames <= self.max_lost_frames:
                # Use cached face region from last known position
                x, y, width, height = self.last_face_bbox
                if x + width <= w and y + height <= h and x >= 0 and y >= 0:
                    face_region = frame[y:y + height, x:x + width]
                    self.stats["regions_processed"] += 1
                    return face_region, self.last_face_bbox
            
            # No face found and no recent cache available
            self.stats["full_frame_fallbacks"] += 1
            
            # Debug: Print face detection failure (first few times)
            if self.stats["full_frame_fallbacks"] <= 3:  # First few failures
                print(f"Face detection lost - fallback to full frame (failure #{self.stats['full_frame_fallbacks']})")
            
            return None, None
    
    def transform_landmarks_to_full_frame(self, landmarks, face_bbox: Tuple[int, int, int, int], 
                                        face_shape: Tuple[int, int], full_frame_shape: Tuple[int, int]):
        """
        Transform landmarks from face region coordinates to full frame coordinates.
        
        This is essential for accurate eye highlighting when using face region preprocessing.
        The landmarks detected on the cropped face region need to be mapped back to the
        original full frame coordinates for proper display overlay.
        
        Args:
            landmarks: MediaPipe landmarks from face region processing
            face_bbox: (x, y, width, height) of face region in full frame
            face_shape: (height, width) of face region
            full_frame_shape: (height, width) of full frame
            
        Returns:
            Transformed landmarks for drawing on full frame
        """
        import copy
        
        # Create a deep copy to avoid modifying original landmarks
        transformed = copy.deepcopy(landmarks)
        
        bbox_x, bbox_y, bbox_w, bbox_h = face_bbox
        face_h, face_w = face_shape[:2]
        full_frame_h, full_frame_w = full_frame_shape[:2]
        
        # Transform each landmark coordinate
        for landmark in transformed.landmark:
            # Convert from face region normalized coordinates to face region pixels
            face_pixel_x = landmark.x * face_w
            face_pixel_y = landmark.y * face_h
            
            # Transform to full frame pixel coordinates
            full_frame_pixel_x = bbox_x + face_pixel_x
            full_frame_pixel_y = bbox_y + face_pixel_y
            
            # Convert back to full frame normalized coordinates
            landmark.x = full_frame_pixel_x / full_frame_w
            landmark.y = full_frame_pixel_y / full_frame_h
            
        return transformed
    
    def get_face_bbox_for_display(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Get current face bounding box for display overlay.
        
        Returns:
            (x, y, width, height) of face region or None if no face tracked
        """
        return self.last_face_bbox
    
    def get_statistics(self) -> dict:
        """
        Get face detection statistics.
        
        Returns:
            Dictionary with detection statistics and performance metrics
        """
        total_attempts = self.stats["regions_processed"] + self.stats["full_frame_fallbacks"]
        if total_attempts > 0:
            self.stats["detection_success_rate"] = (self.stats["regions_processed"] / total_attempts) * 100
        else:
            self.stats["detection_success_rate"] = 0.0
            
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset detection statistics."""
        self.stats = {
            "regions_processed": 0,
            "full_frame_fallbacks": 0,
            "detection_success_rate": 0.0,
            "avg_region_size_percentage": 0.0
        }
    
    def reset_tracking(self):
        """Reset face tracking state."""
        self.last_face_bbox = None
        self.face_not_found_frames = 0