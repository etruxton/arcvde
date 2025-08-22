"""
Instructions/How-to screen
"""

# Standard library imports
from typing import Optional

# Third-party imports
import pygame

# Local application imports
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    GAME_STATE_MENU,
    GAME_STATE_PLAYING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    UI_BACKGROUND,
    UI_TEXT,
    VAPORWAVE_CYAN,
    WHITE,
    YELLOW,
)
from utils.sound_manager import get_sound_manager
from utils.ui_components import Button


class InstructionsScreen(BaseScreen):
    """Instructions screen showing how to play"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Initialize sound manager
        self.sound_manager = get_sound_manager()

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.section_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

        # Create back button
        self.back_button = Button(50, 50, 120, 50, "BACK", self.text_font)

        # Shooting state for visual feedback
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # milliseconds

        # Instructions content
        self.instructions = [
            {
                "title": "How to Make a Finger Gun",
                "steps": [
                    "• Extend your index finger (pointing finger)",
                    "• Curl your middle, ring, and pinky fingers",
                    "• Point your thumb upward",
                    "• Keep your hand steady",
                ],
            },
            {
                "title": "How to Shoot",
                "steps": [
                    "• While aiming, quickly flick your thumb down",
                    "• Keep the finger gun pose while shooting",
                    "• Wait for cooldown between shots",
                    "• Practice in the camera demo area!",
                ],
            },
            {
                "title": "Tips for Better Tracking",
                "steps": [
                    "• Use good lighting",
                    "• Position yourself 2-3 feet from camera",
                    "• Hold hand at slight angle for best results",
                    "• Move slowly and deliberately",
                    "• If tracking fails, try adjusting hand position",
                ],
            },
        ]

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle back button
        if self.back_button.handle_event(event):
            self.sound_manager.play("shoot")
            return GAME_STATE_MENU

        # Handle keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                return GAME_STATE_PLAYING

        return None

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update instructions screen"""
        # Process hand tracking
        self.process_finger_gun_tracking()

        # Handle finger gun shooting
        shot_button = self.check_button_shoot([self.back_button])
        if shot_button:
            self.sound_manager.play("shoot")
            return GAME_STATE_MENU

        # Handle shooting for visual feedback
        if self.shoot_detected and self.crosshair_pos:
            self._handle_shoot(self.crosshair_pos)
            self.shoot_detected = False  # Reset after handling shot

        return None

    def draw(self) -> None:
        """Draw the instructions screen"""
        # Clear screen
        self.screen.fill(UI_BACKGROUND)

        # Draw title with vaporwave styling
        title_text = self.title_font.render("HOW TO PLAY", True, VAPORWAVE_CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)

        # Update finger aiming state and draw back button
        self.update_button_finger_states([self.back_button])
        self.back_button.draw(self.screen)

        # Draw crosshair if aiming
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
            self._draw_shoot_animation(self.shoot_pos)

        # Draw instructions - avoid top-right where camera is
        left_x = 100
        start_y = 150
        # Make left column wider since right column needs to avoid camera
        left_column_width = SCREEN_WIDTH // 2 - 120

        # Draw first two sections on the left
        for i in range(min(2, len(self.instructions))):
            y = start_y + i * 250  # Reduced spacing
            self._draw_instruction_section(self.instructions[i], left_x, y, left_column_width)

        # Draw remaining sections on the right, below the camera
        right_x = SCREEN_WIDTH // 2 + 50
        right_start_y = 300  # Start below camera (camera is at y=50, height=200)
        right_column_width = 350  # Narrower to avoid camera

        for i in range(2, len(self.instructions)):
            y = right_start_y + (i - 2) * 250
            self._draw_instruction_section(self.instructions[i], right_x, y, right_column_width)

        # Draw camera demo
        self._draw_camera_demo()

        # Draw bottom text
        bottom_text = self.small_font.render("Press SPACE to start playing!", True, UI_ACCENT)
        bottom_rect = bottom_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.screen.blit(bottom_text, bottom_rect)

    def _draw_instruction_section(self, section: dict, x: int, y: int, width: int) -> None:
        """Draw a single instruction section"""
        # Draw section title
        title_surface = self.section_font.render(section["title"], True, UI_TEXT)
        self.screen.blit(title_surface, (x, y))

        # Draw steps
        step_y = y + 50
        for step in section["steps"]:
            # Word wrap for long lines
            words = step.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surface = self.text_font.render(test_line, True, WHITE)

                if test_surface.get_width() <= width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)

            if current_line:
                lines.append(current_line)

            # Draw wrapped lines
            for line in lines:
                step_surface = self.text_font.render(line, True, WHITE)
                self.screen.blit(step_surface, (x, step_y))
                step_y += 30

            step_y += 10  # Extra spacing between steps

    def _draw_camera_demo(self) -> None:
        """Draw camera demonstration"""
        demo_width = 300
        demo_height = 200
        demo_x = SCREEN_WIDTH - demo_width - 50
        demo_y = 50  # Moved to top-right

        # Draw camera feed with tracking
        self.draw_camera_with_tracking(demo_x, demo_y, demo_width, demo_height)

    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action for visual feedback"""
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()

        # Play shoot sound
        self.sound_manager.play("shoot")

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
