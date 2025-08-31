"""
Blink detection module for computer vision-based gameplay.

Available detectors:
- BlinkDetector: Basic blink detection with adaptive thresholds
- EnhancedBlinkDetector: Advanced detection with relative detection and preprocessing
- FramePreprocessor: Image preprocessing for challenging lighting conditions
"""

from .blink_detector import BlinkDetector
from .enhanced_blink_detector import EnhancedBlinkDetector
from .frame_preprocessor import FramePreprocessor

__all__ = ["BlinkDetector", "EnhancedBlinkDetector", "FramePreprocessor"]
