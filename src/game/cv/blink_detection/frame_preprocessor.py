"""
Frame preprocessing module for enhanced blink detection.

Provides image enhancement techniques to improve blink detection reliability
in various lighting conditions, similar to those used in finger gun detection.
"""

# Standard library imports
from typing import Dict, Optional, Tuple

# Third-party imports
import cv2
import mediapipe as mp
import numpy as np


class FramePreprocessor:
    """
    Handles frame preprocessing for better blink detection in various lighting conditions.

    Features:
    - LAB color space conversion for better lighting control
    - CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Bilateral filtering for noise reduction while preserving edges
    - Adaptive gamma correction based on image brightness
    - Cached gamma tables for performance
    """

    def __init__(self):
        # CLAHE for adaptive histogram equalization
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

        # Cache for performance
        self.gamma_table_cache: Dict[float, np.ndarray] = {}
        
        # Face detection for region cropping (same as test file)
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.7
        )
        
        # Face region tracking
        self.last_face_bbox = None
        self.face_not_found_frames = 0
        self.max_face_lost_frames = 5

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to improve eye detection in various lighting conditions.

        Processing pipeline:
        1. Convert BGR to LAB color space
        2. Apply CLAHE to L channel for contrast enhancement
        3. Convert back to BGR
        4. Apply bilateral filter for noise reduction
        5. Apply adaptive gamma correction based on brightness

        Args:
            frame: Input BGR frame

        Returns:
            Preprocessed BGR frame
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
        """
        Apply gamma correction based on image brightness.

        Gamma values:
        - Very dark (< 80): gamma 1.8 (brighten significantly)
        - Dark (< 100): gamma 1.5 (brighten moderately)
        - Normal: gamma 1.0 (no change)
        - Bright (> 150): gamma 0.8 (darken slightly)
        - Very bright (> 170): gamma 0.6 (darken significantly)

        Args:
            image: Input BGR image

        Returns:
            Gamma-corrected BGR image
        """
        # Calculate mean brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)

        # Determine gamma value based on brightness
        if mean_brightness < 80:  # Very dark
            gamma = 1.8
        elif mean_brightness < 100:  # Dark
            gamma = 1.5
        elif mean_brightness > 170:  # Very bright
            gamma = 0.6
        elif mean_brightness > 150:  # Bright
            gamma = 0.8
        else:  # Normal lighting
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

    def extract_face_region(self, frame: np.ndarray, padding_factor: float = 0.3) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """
        Extract face region from frame for focused processing
        
        Args:
            frame: Input BGR frame
            padding_factor: Factor to expand face bounding box (0.3 = 30% padding)
            
        Returns:
            face_region: Cropped face image (None if no face found)
            face_bbox: (x, y, width, height) for coordinate transformation (None if no face found)
        """
        h, w = frame.shape[:2]
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Detect faces
        results = self.face_detection.process(rgb_frame)
        
        if results.detections:
            # Use first detection
            detection = results.detections[0]
            
            # Get relative bounding box
            bbox = detection.location_data.relative_bounding_box
            
            # Convert to pixel coordinates
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            # Add padding
            padding_x = int(width * padding_factor)
            padding_y = int(height * padding_factor)
            
            # Expand bounding box with padding
            x_padded = max(0, x - padding_x)
            y_padded = max(0, y - padding_y)
            width_padded = min(w - x_padded, width + 2 * padding_x)
            height_padded = min(h - y_padded, height + 2 * padding_y)
            
            # Extract face region
            face_region = frame[y_padded:y_padded + height_padded, x_padded:x_padded + width_padded]
            
            # Update tracking
            self.last_face_bbox = (x_padded, y_padded, width_padded, height_padded)
            self.face_not_found_frames = 0
            
            return face_region, self.last_face_bbox
        else:
            # No face detected - use last known position if recent
            self.face_not_found_frames += 1
            
            if self.last_face_bbox and self.face_not_found_frames <= self.max_face_lost_frames:
                # Use cached face region
                x, y, width, height = self.last_face_bbox
                if x + width <= w and y + height <= h:
                    face_region = frame[y:y + height, x:x + width]
                    return face_region, self.last_face_bbox
            
            # No face found and no recent cache
            return None, None
    
    def preprocess_face_region(self, face_region: np.ndarray) -> np.ndarray:
        """
        Apply focused preprocessing to a cropped face region
        
        Args:
            face_region: Cropped face image
            
        Returns:
            Preprocessed face region
        """
        return self.preprocess_frame(face_region)

    def clear_cache(self):
        """Clear the gamma table cache to free memory."""
        self.gamma_table_cache.clear()
