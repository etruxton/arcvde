"""
Debug overlay for displaying hand tracking statistics
"""

# Standard library imports
from typing import Any, Dict, Optional

# Third-party imports
import pygame


def draw_debug_overlay(screen: pygame.Surface, stats: Optional[Dict[str, Any]], hand_tracker: Any) -> None:
    """
    Draw debug information overlay when debug mode is enabled

    Args:
        screen: Pygame surface to draw on
        stats: Tracking statistics dictionary
        hand_tracker: Hand tracker instance
    """
    if not stats:
        return

    # Create semi-transparent background for debug info
    debug_surface = pygame.Surface((350, 200))
    debug_surface.set_alpha(200)
    debug_surface.fill((0, 0, 0))
    screen.blit(debug_surface, (10, 10))

    # Font for debug text
    debug_font = pygame.font.Font(None, 20)

    # Color constants
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)
    RED = (255, 0, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    LIGHT_BLUE = (128, 128, 255)
    DIM_CYAN = (0, 200, 200)
    GRAY = (200, 200, 200)

    y_offset = 20

    # Title
    title = debug_font.render("=== DEBUG MODE ===", True, CYAN)
    screen.blit(title, (20, y_offset))
    y_offset += 25

    # Performance stats
    fps_text = f"FPS: {1000/stats['total_ms']:.1f}" if stats.get("total_ms", 0) > 0 else "FPS: --"
    fps_surface = debug_font.render(fps_text, True, GREEN)
    screen.blit(fps_surface, (20, y_offset))
    y_offset += 20

    preprocess_text = f"Preprocessing: {stats.get('preprocessing_ms', 0):.1f}ms"
    preprocess_surface = debug_font.render(preprocess_text, True, WHITE)
    screen.blit(preprocess_surface, (20, y_offset))
    y_offset += 20

    detection_text = f"Detection: {stats.get('detection_ms', 0):.1f}ms"
    detection_surface = debug_font.render(detection_text, True, WHITE)
    screen.blit(detection_surface, (20, y_offset))
    y_offset += 20

    # Detection mode
    mode_colors = {
        "standard": GREEN,
        "angles": CYAN,
        "depth": MAGENTA,
        "wrist_angle": LIGHT_BLUE,
        "angles_only": DIM_CYAN,
        "none": RED,
    }
    mode = stats.get("detection_mode", "none")
    mode_color = mode_colors.get(mode, WHITE)
    mode_text = f"Mode: {mode}"
    mode_surface = debug_font.render(mode_text, True, mode_color)
    screen.blit(mode_surface, (20, y_offset))
    y_offset += 20

    # Confidence
    confidence = stats.get("confidence", 0)
    conf_color = GREEN if confidence > 0.7 else YELLOW if confidence > 0.4 else RED
    conf_text = f"Confidence: {confidence:.2f}"
    conf_surface = debug_font.render(conf_text, True, conf_color)
    screen.blit(conf_surface, (20, y_offset))
    y_offset += 20

    # Kalman status
    if stats.get("kalman_active"):
        kalman_conf = stats.get("kalman_tracking_confidence", 0)
        kalman_text = f"Kalman: {kalman_conf:.2f}"
        kalman_surface = debug_font.render(kalman_text, True, YELLOW)
        screen.blit(kalman_surface, (20, y_offset))
        y_offset += 20

    # Feature status
    if hasattr(hand_tracker, "enable_preprocessing"):
        features = []
        if hand_tracker.enable_preprocessing:
            features.append("Preprocess")
        if hand_tracker.enable_angles:
            features.append("Angles")
        if hand_tracker.enable_kalman:
            features.append("Kalman")

        feature_text = f"Features: {', '.join(features)}"
        feature_surface = debug_font.render(feature_text, True, GRAY)
        screen.blit(feature_surface, (20, y_offset))
