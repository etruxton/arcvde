"""
Region-adaptive detection for problematic areas of the camera frame
"""

# Standard library imports
from typing import Optional, Tuple

# Third-party imports
import numpy as np


class RegionAdaptiveDetector:
    """Adapts detection parameters based on hand position in frame"""

    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Define the problematic region (full width at bottom)
        # Full width of camera, bottom 160 pixels
        self.problem_region = {
            "x_min": 0,  # Full width
            "x_max": frame_width,  # Full width
            "y_min": frame_height - 160,  # ~320 (160 pixels from bottom)
            "y_max": frame_height,  # All the way to bottom edge (480)
        }

    def get_hand_position_category(self, hand_landmarks) -> str:
        """
        Categorize hand position in frame
        Returns: 'problem_zone', 'edge', or 'normal'
        """
        if not hand_landmarks:
            return "normal"

        # Get multiple reference points for more accurate position
        wrist = hand_landmarks.landmark[0]  # WRIST landmark
        middle_mcp = hand_landmarks.landmark[9]  # MIDDLE_FINGER_MCP

        # Use average of wrist and middle MCP for more stable position
        avg_x = ((wrist.x + middle_mcp.x) / 2) * self.frame_width
        avg_y = ((wrist.y + middle_mcp.y) / 2) * self.frame_height

        # Debug: uncomment to see exact positions
        # print(f"Hand position: ({avg_x:.0f}, {avg_y:.0f}), Problem region: x[{self.problem_region['x_min']}-{self.problem_region['x_max']}], y[{self.problem_region['y_min']}-{self.problem_region['y_max']}], In zone: {in_x_range and in_y_range}")

        # Check if in problem region (bottom-center)
        # Must be within BOTH X and Y boundaries
        in_x_range = avg_x >= self.problem_region["x_min"] and avg_x <= self.problem_region["x_max"]
        in_y_range = avg_y >= self.problem_region["y_min"] and avg_y <= self.problem_region["y_max"]

        if in_x_range and in_y_range:
            return "problem_zone"

        # Check if near edges
        edge_threshold = 60
        if (
            avg_x < edge_threshold
            or avg_x > self.frame_width - edge_threshold
            or avg_y < edge_threshold
            or avg_y > self.frame_height - edge_threshold
        ):
            return "edge"

        return "normal"

    def get_adaptive_thresholds(self, position_category: str) -> dict:
        """
        Get adjusted thresholds based on position category
        """
        if position_category == "problem_zone":
            # Much more lenient thresholds for problem zone
            return {
                "thumb_index_multiplier": 1.8,  # 80% more lenient
                "middle_ring_multiplier": 2.0,  # 100% more lenient
                "ring_pinky_multiplier": 2.0,  # 100% more lenient
                "index_wrist_multiplier": 0.7,  # 30% less strict
                "min_confidence": 0.4,  # Lower confidence requirement
                "angle_weight_boost": 0.3,  # Boost angle detection weight
                "require_all_checks": False,  # Don't require all checks to pass
            }
        elif position_category == "edge":
            # Moderately lenient for edge positions
            return {
                "thumb_index_multiplier": 1.4,
                "middle_ring_multiplier": 1.5,
                "ring_pinky_multiplier": 1.5,
                "index_wrist_multiplier": 0.85,
                "min_confidence": 0.5,
                "angle_weight_boost": 0.15,
                "require_all_checks": False,
            }
        else:
            # Normal thresholds for center area
            return {
                "thumb_index_multiplier": 1.0,
                "middle_ring_multiplier": 1.0,
                "ring_pinky_multiplier": 1.0,
                "index_wrist_multiplier": 1.0,
                "min_confidence": 0.6,
                "angle_weight_boost": 0.0,
                "require_all_checks": True,
            }

    def adjust_detection_for_problem_zone(self, hand_landmarks) -> dict:
        """
        Special adjustments for the problem zone
        """
        hints = {}

        # In problem zone, we often see compressed perspective
        # Index finger appears shorter, other fingers bunch together

        # Get key landmarks
        index_tip = hand_landmarks.landmark[8]  # INDEX_FINGER_TIP
        index_mcp = hand_landmarks.landmark[5]  # INDEX_FINGER_MCP
        middle_tip = hand_landmarks.landmark[12]  # MIDDLE_FINGER_TIP
        wrist = hand_landmarks.landmark[0]  # WRIST

        # Check if hand is angled upward (common in bottom region)
        hand_angle = np.arctan2(index_mcp.y - wrist.y, index_mcp.x - wrist.x)
        hints["hand_pointing_up"] = hand_angle < -0.5  # Pointing upward

        # Check if fingers appear compressed (Z-depth issue)
        z_spread = abs(index_tip.z - middle_tip.z)
        hints["fingers_compressed"] = z_spread < 0.02

        # Check if hand appears small (far or angled)
        hand_size = np.sqrt((index_mcp.x - wrist.x) ** 2 + (index_mcp.y - wrist.y) ** 2)
        hints["hand_small"] = hand_size < 0.15

        return hints

    def calculate_region_specific_confidence(
        self, standard_score: float, angle_score: float, position_category: str, hints: dict
    ) -> float:
        """
        Calculate confidence with region-specific adjustments
        """
        base_confidence = standard_score * 0.6 + angle_score * 0.4

        if position_category == "problem_zone":
            # Boost confidence if we have supporting hints
            if hints.get("hand_pointing_up"):
                base_confidence += 0.15
            if hints.get("fingers_compressed"):
                base_confidence += 0.1
            if hints.get("hand_small"):
                # Small hand in problem zone is expected, slight boost
                base_confidence += 0.05

            # Apply minimum threshold for problem zone
            base_confidence = max(base_confidence, 0.45)

        return min(base_confidence, 1.0)

    def should_use_fallback_detection(self, position_category: str, hints: dict) -> bool:
        """
        Determine if we should use alternative detection methods
        """
        if position_category == "problem_zone":
            # Use fallback if multiple problem indicators
            problem_count = sum(
                [hints.get("hand_pointing_up", False), hints.get("fingers_compressed", False), hints.get("hand_small", False)]
            )
            return problem_count >= 2

        return False

    def get_debug_info(self, position_category: str, hints: dict) -> str:
        """
        Get debug information about current detection state
        """
        info = f"Region: {position_category}"
        if position_category == "problem_zone":
            info += " [PROBLEM ZONE]"
            if hints.get("hand_pointing_up"):
                info += " ↑"
            if hints.get("fingers_compressed"):
                info += " ≈"
            if hints.get("hand_small"):
                info += " ◦"
        return info
