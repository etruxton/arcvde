"""
Main menu screen with camera feed and finger gun interaction
"""

import pygame
import cv2
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from screens.base_screen import BaseScreen

class Button:
    """Simple button class for UI"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.clicked = False
    
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
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the button"""
        color = UI_BUTTON_ACTIVE if self.clicked else UI_BUTTON_HOVER if self.hovered else UI_BUTTON
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, UI_TEXT, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text, True, UI_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class MenuScreen(BaseScreen):
    """Main menu screen"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 48)
        self.info_font = pygame.font.Font(None, 24)
        
        # Create buttons
        button_width = 250
        button_height = 60
        button_spacing = 20
        start_y = SCREEN_HEIGHT // 2 - 100
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        self.play_button = Button(
            center_x, start_y, button_width, button_height,
            "TARGET PRACTICE", self.button_font
        )
        
        self.arcade_button = Button(
            center_x, start_y + button_height + button_spacing, button_width, button_height,
            "ARCADE MODE", self.button_font
        )
        
        self.settings_button = Button(
            center_x, start_y + 2 * (button_height + button_spacing), button_width, button_height,
            "SETTINGS", self.button_font
        )
        
        self.instructions_button = Button(
            center_x, start_y + 3 * (button_height + button_spacing), button_width, button_height,
            "HOW TO PLAY", self.button_font
        )
        
        self.quit_button = Button(
            center_x, start_y + 4 * (button_height + button_spacing), button_width, button_height,
            "QUIT", self.button_font
        )
        
        self.buttons = [self.play_button, self.arcade_button, self.settings_button, self.instructions_button, self.quit_button]
        
        # Camera setup
        if not self.camera_manager.current_camera:
            self.camera_manager.initialize_camera(DEFAULT_CAMERA_ID)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle button events (mouse clicks)
        for button in self.buttons:
            if button.handle_event(event):
                return self._handle_button_action(button)
        
        # Handle keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return GAME_STATE_PLAYING
            elif event.key == pygame.K_2:
                return GAME_STATE_ARCADE
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        
        return None
    
    def _handle_button_action(self, button) -> str:
        """Handle button action - centralized logic"""
        if button == self.play_button:
            return GAME_STATE_PLAYING
        elif button == self.arcade_button:
            return GAME_STATE_ARCADE
        elif button == self.settings_button:
            return GAME_STATE_SETTINGS
        elif button == self.instructions_button:
            return GAME_STATE_INSTRUCTIONS
        elif button == self.quit_button:
            return "quit"
        return None
    
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update menu state"""
        # Process hand tracking
        self.process_finger_gun_tracking()
        
        # Handle finger gun shooting as clicks
        shot_button = self.check_button_shoot(self.buttons)
        if shot_button:
            return self._handle_button_action(shot_button)
        
        return None
    
    def draw(self) -> None:
        """Draw the menu screen"""
        # Clear screen
        self.screen.fill(UI_BACKGROUND)
        
        # Draw title
        title_text = self.title_font.render("FINGER GUN GAME", True, UI_ACCENT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.info_font.render("Use your finger gun to shoot targets!", True, UI_TEXT)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            self.highlight_button_if_aimed(button)
            button.draw(self.screen)
        
        # Draw crosshair if aiming
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
        
        # Draw camera feed
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        
        # Draw camera info
        self._draw_camera_info()
    
    
    def _draw_camera_info(self) -> None:
        """Draw camera information"""
        camera_info = self.camera_manager.get_camera_info()
        
        info_text = f"Camera {camera_info['current_id']} - {camera_info['resolution'][0]}x{camera_info['resolution'][1]}"
        info_surface = self.info_font.render(info_text, True, UI_TEXT)
        self.screen.blit(info_surface, (CAMERA_X, CAMERA_Y + CAMERA_HEIGHT + 5))
        
        # Show available cameras
        if len(camera_info['available_cameras']) > 1:
            avail_text = f"Available: {', '.join(map(str, camera_info['available_cameras']))}"
            avail_surface = self.info_font.render(avail_text, True, GRAY)
            self.screen.blit(avail_surface, (CAMERA_X, CAMERA_Y + CAMERA_HEIGHT + 25))