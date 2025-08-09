"""
Main game screen with hand tracking and shooting gameplay
"""

import pygame
import cv2
import time
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from game.hand_tracker import HandTracker
from game.target import TargetManager

class GameScreen:
    """Main gameplay screen"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        self.screen = screen
        self.camera_manager = camera_manager
        
        # Initialize game components
        self.hand_tracker = HandTracker()
        self.target_manager = TargetManager(
            SCREEN_WIDTH, SCREEN_HEIGHT, 
            (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        )
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        
        # Game state
        self.score = 0
        self.game_time = 0
        self.paused = False
        
        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # milliseconds
        
        # Crosshair state
        self.crosshair_pos = None
        self.crosshair_color = GREEN
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
        
        return None
    
    def reset_game(self) -> None:
        """Reset the game state"""
        self.score = 0
        self.game_time = 0
        self.target_manager.clear_all_targets()
        self.hand_tracker.reset_tracking_state()
        self.shoot_pos = None
        self.crosshair_pos = None
    
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        if self.paused:
            return None
        
        self.game_time += dt
        
        # Update targets
        self.target_manager.update(dt, current_time)
        
        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
        
        # Process hand tracking
        self._process_hand_tracking()
        
        return None
    
    def _process_hand_tracking(self) -> None:
        """Process hand tracking and shooting detection"""
        ret, frame = self.camera_manager.read_frame()
        if not ret or frame is None:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
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
                    
                    # Map finger position to game screen
                    game_x = int((index_coords[0] / self.camera_manager.frame_width) * SCREEN_WIDTH)
                    game_y = int((index_coords[1] / self.camera_manager.frame_height) * SCREEN_HEIGHT)
                    self.crosshair_pos = (game_x, game_y)
                    
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
                    if shoot_this_frame:
                        self._handle_shoot(self.crosshair_pos)
                        # Add "SHOOT!" text to camera feed in red
                        cv2.putText(processed_frame, "SHOOT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    self.crosshair_pos = None
        else:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
        
        # Store processed frame for display
        self._processed_camera_frame = processed_frame
    
    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        
        # Check for target hits
        score_gained = self.target_manager.check_hit(shoot_position[0], shoot_position[1])
        self.score += score_gained
    
    def draw(self) -> None:
        """Draw the game screen"""
        # Clear screen
        self.screen.fill(BLACK)
        
        if self.paused:
            self._draw_pause_screen()
            return
        
        # Draw targets
        self.target_manager.draw(self.screen)
        
        # Draw crosshair
        if self.crosshair_pos:
            self._draw_crosshair(self.crosshair_pos, self.crosshair_color)
        
        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if (self.shoot_pos and 
            current_time - self.shoot_animation_time < self.shoot_animation_duration):
            self._draw_shoot_animation(self.shoot_pos)
        
        # Draw UI
        self._draw_ui()
        
        # Draw camera feed
        self._draw_camera_feed()
    
    def _draw_crosshair(self, pos: tuple, color: tuple) -> None:
        """Draw crosshair at given position"""
        x, y = pos
        size = 20
        thickness = 2
        
        # Draw circle
        pygame.draw.circle(self.screen, color, pos, size, thickness)
        
        # Draw cross lines
        pygame.draw.line(self.screen, color, (x - size - 10, y), (x + size + 10, y), thickness)
        pygame.draw.line(self.screen, color, (x, y - size - 10), (x, y + size + 10), thickness)
    
    def _draw_shoot_animation(self, pos: tuple) -> None:
        """Draw shooting animation"""
        current_time = pygame.time.get_ticks()
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
                pygame.draw.circle(shoot_surface, (*WHITE, alpha//2), (radius, radius), radius//2, 2)
                self.screen.blit(shoot_surface, (pos[0] - radius, pos[1] - radius))
    
    def _draw_ui(self) -> None:
        """Draw game UI elements"""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Active targets count
        active_targets = self.target_manager.get_active_target_count()
        targets_text = self.small_font.render(f"Targets: {active_targets}", True, WHITE)
        self.screen.blit(targets_text, (10, 50))
        
        # Detection mode indicator
        if self.hand_tracker.detection_mode != "none":
            mode_color = self.crosshair_color
            mode_text = self.small_font.render(
                f"Mode: {self.hand_tracker.detection_mode.title()}", True, mode_color
            )
            self.screen.blit(mode_text, (10, 80))
            
            # Confidence score
            conf_text = self.small_font.render(
                f"Confidence: {self.hand_tracker.confidence_score:.2f}", True, mode_color
            )
            self.screen.blit(conf_text, (10, 100))
        
        # FPS counter
        fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, GRAY)
        self.screen.blit(fps_text, (10, SCREEN_HEIGHT - 30))
        
        # Controls hint
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Reset", True, GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        self.screen.blit(controls_text, controls_rect)
    
    def _draw_camera_feed(self) -> None:
        """Draw camera feed in corner"""
        if hasattr(self, '_processed_camera_frame') and self._processed_camera_frame is not None:
            # Convert processed frame to pygame surface
            camera_surface = self.camera_manager.frame_to_pygame_surface(
                self._processed_camera_frame, (CAMERA_WIDTH, CAMERA_HEIGHT)
            )
        else:
            # Fallback: get raw frame
            ret, frame = self.camera_manager.read_frame()
            if ret and frame is not None:
                camera_surface = self.camera_manager.frame_to_pygame_surface(
                    frame, (CAMERA_WIDTH, CAMERA_HEIGHT)
                )
            else:
                # No camera available
                camera_surface = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT))
                camera_surface.fill(DARK_GRAY)
                no_cam_text = self.small_font.render("No Camera", True, WHITE)
                text_rect = no_cam_text.get_rect(center=(CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2))
                camera_surface.blit(no_cam_text, text_rect)
        
        # Draw border
        border_color = self.crosshair_color if self.crosshair_pos else WHITE
        border_rect = pygame.Rect(CAMERA_X - 2, CAMERA_Y - 2, CAMERA_WIDTH + 4, CAMERA_HEIGHT + 4)
        pygame.draw.rect(self.screen, border_color, border_rect, 2)
        
        # Draw camera feed
        self.screen.blit(camera_surface, (CAMERA_X, CAMERA_Y))
    
    def _draw_pause_screen(self) -> None:
        """Draw pause overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.big_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(pause_text, pause_rect)
        
        # Instructions
        instructions = [
            "Press P or SPACE to resume",
            "Press ESC to return to menu",
            "Press R to reset game"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)