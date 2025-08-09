"""
Base screen class with shared finger gun functionality
"""

import pygame
import cv2
from typing import Optional, Tuple
from utils.constants import *
from utils.camera_manager import CameraManager
from game.hand_tracker import HandTracker

class BaseScreen:
    """Base class for screens that need finger gun interaction"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        self.screen = screen
        self.camera_manager = camera_manager
        
        # Initialize hand tracker
        self.hand_tracker = HandTracker()
        
        # Finger gun interaction state
        self.crosshair_pos = None
        self.crosshair_color = GREEN
        self.shoot_detected = False
        self.last_shoot_check_time = 0
        self.shoot_detected_time = 0
        self._processed_camera_frame = None
    
    def process_finger_gun_tracking(self) -> None:
        """Process finger gun tracking - shared across all screens"""
        ret, frame = self.camera_manager.read_frame()
        if not ret or frame is None:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
            self.shoot_detected = False
            return
        
        # Process frame for hand detection
        processed_frame, results = self.hand_tracker.process_frame(frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on camera frame
                self.hand_tracker.draw_landmarks(processed_frame, hand_landmarks)
                
                # Detect finger gun
                is_gun, index_coords, thumb_tip, middle_mcp, thumb_middle_dist, confidence = \
                    self.hand_tracker.detect_finger_gun(
                        hand_landmarks,
                        self.camera_manager.frame_width,
                        self.camera_manager.frame_height
                    )
                
                if is_gun and index_coords:
                    # Draw green dot on index finger in camera feed
                    cv2.circle(processed_frame, index_coords, 15, (0, 255, 0), -1)
                    
                    # Map finger position to screen coordinates
                    screen_x = int((index_coords[0] / self.camera_manager.frame_width) * SCREEN_WIDTH)
                    screen_y = int((index_coords[1] / self.camera_manager.frame_height) * SCREEN_HEIGHT)
                    self.crosshair_pos = (screen_x, screen_y)
                    
                    # Set crosshair color based on detection mode
                    if self.hand_tracker.detection_mode == "standard":
                        self.crosshair_color = GREEN
                    elif self.hand_tracker.detection_mode == "depth":
                        self.crosshair_color = YELLOW
                    elif self.hand_tracker.detection_mode == "wrist_angle":
                        self.crosshair_color = PURPLE
                    else:
                        self.crosshair_color = WHITE
                    
                    # Detect shooting gesture
                    shoot_this_frame = self.hand_tracker.detect_shooting_gesture(thumb_tip, thumb_middle_dist)
                    if shoot_this_frame and not self.shoot_detected:  # Only set if not already detected
                        import time
                        self.shoot_detected = True
                        self.shoot_detected_time = time.time()
                    
                    # Add detection mode text to camera feed
                    cv2.putText(processed_frame, f"Mode: {self.hand_tracker.detection_mode}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(processed_frame, f"Conf: {confidence:.2f}", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Show if shoot is detected on camera feed
                    if shoot_this_frame:  # Show SHOOT! when shooting happens, not when flag is set
                        cv2.putText(processed_frame, "SHOOT!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                else:
                    self.crosshair_pos = None
        else:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
            self.shoot_detected = False
        
        # Store processed frame for display
        self._processed_camera_frame = processed_frame
        
        # Auto-reset shoot_detected after timeout (prevents getting stuck)
        import time
        if self.shoot_detected and time.time() - self.shoot_detected_time > 0.5:  # 500ms timeout
            self.shoot_detected = False
    
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
            for button in buttons:
                if hasattr(button, 'rect') and button.rect.collidepoint(self.crosshair_pos):
                    self.shoot_detected = False  # Reset after detecting a shot
                    return button
        return None
    
    def draw_camera_with_tracking(self, x: int, y: int, width: int, height: int) -> None:
        """Draw camera feed with hand tracking overlays"""
        # Use processed frame if available (with hand tracking overlays)
        if self._processed_camera_frame is not None:
            camera_surface = self.camera_manager.frame_to_pygame_surface(
                self._processed_camera_frame, (width, height)
            )
        else:
            # Fallback to raw frame
            ret, frame = self.camera_manager.read_frame()
            if ret and frame is not None:
                camera_surface = self.camera_manager.frame_to_pygame_surface(
                    frame, (width, height)
                )
            else:
                # Create a placeholder if no camera
                camera_surface = pygame.Surface((width, height))
                camera_surface.fill(DARK_GRAY)
                
                # Add "No Camera" text
                font = pygame.font.Font(None, 24)
                no_cam_text = font.render("No Camera", True, WHITE)
                text_rect = no_cam_text.get_rect(center=(width // 2, height // 2))
                camera_surface.blit(no_cam_text, text_rect)
        
        # Draw border with tracking color if active
        border_color = self.crosshair_color if self.crosshair_pos else UI_ACCENT
        border_rect = pygame.Rect(x - 2, y - 2, width + 4, height + 4)
        pygame.draw.rect(self.screen, border_color, border_rect, 2)
        
        # Draw camera feed
        self.screen.blit(camera_surface, (x, y))
    
    def highlight_button_if_aimed(self, button, highlight_color: Optional[Tuple[int, int, int]] = None) -> None:
        """Highlight button if crosshair is over it"""
        if self.crosshair_pos and hasattr(button, 'rect') and button.rect.collidepoint(self.crosshair_pos):
            color = highlight_color or self.crosshair_color
            highlight_rect = pygame.Rect(button.rect.x - 3, button.rect.y - 3,
                                       button.rect.width + 6, button.rect.height + 6)
            pygame.draw.rect(self.screen, color, highlight_rect, 3)