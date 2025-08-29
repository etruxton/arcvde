"""
Target Practice screen with hand tracking and shooting gameplay
"""

# Standard library imports
import time
from typing import Optional

# Third-party imports
import cv2
import pygame

# Local application imports
from game.target import TargetManager
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    BLACK,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    DARK_GRAY,
    GAME_STATE_MENU,
    GRAY,
    GREEN,
    PURPLE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from utils.sound_manager import get_sound_manager


class TargetPracticeScreen(BaseScreen):
    """Target Practice gameplay screen"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        self.target_manager = TargetManager(SCREEN_WIDTH, SCREEN_HEIGHT, (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT))

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)

        self.score = 0
        self.game_time = 0
        self.paused = False

        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # milliseconds

        # Note: crosshair_pos and crosshair_color are inherited from BaseScreen

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

        self.target_manager.update(dt, current_time)

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
        # Use base class method for tracking
        self.process_finger_gun_tracking()

        if self.shoot_detected:
            self._handle_shoot(self.crosshair_pos)
            self.shoot_detected = False  # Reset after handling

    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()

        # Play shoot sound
        self.sound_manager.play("shoot")

        score_gained = self.target_manager.check_hit(shoot_position[0], shoot_position[1])
        if score_gained > 0:
            self.sound_manager.play("hit")
        self.score += score_gained

    def draw(self) -> None:
        """Draw the game screen"""
        # Clear screen
        self.screen.fill(BLACK)

        if self.paused:
            self._draw_pause_screen()
            return

        self.target_manager.draw(self.screen)

        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
            self._draw_shoot_animation(self.shoot_pos)

        self._draw_ui()

        self._draw_camera_feed()

        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

    # Note: _draw_crosshair removed - using base class draw_crosshair method

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
                pygame.draw.circle(shoot_surface, (*WHITE, alpha // 2), (radius, radius), radius // 2, 2)
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
            mode_text = self.small_font.render(f"Mode: {self.hand_tracker.detection_mode.title()}", True, mode_color)
            self.screen.blit(mode_text, (10, 80))

            # Confidence score
            conf_text = self.small_font.render(f"Confidence: {self.hand_tracker.confidence_score:.2f}", True, mode_color)
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
        # Use base class method
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

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
        instructions = ["Press P or SPACE to resume", "Press ESC to return to menu", "Press R to reset game"]

        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)
