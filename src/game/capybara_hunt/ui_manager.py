# Standard library imports
from typing import Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from utils.constants import GAME_STATE_MENU, SCREEN_WIDTH, UI_ACCENT
from utils.ui_components import Button


class CapybaraHuntUI:
    """Manages UI elements and button interactions for Capybara Hunt game mode"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.continue_button: Optional[Button] = None
        self.retry_button: Optional[Button] = None
        self.menu_button: Optional[Button] = None

    def create_continue_button(self, screen_height: int) -> Button:
        """Create continue button for round completion screen"""
        button_width = 200
        button_height = 60
        button_y = screen_height // 2 + 80

        self.continue_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2, button_y, button_width, button_height, "CONTINUE", self.font
        )
        return self.continue_button

    def create_game_over_buttons(self, screen_height: int) -> Tuple[Button, Button]:
        """Create retry and menu buttons for game over screen"""
        button_width = 150
        button_height = 50
        button_y = screen_height // 2 + 180

        self.retry_button = Button(
            SCREEN_WIDTH // 2 - button_width - 20, button_y, button_width, button_height, "RETRY", self.font
        )

        self.menu_button = Button(SCREEN_WIDTH // 2 + 20, button_y, button_width, button_height, "MENU", self.font)

        return self.retry_button, self.menu_button

    def handle_mouse_button_click(self, mouse_pos: Tuple[int, int], round_complete: bool, game_over: bool) -> Optional[str]:
        """Handle mouse button clicks on UI buttons

        Returns:
            Action string or None: 'continue', 'retry', 'menu', or None
        """
        if round_complete and self.continue_button:
            if self.continue_button.rect.collidepoint(mouse_pos):
                return "continue"

        if game_over:
            if self.retry_button and self.retry_button.rect.collidepoint(mouse_pos):
                return "retry"
            if self.menu_button and self.menu_button.rect.collidepoint(mouse_pos):
                return "menu"

        return None

    def check_button_hit(self, button: Button, crosshair_pos: Optional[Tuple[int, int]], sound_manager) -> bool:
        """Check if crosshair is over button when shooting"""
        try:
            if crosshair_pos and button and hasattr(button, "rect") and button.rect.collidepoint(crosshair_pos):
                sound_manager.play("shoot")
                return True
        except Exception as e:
            print(f"Error checking button hit: {e}")
        return False

    def handle_shooting_buttons(
        self, crosshair_pos: Optional[Tuple[int, int]], sound_manager, round_complete: bool, game_over: bool
    ) -> Optional[str]:
        """Handle shooting at buttons with crosshair

        Returns:
            Action string or None: 'continue', 'retry', 'menu', or None
        """
        if round_complete and self.continue_button:
            if self.check_button_hit(self.continue_button, crosshair_pos, sound_manager):
                return "continue"

        if game_over:
            # Check retry button first
            if self.retry_button and self.check_button_hit(self.retry_button, crosshair_pos, sound_manager):
                return "retry"
            # Only check menu if retry wasn't hit
            if self.menu_button and self.check_button_hit(self.menu_button, crosshair_pos, sound_manager):
                return "menu"

        return None

    def draw_continue_button(self, screen: pygame.Surface, crosshair_pos: Optional[Tuple[int, int]]):
        """Draw continue button with highlight if aimed at"""
        if not self.continue_button:
            return

        self.continue_button.draw(screen)

        if crosshair_pos and self.continue_button.rect.collidepoint(crosshair_pos):
            pygame.draw.rect(screen, UI_ACCENT, self.continue_button.rect, 3)

    def draw_game_over_buttons(self, screen: pygame.Surface, crosshair_pos: Optional[Tuple[int, int]]):
        """Draw game over buttons with highlights if aimed at"""
        if not self.retry_button or not self.menu_button:
            return

        self.retry_button.draw(screen)
        self.menu_button.draw(screen)

        if crosshair_pos:
            if self.retry_button.rect.collidepoint(crosshair_pos):
                pygame.draw.rect(screen, UI_ACCENT, self.retry_button.rect, 3)
            if self.menu_button.rect.collidepoint(crosshair_pos):
                pygame.draw.rect(screen, UI_ACCENT, self.menu_button.rect, 3)

    def reset_buttons(self):
        """Reset all buttons to None"""
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None
