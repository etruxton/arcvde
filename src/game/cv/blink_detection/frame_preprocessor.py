"""
Frame preprocessing module for enhanced blink detection.

Provides image enhancement techniques to improve blink detection reliability
in various lighting conditions, similar to those used in finger gun detection.
"""

# Standard library imports
from typing import Dict

# Third-party imports
import cv2
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

    def clear_cache(self):
        """Clear the gamma table cache to free memory."""
        self.gamma_table_cache.clear()
