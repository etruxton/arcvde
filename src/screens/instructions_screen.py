"""
Instructions/How-to screen
"""

import pygame
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from screens.menu_screen import Button
from screens.base_screen import BaseScreen
from game.target import TargetManager

class InstructionsScreen(BaseScreen):
    """Instructions screen showing how to play"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.section_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Create back button
        self.back_button = Button(
            50, 50, 120, 50,
            "← BACK", self.text_font
        )
        
        # Initialize target manager for practice area
        self.target_manager = TargetManager(
            SCREEN_WIDTH, SCREEN_HEIGHT, 
            (CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        )
        
        # Shooting state for practice area
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # milliseconds
        self.practice_score = 0
        
        # Instructions content
        self.instructions = [
            {
                "title": "How to Make a Finger Gun",
                "steps": [
                    "• Extend your index finger (pointing finger)",
                    "• Curl your middle, ring, and pinky fingers",
                    "• Point your thumb upward",
                    "• Keep your hand steady"
                ]
            },
            {
                "title": "How to Aim",
                "steps": [
                    "• Make the finger gun gesture",
                    "• Move your hand to aim the crosshair",
                    "• Green crosshair = Standard mode (best)",
                    "• Yellow crosshair = Depth mode (pointing at camera)",
                    "• Purple crosshair = Wrist angle mode (fallback)"
                ]
            },
            {
                "title": "How to Shoot",
                "steps": [
                    "• While aiming, quickly flick your thumb down",
                    "• Keep the finger gun pose while shooting",
                    "• Wait for cooldown between shots",
                    "• Hit targets to score points!"
                ]
            },
            {
                "title": "Tips for Better Tracking",
                "steps": [
                    "• Use good lighting",
                    "• Position yourself 2-3 feet from camera",
                    "• Hold hand at slight angle for best results",
                    "• Move slowly and deliberately",
                    "• If tracking fails, try adjusting hand position"
                ]
            }
        ]
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle back button
        if self.back_button.handle_event(event):
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
        
        # Update target manager for practice area
        self.target_manager.update(dt, current_time)
        
        # Handle finger gun shooting
        shot_button = self.check_button_shoot([self.back_button])
        if shot_button:
            return GAME_STATE_MENU
        
        # Handle shooting at targets
        if self.shoot_detected and self.crosshair_pos:
            self._handle_shoot(self.crosshair_pos)
            self.shoot_detected = False  # Reset after handling shot
        
        return None
    
    def draw(self) -> None:
        """Draw the instructions screen"""
        # Clear screen
        self.screen.fill(UI_BACKGROUND)
        
        # Draw title
        title_text = self.title_font.render("HOW TO PLAY", True, UI_ACCENT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw back button
        self.highlight_button_if_aimed(self.back_button)
        self.back_button.draw(self.screen)
        
        # Draw targets
        self.target_manager.draw(self.screen)
        
        # Draw crosshair if aiming
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
        
        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if (self.shoot_pos and 
            current_time - self.shoot_animation_time < self.shoot_animation_duration):
            self._draw_shoot_animation(self.shoot_pos)
        
        # Draw instructions in two columns
        left_x = 100
        right_x = SCREEN_WIDTH // 2 + 50
        start_y = 150
        column_width = SCREEN_WIDTH // 2 - 150
        
        for i, section in enumerate(self.instructions):
            x = left_x if i % 2 == 0 else right_x
            y = start_y + (i // 2) * 300
            
            self._draw_instruction_section(section, x, y, column_width)
        
        # Draw camera demo
        self._draw_camera_demo()
        
        # Draw practice score
        if self.practice_score > 0:
            score_text = self.text_font.render(f"Practice Score: {self.practice_score}", True, GREEN)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            self.screen.blit(score_text, score_rect)
        
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
        demo_y = 150
        
        # Draw camera feed with tracking
        self.draw_camera_with_tracking(demo_x, demo_y, demo_width, demo_height)
        
        # Draw label
        label_text = self.small_font.render("Practice your finger gun here!", True, UI_TEXT)
        label_rect = label_text.get_rect(center=(demo_x + demo_width // 2, demo_y - 20))
        self.screen.blit(label_text, label_rect)
        
        # Draw crosshair examples
        examples_y = demo_y + demo_height + 30
        
        # Green crosshair example
        pygame.draw.circle(self.screen, GREEN, (demo_x + 50, examples_y), 15, 2)
        pygame.draw.line(self.screen, GREEN, (demo_x + 20, examples_y), (demo_x + 80, examples_y), 2)
        pygame.draw.line(self.screen, GREEN, (demo_x + 50, examples_y - 30), (demo_x + 50, examples_y + 30), 2)
        standard_text = self.small_font.render("Standard", True, GREEN)
        self.screen.blit(standard_text, (demo_x + 90, examples_y - 10))
        
        # Yellow crosshair example
        pygame.draw.circle(self.screen, YELLOW, (demo_x + 50, examples_y + 50), 15, 2)
        pygame.draw.line(self.screen, YELLOW, (demo_x + 20, examples_y + 50), (demo_x + 80, examples_y + 50), 2)
        pygame.draw.line(self.screen, YELLOW, (demo_x + 50, examples_y + 20), (demo_x + 50, examples_y + 80), 2)
        depth_text = self.small_font.render("Depth", True, YELLOW)
        self.screen.blit(depth_text, (demo_x + 90, examples_y + 40))
        
        # Purple crosshair example
        pygame.draw.circle(self.screen, PURPLE, (demo_x + 50, examples_y + 100), 15, 2)
        pygame.draw.line(self.screen, PURPLE, (demo_x + 20, examples_y + 100), (demo_x + 80, examples_y + 100), 2)
        pygame.draw.line(self.screen, PURPLE, (demo_x + 50, examples_y + 70), (demo_x + 50, examples_y + 130), 2)
        wrist_text = self.small_font.render("Wrist Angle", True, PURPLE)
        self.screen.blit(wrist_text, (demo_x + 90, examples_y + 90))
    
    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action in practice area"""
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        
        # Check for target hits
        score_gained = self.target_manager.check_hit(shoot_position[0], shoot_position[1])
        self.practice_score += score_gained
    
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