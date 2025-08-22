"""
Shared UI components with vaporwave styling
"""

# Third-party imports
import pygame

# Local application imports
from utils.constants import *


class Button:
    """Vaporwave-styled button class for UI"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_font = font
        self.hovered = False
        self.clicked = False
        self.finger_aimed = False  # State for finger gun aiming
        # Dynamically adjust font size to fit text within button
        self.font = self._get_fitted_font(width, height)

    def _get_fitted_font(self, width: int, height: int) -> pygame.font.Font:
        """Get a font size that fits the text within the button"""
        # Start with base font size
        font_size = 48  # Start with reasonable button text size

        # Leave some padding
        max_width = width - 30  # More padding for better appearance
        max_height = height - 10

        # Try progressively smaller fonts until text fits
        while font_size > 10:
            test_font = pygame.font.Font(None, font_size)
            text_surface = test_font.render(self.text, True, (255, 255, 255))

            if text_surface.get_width() <= max_width and text_surface.get_height() <= max_height:
                return test_font

            font_size -= 2

        # Return minimum size font if nothing else fits
        return pygame.font.Font(None, 10)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events, return True if clicked"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False

        return False

    def set_finger_aimed(self, aimed: bool) -> None:
        """Set whether the finger gun is aimed at this button"""
        self.finger_aimed = aimed

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the button with vaporwave styling"""
        # Determine colors based on state - finger aiming takes priority over mouse hover
        # Removed clicked state visual change - button returns to normal immediately
        if self.finger_aimed:  # Finger gun aiming takes priority
            bg_color = UI_BUTTON  # Keep the purple background
            border_color = VAPORWAVE_CYAN  # Use your cyan for the border
            text_color = UI_TEXT  # Keep normal text color
            glow_color = VAPORWAVE_CYAN  # Cyan glow effect
        elif self.hovered:  # Mouse hover as fallback
            bg_color = UI_BUTTON  # Keep the purple background
            border_color = VAPORWAVE_CYAN  # Use cyan border for mouse hover
            text_color = UI_TEXT  # Keep normal text color
            glow_color = VAPORWAVE_CYAN  # Cyan glow for mouse
        else:
            bg_color = UI_BUTTON
            border_color = VAPORWAVE_PURPLE
            text_color = UI_TEXT
            glow_color = None

        # Draw glow effect for hovered/clicked states
        if glow_color:
            for i in range(3):
                glow_rect = pygame.Rect(
                    self.rect.x - (i * 2), self.rect.y - (i * 2), self.rect.width + (i * 4), self.rect.height + (i * 4)
                )
                glow_alpha = max(30 - i * 10, 5)
                glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*glow_color, glow_alpha), (0, 0, glow_rect.width, glow_rect.height), 2)
                screen.blit(glow_surface, (glow_rect.x, glow_rect.y))

        # Draw button background
        pygame.draw.rect(screen, bg_color, self.rect)

        # Draw border with rounded corners effect
        pygame.draw.rect(screen, border_color, self.rect, 3)

        # Draw inner highlight for depth
        if not self.clicked:
            highlight_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, self.rect.height - 4)
            pygame.draw.rect(screen, (*border_color, 60), highlight_rect, 1)

        # Draw text with shadow for depth
        if not self.clicked:
            # Text shadow
            shadow_surface = self.font.render(self.text, True, VAPORWAVE_DARK)
            shadow_rect = shadow_surface.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
            screen.blit(shadow_surface, shadow_rect)

        # Main text
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
