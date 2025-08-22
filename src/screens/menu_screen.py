"""
Main menu screen with camera feed and finger gun interaction
"""

import pygame
import cv2
import time
import math
import os
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from utils.sound_manager import get_sound_manager
from utils.ui_components import Button
from screens.base_screen import BaseScreen
from game.enemy import Enemy


class MenuScreen(BaseScreen):
    """Main menu screen"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)
        
        # Initialize sound manager
        self.sound_manager = get_sound_manager()
        
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
            "DOOMSDAY", self.button_font
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
        
        self.logo = None
        self.load_logo()
    
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
        # Play sound effect when button is clicked
        self.sound_manager.play('shoot')
        
        result = None
        if button == self.play_button:
            result = GAME_STATE_PLAYING
        elif button == self.arcade_button:
            result = GAME_STATE_ARCADE
        elif button == self.settings_button:
            result = GAME_STATE_SETTINGS
        elif button == self.instructions_button:
            result = GAME_STATE_INSTRUCTIONS
        elif button == self.quit_button:
            result = "quit"
        
        
        return result
    
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
    
    def load_logo(self):
        """Load the game logo image"""
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "arCVde-2.png")
            if os.path.exists(logo_path):
                self.logo = pygame.image.load(logo_path).convert_alpha()
                logo_width = 500
                logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
                self.logo = pygame.transform.scale(self.logo, (logo_width, logo_height))
                print(f"Logo loaded successfully from {logo_path}")
            else:
                print(f"Logo file not found at {logo_path}")
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo = None
    
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
        # Clear screen with vaporwave background
        self.screen.fill(UI_BACKGROUND)
        
        # Draw gradient background similar to game
        self._draw_menu_background()
        
        # Draw enemy showcase
        self._draw_enemy_showcase()
        
        # Draw semi-transparent overlay for UI readability (reduced opacity)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(40)  # Reduced from 100 to 40 for more vibrant enemies
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        if self.logo:
            logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(self.logo, logo_rect)
        else:
            # Draw title with vaporwave glow effect
            title_y = 100
            
            # Multi-layer glow effect
            glow_layers = [
                (VAPORWAVE_PINK, 6, 30),     # Outer pink glow
                (VAPORWAVE_CYAN, 4, 50),     # Mid cyan glow  
                (VAPORWAVE_PURPLE, 2, 70),   # Inner purple glow
            ]
            
            for glow_color, radius, alpha in glow_layers:
                glow_text = self.title_font.render("arcvde", True, glow_color)
                
                for x_offset in range(-radius, radius + 1):
                    for y_offset in range(-radius, radius + 1):
                        if x_offset * x_offset + y_offset * y_offset <= radius * radius:
                            glow_rect = glow_text.get_rect(center=(SCREEN_WIDTH // 2 + x_offset, title_y + y_offset))
                            
                            # Create alpha surface for this glow layer
                            glow_surface = pygame.Surface(glow_text.get_size(), pygame.SRCALPHA)
                            glow_surface.blit(glow_text, (0, 0))
                            glow_surface.set_alpha(alpha)
                            self.screen.blit(glow_surface, glow_rect)
            
            # Main title text
            title_text = self.title_font.render("arcvde", True, VAPORWAVE_LIGHT)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, title_y))
            self.screen.blit(title_text, title_rect)
        
        
        # Update finger aiming states and draw buttons
        self.update_button_finger_states(self.buttons)
        for button in self.buttons:
            button.draw(self.screen)
        
        # Draw crosshair if aiming
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
        
        # Draw camera feed
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        
        # Draw camera info
        self._draw_camera_info()
    
    
    def _draw_menu_background(self):
        """Draw vaporwave atmospheric background for menu"""
        # Create vaporwave gradient from dark purple at top to dark cyan at bottom
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            
            # Interpolate between dark purple and dark cyan
            r = int(VAPORWAVE_DARK[0] + progress * (10 - VAPORWAVE_DARK[0]))
            g = int(VAPORWAVE_DARK[1] + progress * (40 - VAPORWAVE_DARK[1]))
            b = int(VAPORWAVE_DARK[2] + progress * (60 - VAPORWAVE_DARK[2]))
            
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Add retro grid lines with vaporwave colors
        horizon_y = int(SCREEN_HEIGHT * 0.6)
        
        # Horizontal grid lines
        for i in range(10):
            y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (i / 10) ** 0.8
            alpha = max(20, 60 - i * 5)
            grid_color = (*VAPORWAVE_CYAN[:3], alpha)
            
            # Create surface for alpha blending
            line_surface = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
            line_surface.fill(grid_color)
            self.screen.blit(line_surface, (0, int(y)))
        
        # Vertical perspective lines
        for i in range(-8, 9):
            x_start = SCREEN_WIDTH // 2 + i * 120
            x_end = SCREEN_WIDTH // 2 + i * 40
            alpha = max(15, 50 - abs(i) * 3)
            grid_color = (*VAPORWAVE_PINK[:3], alpha)
            
            # Draw with alpha
            line_surface = pygame.Surface((2, SCREEN_HEIGHT - horizon_y), pygame.SRCALPHA)
            line_surface.fill(grid_color)
            
            # Calculate line positions
            if 0 <= x_start < SCREEN_WIDTH or 0 <= x_end < SCREEN_WIDTH:
                pygame.draw.line(self.screen, VAPORWAVE_PURPLE,
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