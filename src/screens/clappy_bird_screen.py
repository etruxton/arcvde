"""
Clappy Bird - A Flappy Bird clone controlled by clapping
"""
import pygame
import random
import math
import cv2
from typing import List, Tuple, Optional
from src.screens.base_screen import BaseScreen
from src.game.cv.clap_detection import ClapDetector
from src.utils.constants import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    GAME_STATE_MENU,
)

class Pipe:
    """A pipe obstacle in the game"""
    def __init__(self, x: int, gap_y: int, gap_height: int = 200):  # Increased from 150 to 200
        self.x = x
        self.gap_y = gap_y
        self.gap_height = gap_height
        self.width = 60
        self.passed = False
        
    def update(self, speed: float):
        """Move the pipe left"""
        self.x -= speed
        
    def draw(self, screen: pygame.Surface):
        """Draw the pipe with a fun, cartoony style"""
        # Top pipe
        top_height = self.gap_y
        if top_height > 0:
            # Main pipe body
            pygame.draw.rect(screen, (34, 139, 34), 
                           (self.x, 0, self.width, top_height))
            # Pipe cap
            pygame.draw.rect(screen, (46, 125, 50), 
                           (self.x - 5, top_height - 20, self.width + 10, 25))
            # Highlight
            pygame.draw.rect(screen, (60, 179, 60), 
                           (self.x + 5, 0, 10, top_height - 20))
        
        # Bottom pipe
        bottom_y = self.gap_y + self.gap_height
        bottom_height = SCREEN_HEIGHT - bottom_y
        if bottom_height > 0:
            # Main pipe body
            pygame.draw.rect(screen, (34, 139, 34), 
                           (self.x, bottom_y, self.width, bottom_height))
            # Pipe cap
            pygame.draw.rect(screen, (46, 125, 50), 
                           (self.x - 5, bottom_y - 5, self.width + 10, 25))
            # Highlight
            pygame.draw.rect(screen, (60, 179, 60), 
                           (self.x + 5, bottom_y + 20, 10, bottom_height - 20))
    
    def get_collision_rects(self) -> List[pygame.Rect]:
        """Get collision rectangles for the pipe"""
        rects = []
        # Top pipe
        if self.gap_y > 0:
            rects.append(pygame.Rect(self.x, 0, self.width, self.gap_y))
        # Bottom pipe
        bottom_y = self.gap_y + self.gap_height
        if bottom_y < SCREEN_HEIGHT:
            rects.append(pygame.Rect(self.x, bottom_y, self.width, SCREEN_HEIGHT - bottom_y))
        return rects

class Bird:
    """The bird character"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.velocity = 0
        self.gravity = 0.5
        self.jump_strength = -8
        self.radius = 20
        self.rotation = 0
        self.flap_animation = 0
        
    def update(self):
        """Update bird physics"""
        self.velocity += self.gravity
        self.y += self.velocity
        
        # Update rotation based on velocity
        self.rotation = max(-30, min(30, self.velocity * 3))
        
        # Flap animation
        self.flap_animation += 0.3
        
    def jump(self):
        """Make the bird jump"""
        self.velocity = self.jump_strength
        
    def draw(self, screen: pygame.Surface):
        """Draw the bird with a cute, animated style"""
        # Wing flap offset
        wing_offset = math.sin(self.flap_animation) * 3
        
        # Bird body (yellow circle)
        pygame.draw.circle(screen, (255, 215, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 140, 0), (int(self.x), int(self.y)), self.radius, 3)
        
        # Wings (animated)
        wing_y = self.y + wing_offset
        # Left wing
        pygame.draw.ellipse(screen, (255, 165, 0), 
                          (self.x - self.radius - 8, wing_y - 5, 15, 10))
        # Right wing
        pygame.draw.ellipse(screen, (255, 165, 0), 
                          (self.x + self.radius - 7, wing_y - 5, 15, 10))
        
        # Eye
        eye_x = self.x + 5
        eye_y = self.y - 5
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_x), int(eye_y)), 6)
        pygame.draw.circle(screen, (0, 0, 0), (int(eye_x + 2), int(eye_y)), 3)
        
        # Beak
        beak_points = [
            (self.x + self.radius - 5, self.y + 2),
            (self.x + self.radius + 8, self.y),
            (self.x + self.radius - 5, self.y - 2)
        ]
        pygame.draw.polygon(screen, (255, 165, 0), beak_points)
        
    def get_collision_rect(self) -> pygame.Rect:
        """Get collision rectangle for the bird"""
        return pygame.Rect(self.x - self.radius + 5, self.y - self.radius + 5, 
                          (self.radius - 5) * 2, (self.radius - 5) * 2)

class ClappyBirdScreen(BaseScreen):
    """Clappy Bird game screen"""
    
    def __init__(self, screen: pygame.Surface, camera_manager):
        # Initialize base class (handles camera, hand tracker, sound manager, settings)
        super().__init__(screen, camera_manager)
        
        # Initialize clap detection
        try:
            self.clap_detector = ClapDetector()
            self.clap_available = True
        except Exception as e:
            print(f"Warning: Clap detection failed to initialize: {e}")
            self.clap_detector = None
            self.clap_available = False
        
        # Camera frame caching for better performance
        self.current_frame = None
        self.current_clap_detected = False
        self.current_debug_info = {}
            
        self.reset_game()
    
        
    def reset_game(self):
        """Reset the game state"""
        self.bird = Bird(100, SCREEN_HEIGHT // 2)
        self.pipes: List[Pipe] = []
        self.score = 0
        self.game_over = False
        self.started = False
        self.pipe_speed = 3
        self.pipe_spawn_timer = 0
        self.background_x = 0
        
        # Spawn initial pipe
        self.spawn_pipe()
        
    def spawn_pipe(self):
        """Spawn a new pipe"""
        gap_y = random.randint(100, SCREEN_HEIGHT - 250)
        pipe = Pipe(SCREEN_WIDTH, gap_y)
        self.pipes.append(pipe)
        
    def handle_event(self, event):
        """Handle pygame events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from src.utils.constants import GAME_STATE_MENU
                return GAME_STATE_MENU
            elif event.key == pygame.K_r and self.game_over:
                self.reset_game()
            elif event.key == pygame.K_SPACE and not self.game_over:
                if not self.started:
                    self.started = True
                self.bird.jump()
                
        return None
        
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game logic"""
        # Process camera frame and store it for both clap detection and drawing
        self.current_frame = None
        self.current_clap_detected = False
        
        if self.clap_available and self.clap_detector and self.camera_manager.current_camera:
            try:
                # Read camera frame once per update
                ret, frame = self.camera_manager.current_camera.read()
                if ret and frame is not None:
                    # Process frame and store results
                    processed_frame, clap_detected, debug_info = self.clap_detector.process_frame(frame)
                    self.current_frame = processed_frame
                    self.current_clap_detected = clap_detected
                    self.current_debug_info = debug_info
            except Exception as e:
                print(f"Error during clap detection: {e}")
            
        if self.current_clap_detected:
            print(f"[DEBUG] Clap detected in game! started={self.started}, game_over={self.game_over}")
            if not self.started and not self.game_over:
                self.started = True
                print("[DEBUG] Game started!")
            if not self.game_over:
                self.bird.jump()
                print("[DEBUG] Bird jumped!")
        
        if not self.started or self.game_over:
            return None
            
        # Update bird
        self.bird.update()
        
        # Check if bird hits ground or ceiling
        if self.bird.y + self.bird.radius >= SCREEN_HEIGHT or self.bird.y - self.bird.radius <= 0:
            self.game_over = True
            
        # Update pipes
        for pipe in self.pipes[:]:
            pipe.update(self.pipe_speed)
            
            # Check collision
            bird_rect = self.bird.get_collision_rect()
            for pipe_rect in pipe.get_collision_rects():
                if bird_rect.colliderect(pipe_rect):
                    self.game_over = True
                    
            # Check if bird passed pipe
            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                pipe.passed = True
                self.score += 1
                
            # Remove pipes that are off screen
            if pipe.x + pipe.width < 0:
                self.pipes.remove(pipe)
                
        # Spawn new pipes
        self.pipe_spawn_timer += 1
        if self.pipe_spawn_timer >= 90:  # Spawn every ~1.5 seconds at 60fps
            self.spawn_pipe()
            self.pipe_spawn_timer = 0
            
        # Scroll background
        self.background_x -= 1
        if self.background_x <= -50:
            self.background_x = 0
            
        return None
    
    def draw_background(self):
        """Draw animated background"""
        # Sky gradient
        for y in range(0, SCREEN_HEIGHT // 2, 2):
            color_intensity = 135 + int(y * 120 / (SCREEN_HEIGHT // 2))
            pygame.draw.rect(self.screen, (135, 206, color_intensity), 
                           (0, y, SCREEN_WIDTH, 2))
        
        # Ground
        ground_color = (222, 184, 135)
        pygame.draw.rect(self.screen, ground_color, 
                        (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        
        # Ground texture
        for x in range(self.background_x, SCREEN_WIDTH + 50, 50):
            pygame.draw.rect(self.screen, (205, 170, 125), 
                           (x, SCREEN_HEIGHT - 100, 45, 5))
            pygame.draw.rect(self.screen, (139, 115, 85), 
                           (x, SCREEN_HEIGHT - 20, 45, 5))
        
        # Clouds
        cloud_positions = [(200, 80), (400, 120), (600, 60), (800, 100)]
        for i, (base_x, y) in enumerate(cloud_positions):
            x = (base_x + self.background_x * 0.3 + i * 20) % (SCREEN_WIDTH + 100)
            # Cloud circles
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), y), 25)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x + 20), y), 20)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x - 15), y + 5), 18)
    
    def draw_ui(self):
        """Draw user interface elements"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Score
        score_text = font_large.render(str(self.score), True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        # Score shadow
        score_shadow = font_large.render(str(self.score), True, (0, 0, 0))
        shadow_rect = score_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, 83))
        self.screen.blit(score_shadow, shadow_rect)
        self.screen.blit(score_text, score_rect)
        
        if not self.started and not self.game_over:
            # Start instructions
            title_text = font_large.render("CLAPPY BIRD", True, (255, 215, 0))
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            self.screen.blit(title_text, title_rect)
            
            # Show clapping instructions with finger gun fallback
            if self.clap_available:
                instruction_text = font_medium.render("Clap to Start!", True, (255, 255, 255))
                control_text = font_small.render("Clap your hands to make the bird jump", True, (200, 200, 200))
            else:
                instruction_text = font_medium.render("Make Finger Gun to Start!", True, (255, 255, 255))
                control_text = font_small.render("Point finger gun to make the bird jump (clap detection failed)", True, (200, 200, 200))
            
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(instruction_text, instruction_rect)
            
            control_rect = control_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(control_text, control_rect)
            
        elif self.game_over:
            # Game over screen
            game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(game_over_text, game_over_rect)
            
            final_score_text = font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
            final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(final_score_text, final_score_rect)
            
            restart_text = font_small.render("Press R to Restart or ESC for Menu", True, (200, 200, 200))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(restart_text, restart_rect)
        
        # ESC instruction
        esc_text = font_small.render("ESC: Menu", True, (150, 150, 150))
        self.screen.blit(esc_text, (10, 10))
    
    def draw(self):
        """Draw the game"""
        # Clear the screen first to prevent menu overlap
        self.screen.fill((0, 0, 0))
        
        self.draw_background()
        
        # Draw pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)
            
        # Draw bird
        self.bird.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        # Draw camera feed with clap detection (custom method)
        self.draw_camera_with_clap_detection(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        
        return None
    
    def draw_camera_with_clap_detection(self, x: int, y: int, width: int, height: int):
        """Draw camera feed with clap detection visualization using cached frame"""
        try:
            # Use cached frame from update() for better performance
            if self.current_frame is not None:
                # Convert frame for pygame and mirror it
                frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.flip(frame_rgb, 1)  # Mirror horizontally
                frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                
                # Scale frame to fit camera window
                frame_surface = pygame.transform.scale(frame_surface, (width, height))
                
                # Draw frame
                self.screen.blit(frame_surface, (x, y))
                
                # Draw clap status text
                font = pygame.font.Font(None, 24)
                if self.current_clap_detected:
                    status_text = font.render("CLAP!", True, (0, 255, 0))
                    self.screen.blit(status_text, (x + 5, y + height - 25))
                else:
                    hands_count = self.current_debug_info.get('hands_detected', 0)
                    if hands_count >= 2:
                        status_text = font.render("Ready to clap", True, (255, 255, 0))
                        self.screen.blit(status_text, (x + 5, y + height - 25))
                    elif hands_count == 1:
                        status_text = font.render("Need both hands", True, (255, 165, 0))
                        self.screen.blit(status_text, (x + 5, y + height - 25))
                    else:
                        status_text = font.render("Show hands", True, (255, 255, 255))
                        self.screen.blit(status_text, (x + 5, y + height - 25))
            else:
                # No frame available - draw black rectangle
                pygame.draw.rect(self.screen, (0, 0, 0), (x, y, width, height))
                font = pygame.font.Font(None, 24)
                error_text = font.render("No Camera", True, (255, 0, 0))
                self.screen.blit(error_text, (x + 5, y + 5))
                
        except Exception as e:
            print(f"Error drawing camera with clap detection: {e}")
            # Draw a black rectangle as fallback
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, width, height))
            font = pygame.font.Font(None, 24)
            error_text = font.render("Camera Error", True, (255, 0, 0))
            self.screen.blit(error_text, (x + 5, y + 5))