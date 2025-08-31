"""
Blink detection module for computer vision-based gameplay.

Available classes:
- EnhancedBlinkDetector: Advanced blink detection with face region processing and preprocessing
- FramePreprocessor: Image preprocessing for challenging lighting conditions  
- FaceRegionDetector: Face detection and region extraction for focused processing

The EnhancedBlinkDetector provides:
- Face region cropping for improved accuracy and performance
- Coordinate transformation for accurate eye highlighting
- Adaptive thresholds with personal calibration
- Relative blink detection for angled faces
- Optional preprocessing for challenging lighting
- Glasses detection and compensation
- Temporal smoothing for stability

Key Features:
- Face Region Processing: Crops face area for faster, more accurate detection
- Smart Preprocessing: Only processes relevant face region instead of full frame
- Coordinate Transformation: Maps face region landmarks back to full frame for display
- Temporal Stability: Tracks face position across frames for consistent detection
- Performance Optimized: Reduces processing load while improving accuracy
"""

from .enhanced_blink_detector import EnhancedBlinkDetector
from .frame_preprocessor import FramePreprocessor
from .face_region_detector import FaceRegionDetector

# For backward compatibility, make EnhancedBlinkDetector available as BlinkDetector too
BlinkDetector = EnhancedBlinkDetector

__all__ = ["BlinkDetector", "EnhancedBlinkDetector", "FramePreprocessor", "FaceRegionDetector"]
