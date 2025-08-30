"""
Credits screen showing attributions for open source assets
"""

# Standard library imports
from typing import Optional

# Third-party imports
import pygame

# Local application imports
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    BLACK,
    GAME_STATE_MENU,
    GRAY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    VAPORWAVE_PURPLE,
    WHITE,
)


class CreditsScreen(BaseScreen):
    """Credits screen showing open source asset attributions"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.heading_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)

        # Scroll state
        self.scroll_y = 0
        self.scroll_speed = 2
        self.max_scroll = 0  # Will be calculated based on content

        # Credits content
        self.credits_content = self._build_credits_content()
        
        # Calculate initial max scroll
        self._calculate_max_scroll()

    def _build_credits_content(self) -> list:
        """Build the credits content structure"""
        return [
            # Header
            {"type": "title", "text": "CREDITS", "color": VAPORWAVE_PURPLE},
            {"type": "space", "height": 30},
            
            {"type": "text", "text": "Thank you to all the amazing creators who made their work", "color": WHITE},
            {"type": "text", "text": "available under open source licenses!", "color": WHITE},
            {"type": "space", "height": 40},

            # Art Assets Section
            {"type": "heading", "text": "ART ASSETS", "color": UI_ACCENT},
            {"type": "space", "height": 20},
            
            {"type": "subheading", "text": "Capybara Hunt Mode", "color": VAPORWAVE_PURPLE},
            {"type": "text", "text": "Capybara Sprites: \"Simple Capybara Sprite Sheet\" by Rainloaf", "color": WHITE},
            {"type": "text", "text": "Source: rainloaf.itch.io/capybara-sprite-sheet", "color": GRAY},
            {"type": "text", "text": "License: Free to use in commercial/non-commercial projects", "color": GRAY},
            {"type": "space", "height": 30},

            # Music Section
            {"type": "heading", "text": "MUSIC & AUDIO", "color": UI_ACCENT},
            {"type": "space", "height": 20},

            {"type": "text", "text": "Menu/Target Practice Music: \"Somewhere in the Elevator\" by Peachtea", "color": WHITE},
            {"type": "text", "text": "Source: opengameart.org/content/somewhere-in-the-elevator", "color": GRAY},
            {"type": "text", "text": "License: CC-BY 3.0", "color": GRAY},
            {"type": "space", "height": 20},

            {"type": "subheading", "text": "Capybara Hunt Music", "color": VAPORWAVE_PURPLE},
            {"type": "text", "text": "Background Music: \"Day & Night in Summerset\" by edwinnington", "color": WHITE},
            {"type": "text", "text": "Source: opengameart.org/content/day-night-in-summerset", "color": GRAY},
            {"type": "text", "text": "License: CC-BY 3.0", "color": GRAY},
            {"type": "space", "height": 20},

            {"type": "subheading", "text": "Doomsday Mode Stage Music", "color": VAPORWAVE_PURPLE},
            {"type": "text", "text": "All Doomsday stage music by nene from OpenGameArt:", "color": WHITE},
            {"type": "space", "height": 10},
            
            {"type": "text", "text": "Stage 1: \"Boss Battle 3 Alternate (8-bit)\"", "color": WHITE},
            {"type": "text", "text": "Stage 2: \"Boss Battle 4 (8-bit) - Re-upload\"", "color": WHITE},
            {"type": "text", "text": "Stage 3: \"Boss Battle 6 (8-bit)\"", "color": WHITE},
            {"type": "text", "text": "Stage 4+: \"Boss Battle 8 Retro\" (alternating tracks)", "color": WHITE},
            {"type": "text", "text": "Stage 4+ Metal: \"Boss Battle 8 Metal\" (third alternating track)", "color": WHITE},
            {"type": "space", "height": 10},
            {"type": "text", "text": "All tracks licensed under CC0 (Public Domain)", "color": GRAY},
            {"type": "space", "height": 40},

            # Technology Section  
            {"type": "heading", "text": "OPEN SOURCE TECHNOLOGY", "color": UI_ACCENT},
            {"type": "space", "height": 20},
            {"type": "text", "text": "This game is built with amazing open source libraries:", "color": WHITE},
            {"type": "space", "height": 15},
            {"type": "text", "text": "• Pygame - Game development framework", "color": GRAY},
            {"type": "text", "text": "• OpenCV - Computer vision and image processing", "color": GRAY},
            {"type": "text", "text": "• MediaPipe - Real-time hand tracking", "color": GRAY},
            {"type": "text", "text": "• NumPy - Numerical computing", "color": GRAY},
            {"type": "space", "height": 40},

            # Developer Section
            {"type": "heading", "text": "DEVELOPMENT", "color": UI_ACCENT},
            {"type": "space", "height": 20},
            {"type": "text", "text": "Game Design & Programming: Erica Truxton", "color": WHITE},
            {"type": "space", "height": 30},

            # License Info
            {"type": "heading", "text": "LICENSE INFORMATION", "color": UI_ACCENT},
            {"type": "space", "height": 20},
            {"type": "text", "text": "CC-BY 3.0: Attribution required, commercial use allowed", "color": GRAY},
            {"type": "text", "text": "CC0: Public domain, no restrictions", "color": GRAY},
            {"type": "space", "height": 40},

            {"type": "text", "text": "Thank you for playing ARCVDE!", "color": VAPORWAVE_PURPLE},
            {"type": "space", "height": 30},
            {"type": "text", "text": "ESC - Return to Menu", "color": VAPORWAVE_PURPLE},
            {"type": "space", "height": 100},  # Extra space at bottom
        ]

    def _calculate_max_scroll(self) -> None:
        """Calculate the maximum scroll distance based on content height"""
        y = 50  # Starting position
        
        for item in self.credits_content:
            if item["type"] == "title":
                y += 60
            elif item["type"] == "heading":
                y += 45
            elif item["type"] == "subheading":
                y += 35
            elif item["type"] == "text":
                y += 30
            elif item["type"] == "space":
                y += item["height"]
        
        # Set max scroll with some buffer
        self.max_scroll = max(0, y - SCREEN_HEIGHT + 100)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:  # Mouse wheel down
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)
                
        return None

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update credits (auto-scroll)"""
        # Auto-scroll slowly
        self.scroll_y += self.scroll_speed * dt * 10
        
        # Calculate max scroll to ensure we have the current value
        self._calculate_max_scroll()
        
        # Reset to top when reaching bottom (only if max_scroll > 0)
        if self.max_scroll > 0 and self.scroll_y >= self.max_scroll:
            self.scroll_y = 0
            
        return None

    def draw(self) -> None:
        """Draw the credits screen"""
        self.screen.fill(BLACK)
        
        # Start position with scroll offset
        y = -self.scroll_y + 50
        
        for item in self.credits_content:
            if item["type"] == "title":
                text_surface = self.title_font.render(item["text"], True, item["color"])
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
                if text_rect.bottom > 0 and text_rect.top < SCREEN_HEIGHT:  # Only draw if visible
                    self.screen.blit(text_surface, text_rect)
                y += 60
                
            elif item["type"] == "heading":
                text_surface = self.heading_font.render(item["text"], True, item["color"])
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
                if text_rect.bottom > 0 and text_rect.top < SCREEN_HEIGHT:
                    self.screen.blit(text_surface, text_rect)
                y += 45
                
            elif item["type"] == "subheading":
                text_surface = self.font.render(item["text"], True, item["color"])
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
                if text_rect.bottom > 0 and text_rect.top < SCREEN_HEIGHT:
                    self.screen.blit(text_surface, text_rect)
                y += 35
                
            elif item["type"] == "text":
                text_surface = self.font.render(item["text"], True, item["color"])
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
                if text_rect.bottom > 0 and text_rect.top < SCREEN_HEIGHT:
                    self.screen.blit(text_surface, text_rect)
                y += 30
                
            elif item["type"] == "space":
                y += item["height"]
        
        # Draw scroll indicator
        if self.max_scroll > 0:
            total_content_height = self.max_scroll + SCREEN_HEIGHT - 100
            scroll_bar_height = max(20, int((SCREEN_HEIGHT / total_content_height) * SCREEN_HEIGHT))
            scroll_bar_y = int((self.scroll_y / self.max_scroll) * (SCREEN_HEIGHT - scroll_bar_height))
            pygame.draw.rect(self.screen, UI_ACCENT, (SCREEN_WIDTH - 10, scroll_bar_y, 5, scroll_bar_height))