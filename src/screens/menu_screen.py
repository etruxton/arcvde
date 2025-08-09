"""
Main menu screen with camera feed and finger gun interaction
"""

import pygame
import cv2
import time
import math
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from screens.base_screen import BaseScreen
from game.enemy import Enemy

class Button:
    """Simple button class for UI"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_font = font
        self.hovered = False
        self.clicked = False
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
        self.button_font = pygame.font.Font(None, 36)  # Reduced default size for better fit
        self.info_font = pygame.font.Font(None, 24)
        
        # Create buttons
        button_width = 250
        button_height = 60
        button_spacing = 20
        start_y = SCREEN_HEIGHT // 2 - 100
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        self.arcade_button = Button(
            center_x, start_y, button_width, button_height,
            "ARCADE MODE", self.button_font
        )
        
        self.play_button = Button(
            center_x, start_y + button_height + button_spacing, button_width, button_height,
            "TARGET PRACTICE", self.button_font
        )
        
        self.instructions_button = Button(
            center_x, start_y + 2 * (button_height + button_spacing), button_width, button_height,
            "HOW TO PLAY", self.button_font
        )
        
        self.settings_button = Button(
            center_x, start_y + 3 * (button_height + button_spacing), button_width, button_height,
            "SETTINGS", self.button_font
        )
        
        self.quit_button = Button(
            center_x, start_y + 4 * (button_height + button_spacing), button_width, button_height,
            "QUIT", self.button_font
        )
        
        self.buttons = [self.arcade_button, self.play_button, self.instructions_button, self.settings_button, self.quit_button]
        
        # Camera setup
        if not self.camera_manager.current_camera:
            self.camera_manager.initialize_camera(DEFAULT_CAMERA_ID)
        
        # Enemy showcase
        self.showcase_enemies = []
        self.init_enemy_showcase()
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle button events (mouse clicks)
        for button in self.buttons:
            if button.handle_event(event):
                return self._handle_button_action(button)
        
        # Handle keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return GAME_STATE_ARCADE
            elif event.key == pygame.K_2:
                return GAME_STATE_PLAYING
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
    
    def init_enemy_showcase(self):
        """Initialize enemies for showcase display"""
        # Create enemies in two rows to avoid button overlap
        # Front row: zombie and giant (larger, more visible)
        # Back row: skull and demon (behind and offset)
        
        # Front row enemies
        zombie = Enemy(-0.65, 0.4, "zombie")  # Left front
        zombie.animation_time = 0
        self.showcase_enemies.append(zombie)
        
        giant = Enemy(0.65, 0.4, "giant")  # Right front
        giant.animation_time = math.pi
        self.showcase_enemies.append(giant)
        
        # Back row enemies (further back and offset to be visible)
        skull = Enemy(-0.45, 0.7, "skull")  # Left back, slightly inward
        skull.animation_time = math.pi / 2
        self.showcase_enemies.append(skull)
        
        demon = Enemy(0.45, 0.7, "demon")  # Right back, slightly inward
        demon.animation_time = math.pi * 1.5
        self.showcase_enemies.append(demon)
    
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update menu state"""
        # Process hand tracking
        self.process_finger_gun_tracking()
        
        # Update showcase enemies
        for enemy in self.showcase_enemies:
            # Just update their animation time for idle animations
            enemy.animation_time += dt * 2
            enemy.walk_cycle += dt * 4
        
        # Handle finger gun shooting as clicks
        shot_button = self.check_button_shoot(self.buttons)
        if shot_button:
            return self._handle_button_action(shot_button)
        
        return None
    
    def draw(self) -> None:
        """Draw the menu screen"""
        # Clear screen with darker background for enemy visibility
        self.screen.fill((20, 20, 20))
        
        # Draw gradient background similar to game
        self._draw_menu_background()
        
        # Draw enemy showcase
        self._draw_enemy_showcase()
        
        # Draw semi-transparent overlay for UI
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title with glow effect
        title_text = self.title_font.render("FINGER GUN GAME", True, UI_ACCENT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        # Glow effect
        glow_surf = self.title_font.render("FINGER GUN GAME", True, (0, 100, 200))
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            glow_rect = glow_surf.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], 100 + offset[1]))
            self.screen.blit(glow_surf, glow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.info_font.render("Face the Apocalypse with Your Finger Gun!", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
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
    
    
    def _draw_menu_background(self):
        """Draw atmospheric background for menu"""
        # Create gradient from dark at top to slightly lighter at bottom
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            color = (
                int(10 + progress * 20),
                int(10 + progress * 15),
                int(15 + progress * 15)
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Add floor grid for depth
        horizon_y = int(SCREEN_HEIGHT * 0.5)
        grid_color = (30, 30, 40)
        
        # Vertical lines (perspective)
        for i in range(-10, 11):
            x_start = SCREEN_WIDTH // 2 + i * 100
            x_end = SCREEN_WIDTH // 2 + i * 30
            pygame.draw.line(self.screen, grid_color,
                           (x_start, SCREEN_HEIGHT),
                           (x_end, horizon_y), 1)
    
    def _draw_enemy_showcase(self):
        """Draw animated enemies in the background"""
        # Draw enemies
        for enemy in self.showcase_enemies:
            # Draw with full detail
            enemy.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT, debug_hitbox=False)
            
            # Add subtle glow effect around each enemy
            x, y = enemy.get_screen_position(SCREEN_WIDTH, SCREEN_HEIGHT)
            size = enemy.get_size()
            
            # Create pulsing glow
            glow_size = size + int(math.sin(enemy.animation_time) * 10)
            glow_surface = pygame.Surface((glow_size * 3, glow_size * 3), pygame.SRCALPHA)
            
            # Color based on enemy type
            glow_colors = {
                "zombie": (0, 100, 0, 30),
                "demon": (100, 0, 0, 30),
                "skull": (100, 100, 200, 30),
                "giant": (100, 0, 100, 30)
            }
            glow_color = glow_colors.get(enemy.enemy_type, (100, 100, 100, 30))
            
            pygame.draw.circle(glow_surface, glow_color,
                             (glow_size * 3 // 2, glow_size * 3 // 2), glow_size)
            self.screen.blit(glow_surface, (x - glow_size * 3 // 2, y - glow_size * 3 // 2))
    
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