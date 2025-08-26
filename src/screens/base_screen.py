"""
Base screen class with shared finger gun functionality
"""

# Standard library imports
from typing import Optional, Tuple

# Third-party imports
import cv2
import pygame

# Use enhanced tracker for better performance
try:
    # Local application imports
    from game.cv.finger_gun_detection import EnhancedHandTracker as HandTracker

    print("[Hand Tracking] Using Enhanced Tracker with preprocessing, angles, and Kalman filter")
except ImportError:
    # Original tracker fallback
    from game.hand_tracker import HandTracker
    print("[Hand Tracking] Using Original Tracker")
# Local application imports
from utils.camera_manager import CameraManager
from utils.constants import DARK_GRAY, GREEN, PURPLE, SCREEN_HEIGHT, SCREEN_WIDTH, UI_ACCENT, WHITE, YELLOW
from utils.settings_manager import get_settings_manager
from utils.sound_manager import get_sound_manager


class BaseScreen:
    """Base class for screens that need finger gun interaction"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        self.screen = screen
        self.camera_manager = camera_manager

        # Initialize hand tracker and managers
        self.hand_tracker = HandTracker()
        self.sound_manager = get_sound_manager()
        self.settings_manager = get_settings_manager()

        # Finger gun interaction state
        self.crosshair_pos = None
        self.crosshair_color = GREEN
        self.shoot_detected = False
        self.last_shoot_check_time = 0
        self.shoot_detected_time = 0
        self._processed_camera_frame = None

        # Shooting animation state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # milliseconds

    def process_finger_gun_tracking(self) -> None:
        """Process finger gun tracking - shared across all screens"""
        ret, frame = self.camera_manager.read_frame()
        if not ret or frame is None:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
            self.shoot_detected = False
            return

        # Process frame for hand detection
        # Check if debug mode is enabled
        debug_mode = self.settings_manager.get("debug_mode", False)

        # Handle both original (2 returns) and enhanced (3 returns) tracker
        if hasattr(self.hand_tracker, "enable_preprocessing"):  # Enhanced tracker
            processed_frame, results, stats = self.hand_tracker.process_frame(frame, debug_mode)
            self.last_tracking_stats = stats  # Store for debug overlay
        else:  # Original tracker
            processed_frame, results = self.hand_tracker.process_frame(frame)
            self.last_tracking_stats = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on camera frame
                self.hand_tracker.draw_landmarks(processed_frame, hand_landmarks)

                # Detect finger gun
                (
                    is_gun,
                    index_coords,
                    thumb_tip,
                    middle_mcp,
                    thumb_middle_dist,
                    confidence,
                ) = self.hand_tracker.detect_finger_gun(
                    hand_landmarks, self.camera_manager.frame_width, self.camera_manager.frame_height
                )

                if is_gun and index_coords:
                    # Draw green dot on index finger in camera feed
                    cv2.circle(processed_frame, index_coords, 15, (0, 255, 0), -1)

                    # Map finger position to screen coordinates
                    screen_x = int((index_coords[0] / self.camera_manager.frame_width) * SCREEN_WIDTH)
                    screen_y = int((index_coords[1] / self.camera_manager.frame_height) * SCREEN_HEIGHT)
                    self.crosshair_pos = (screen_x, screen_y)

                    # Always use green for crosshair
                    self.crosshair_color = GREEN

                    # Detect shooting gesture
                    shoot_this_frame = self.hand_tracker.detect_shooting_gesture(thumb_tip, thumb_middle_dist)
                    if shoot_this_frame and not self.shoot_detected:  # Only set if not already detected
                        # Standard library imports
                        import time

                        # Check if enough time has passed since last shot (prevents rapid fire)
                        current_time = time.time()
                        if current_time - self.shoot_detected_time > 0.3:  # 300ms cooldown between shots
                            self.shoot_detected = True
                            self.shoot_detected_time = current_time

                            # Trigger shoot animation and sound
                            self.shoot_pos = self.crosshair_pos
                            self.shoot_animation_time = pygame.time.get_ticks()
                            self.sound_manager.play("shoot")

                    # Show if shoot is detected on camera feed
                    if shoot_this_frame:  # Show SHOOT! when shooting happens, not when flag is set
                        cv2.putText(processed_frame, "SHOOT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                else:
                    self.crosshair_pos = None
        else:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
            self.shoot_detected = False

        # Store processed frame for display
        self._processed_camera_frame = processed_frame

    def draw_crosshair(self, pos: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        """Draw crosshair at given position - shared across all screens"""
        x, y = pos
        size = 15
        thickness = 2

        # Draw circle
        pygame.draw.circle(self.screen, color, pos, size, thickness)

        # Draw cross lines
        pygame.draw.line(self.screen, color, (x - size - 8, y), (x + size + 8, y), thickness)
        pygame.draw.line(self.screen, color, (x, y - size - 8), (x, y + size + 8), thickness)

    def check_button_shoot(self, buttons: list) -> Optional[object]:
        """Check if any button was shot at - returns the button if found"""
        if self.shoot_detected and self.crosshair_pos:
            # Always reset the flag after checking
            self.shoot_detected = False

            for button in buttons:
                if hasattr(button, "rect") and button.rect.collidepoint(self.crosshair_pos):
                    return button
        return None

    def draw_camera_with_tracking(self, x: int, y: int, width: int, height: int) -> None:
        """Draw camera feed with hand tracking overlays"""
        # Use processed frame if available (with hand tracking overlays)
        if self._processed_camera_frame is not None:
            camera_surface = self.camera_manager.frame_to_pygame_surface(self._processed_camera_frame, (width, height))
        else:
            # Fallback to raw frame
            ret, frame = self.camera_manager.read_frame()
            if ret and frame is not None:
                camera_surface = self.camera_manager.frame_to_pygame_surface(frame, (width, height))
            else:
                # Create a placeholder if no camera
                camera_surface = pygame.Surface((width, height))
                camera_surface.fill(DARK_GRAY)

                # Add "No Camera" text
                font = pygame.font.Font(None, 24)
                no_cam_text = font.render("No Camera", True, WHITE)
                text_rect = no_cam_text.get_rect(center=(width // 2, height // 2))
                camera_surface.blit(no_cam_text, text_rect)

        # Draw border - green if tracking, accent color otherwise
        border_color = GREEN if self.crosshair_pos else UI_ACCENT
        border_rect = pygame.Rect(x - 2, y - 2, width + 4, height + 4)
        pygame.draw.rect(self.screen, border_color, border_rect, 2)

        # Draw camera feed
        self.screen.blit(camera_surface, (x, y))

        # Draw problem zone rectangle in debug mode
        if self.settings_manager.get("debug_mode", False):
            # Problem zone is bottom 160 pixels of camera (full width)
            # Scale to camera display size
            zone_height_ratio = 160 / self.camera_manager.frame_height  # 160/480 = 0.333
            zone_height = int(height * zone_height_ratio)
            zone_y = y + height - zone_height

            # Determine color based on whether hand is in zone
            zone_color = (
                GREEN
                if (
                    hasattr(self.hand_tracker, "last_position_category")
                    and self.hand_tracker.last_position_category == "problem_zone"
                )
                else (255, 100, 100)
            )

            # Draw semi-transparent overlay
            zone_surface = pygame.Surface((width, zone_height))
            zone_surface.set_alpha(50)
            zone_surface.fill(zone_color)
            self.screen.blit(zone_surface, (x, zone_y))

            # Draw border
            pygame.draw.rect(self.screen, zone_color, (x, zone_y, width, zone_height), 2)

            # Add label
            font = pygame.font.Font(None, 16)
            label = font.render("PROBLEM ZONE", True, zone_color)
            label_rect = label.get_rect(center=(x + width // 2, zone_y + 10))
            self.screen.blit(label, label_rect)

    def highlight_button_if_aimed(self, button, highlight_color: Optional[Tuple[int, int, int]] = None) -> None:
        """Highlight button if crosshair is over it"""
        if self.crosshair_pos and hasattr(button, "rect") and button.rect.collidepoint(self.crosshair_pos):
            color = highlight_color or self.crosshair_color
            highlight_rect = pygame.Rect(button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6)
            pygame.draw.rect(self.screen, color, highlight_rect, 3)

    def update_button_finger_states(self, buttons: list) -> None:
        """Update finger aiming state for all buttons in the list"""
        for button in buttons:
            if hasattr(button, "set_finger_aimed"):
                if self.crosshair_pos and button.rect.collidepoint(self.crosshair_pos):
                    button.set_finger_aimed(True)
                else:
                    button.set_finger_aimed(False)

    def draw_debug_overlay(self) -> None:
        """Draw debug information overlay when debug mode is enabled"""
        if not hasattr(self, "last_tracking_stats") or not self.last_tracking_stats:
            return

        # Import camera constants
        # Local application imports
        from utils.constants import CAMERA_HEIGHT, CAMERA_WIDTH, CAMERA_X, CAMERA_Y

        # Position debug info below the camera
        debug_x = CAMERA_X
        debug_y = CAMERA_Y + CAMERA_HEIGHT + 10  # 10px gap below camera

        # Create semi-transparent background for debug info
        debug_surface = pygame.Surface((CAMERA_WIDTH, 200))  # Match camera width
        debug_surface.set_alpha(200)
        debug_surface.fill((0, 0, 0))
        self.screen.blit(debug_surface, (debug_x, debug_y))

        # Font for debug text
        debug_font = pygame.font.Font(None, 18)  # Slightly smaller font to fit

        # Prepare debug information
        stats = self.last_tracking_stats
        y_offset = debug_y + 10  # Start 10px from top of debug area
        x_offset = debug_x + 10  # 10px padding from left

        # Title
        title = debug_font.render("=== DEBUG MODE ===", True, (0, 255, 255))
        self.screen.blit(title, (x_offset, y_offset))
        y_offset += 25

        # Performance stats
        fps_text = f"FPS: {1000/stats['total_ms']:.1f}" if stats["total_ms"] > 0 else "FPS: --"
        fps_surface = debug_font.render(fps_text, True, (0, 255, 0))
        self.screen.blit(fps_surface, (x_offset, y_offset))
        y_offset += 20

        preprocess_text = f"Preprocessing: {stats['preprocessing_ms']:.1f}ms"
        preprocess_surface = debug_font.render(preprocess_text, True, WHITE)
        self.screen.blit(preprocess_surface, (x_offset, y_offset))
        y_offset += 20

        detection_text = f"Detection: {stats['detection_ms']:.1f}ms"
        detection_surface = debug_font.render(detection_text, True, WHITE)
        self.screen.blit(detection_surface, (x_offset, y_offset))
        y_offset += 20

        # Detection mode
        mode_colors = {
            "standard": (0, 255, 0),
            "angles": (0, 255, 255),
            "depth": (255, 0, 255),
            "wrist_angle": (128, 128, 255),
            "angles_only": (0, 200, 200),
            "none": (255, 0, 0),
        }
        mode_color = mode_colors.get(stats["detection_mode"], WHITE)
        mode_text = f"Mode: {stats['detection_mode']}"
        mode_surface = debug_font.render(mode_text, True, mode_color)
        self.screen.blit(mode_surface, (x_offset, y_offset))
        y_offset += 20

        # Confidence
        conf_color = (0, 255, 0) if stats["confidence"] > 0.7 else (255, 255, 0) if stats["confidence"] > 0.4 else (255, 0, 0)
        conf_text = f"Confidence: {stats['confidence']:.2f}"
        conf_surface = debug_font.render(conf_text, True, conf_color)
        self.screen.blit(conf_surface, (x_offset, y_offset))
        y_offset += 20

        # Kalman status
        if stats.get("kalman_active"):
            kalman_text = f"Kalman: {stats['kalman_tracking_confidence']:.2f}"
            kalman_surface = debug_font.render(kalman_text, True, (255, 255, 0))
            self.screen.blit(kalman_surface, (x_offset, y_offset))
            y_offset += 20

        # Feature status
        if hasattr(self.hand_tracker, "enable_preprocessing"):
            features = []
            if self.hand_tracker.enable_preprocessing:
                features.append("Preprocess")
            if self.hand_tracker.enable_angles:
                features.append("Angles")
            if self.hand_tracker.enable_kalman:
                features.append("Kalman")

            feature_text = f"Features: {', '.join(features)}"
            feature_surface = debug_font.render(feature_text, True, (200, 200, 200))
            self.screen.blit(feature_surface, (x_offset, y_offset))

    def draw_shoot_animation(self) -> None:
        """Draw shooting animation if active"""
        if not self.shoot_pos:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.shoot_animation_time >= self.shoot_animation_duration:
            self.shoot_pos = None  # Animation finished
            return

        time_since_shoot = current_time - self.shoot_animation_time
        animation_progress = time_since_shoot / self.shoot_animation_duration

        if animation_progress < 1.0:
            # Expanding circle animation
            radius = int(40 * animation_progress)
            alpha = int(255 * (1 - animation_progress))

            # Create surface for alpha blending
            if alpha > 0:
                shoot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shoot_surface, (*YELLOW, alpha), (radius, radius), radius, 3)
                pygame.draw.circle(shoot_surface, (*WHITE, alpha // 2), (radius, radius), radius // 2, 2)
                self.screen.blit(shoot_surface, (self.shoot_pos[0] - radius, self.shoot_pos[1] - radius))
