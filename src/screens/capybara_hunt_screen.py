"""
Capybara Hunt - Duck Hunt inspired game mode with flying capybaras
"""

# Standard library imports
import math
import random
import time
from typing import List, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    BLACK,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    GAME_STATE_MENU,
    GRAY,
    GREEN,
    PURPLE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    WHITE,
    YELLOW,
)
from utils.sound_manager import get_sound_manager
from utils.ui_components import Button


class FlyingCapybara:
    """A flying capybara target in the game"""

    def __init__(self, start_x: float, start_y: float, direction: str, speed_multiplier: float = 1.0):
        """
        Initialize a flying capybara
        
        Args:
            start_x: Starting X position
            start_y: Starting Y position
            direction: Flight direction ('left', 'right', 'diagonal_left', 'diagonal_right')
            speed_multiplier: Speed multiplier for difficulty
        """
        self.x = start_x
        self.y = start_y
        self.direction = direction
        self.speed_multiplier = speed_multiplier
        
        # Visual properties
        self.size = 60
        self.color = (139, 90, 43)  # Brown color for capybara
        self.alive = True
        self.hit_time = None
        self.fall_speed = 0
        
        # Flight properties
        self.base_speed = 150  # pixels per second (reduced for better gameplay)
        self.vertical_speed = 0
        self.flight_time = 0
        self.escape_time = random.uniform(4.0, 6.0)  # More time before escaping
        
        # Set initial velocities based on direction
        if direction == 'left':
            self.vx = -self.base_speed * speed_multiplier
            self.vy = random.uniform(-80, -120) * speed_multiplier  # Upward movement
        elif direction == 'right':
            self.vx = self.base_speed * speed_multiplier
            self.vy = random.uniform(-80, -120) * speed_multiplier  # Upward movement
        elif direction == 'diagonal_left':
            self.vx = -self.base_speed * 0.6 * speed_multiplier  # Slower horizontal
            self.vy = -self.base_speed * 0.8 * speed_multiplier  # More vertical
        else:  # diagonal_right
            self.vx = self.base_speed * 0.6 * speed_multiplier  # Slower horizontal
            self.vy = -self.base_speed * 0.8 * speed_multiplier  # More vertical
            
        # Animation
        self.wing_flap_timer = 0
        self.wing_up = True
        
        # Generate capybara shape
        self.generate_capybara_art()
        
    def generate_capybara_art(self):
        """Generate simple capybara art"""
        # We'll draw this dynamically in the draw method
        pass
        
    def update(self, dt: float) -> bool:
        """
        Update capybara position and state
        
        Returns:
            True if capybara should be removed (escaped or fell off screen)
        """
        self.flight_time += dt
        
        if self.alive:
            # Update position
            self.x += self.vx * dt
            self.y += self.vy * dt
            
            # Add some wave motion for more natural flight
            wave_amplitude = 20
            wave_frequency = 2
            self.y += math.sin(self.flight_time * wave_frequency) * wave_amplitude * dt
            
            # Wing flapping animation
            self.wing_flap_timer += dt
            if self.wing_flap_timer > 0.2:  # Flap every 0.2 seconds
                self.wing_up = not self.wing_up
                self.wing_flap_timer = 0
            
            # Check if escaped (off screen or time limit)
            if (self.x < -self.size * 2 or self.x > SCREEN_WIDTH + self.size * 2 or 
                self.y < -self.size * 2 or self.flight_time > self.escape_time):
                return True
                
        else:
            # Falling after being shot
            self.fall_speed += 800 * dt  # Gravity
            self.y += self.fall_speed * dt
            
            # Slight horizontal drift while falling
            self.x += random.uniform(-20, 20) * dt
            
            # Remove when fallen off screen
            if self.y > SCREEN_HEIGHT + self.size:
                return True
                
        return False
        
    def check_hit(self, x: int, y: int) -> bool:
        """Check if shot hit the capybara"""
        if not self.alive:
            return False
            
        # Calculate distance from center
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Hit if within radius (generous hitbox)
        if distance < self.size:
            self.alive = False
            self.hit_time = time.time()
            self.fall_speed = 0
            return True
            
        return False
        
    def draw(self, screen: pygame.Surface):
        """Draw the capybara"""
        if not self.alive:
            # Draw falling/dead capybara
            self._draw_dead_capybara(screen)
        else:
            # Draw flying capybara
            self._draw_flying_capybara(screen)
            
    def _draw_flying_capybara(self, screen: pygame.Surface):
        """Draw a flying capybara with wings"""
        x, y = int(self.x), int(self.y)
        
        # Body (oval)
        body_rect = pygame.Rect(x - self.size//2, y - self.size//3, self.size, self.size * 2//3)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.ellipse(screen, (100, 60, 30), body_rect, 2)  # Darker outline
        
        # Head (circle)
        head_size = self.size // 2
        head_x = x - self.size//2 - head_size//2 if self.vx < 0 else x + self.size//2 - head_size//2
        pygame.draw.circle(screen, self.color, (head_x, y - self.size//4), head_size//2)
        pygame.draw.circle(screen, (100, 60, 30), (head_x, y - self.size//4), head_size//2, 2)
        
        # Snout (smaller circle)
        snout_x = head_x - head_size//3 if self.vx < 0 else head_x + head_size//3
        pygame.draw.circle(screen, (160, 110, 60), (snout_x, y - self.size//4 + 5), head_size//4)
        
        # Eyes
        eye_x = head_x - 5 if self.vx < 0 else head_x + 5
        pygame.draw.circle(screen, BLACK, (eye_x, y - self.size//3), 3)
        pygame.draw.circle(screen, WHITE, (eye_x, y - self.size//3 - 1), 1)
        
        # Wings (animated)
        wing_color = (200, 200, 200)
        wing_width = self.size * 3//4
        wing_height = self.size // 2
        
        if self.wing_up:
            # Wings up position
            left_wing_points = [
                (x - self.size//4, y - self.size//6),
                (x - self.size//4 - wing_width, y - self.size//2),
                (x - self.size//4 - wing_width//2, y - self.size//6)
            ]
            right_wing_points = [
                (x + self.size//4, y - self.size//6),
                (x + self.size//4 + wing_width, y - self.size//2),
                (x + self.size//4 + wing_width//2, y - self.size//6)
            ]
        else:
            # Wings down position
            left_wing_points = [
                (x - self.size//4, y),
                (x - self.size//4 - wing_width, y + self.size//4),
                (x - self.size//4 - wing_width//2, y)
            ]
            right_wing_points = [
                (x + self.size//4, y),
                (x + self.size//4 + wing_width, y + self.size//4),
                (x + self.size//4 + wing_width//2, y)
            ]
            
        pygame.draw.polygon(screen, wing_color, left_wing_points)
        pygame.draw.polygon(screen, (150, 150, 150), left_wing_points, 2)
        pygame.draw.polygon(screen, wing_color, right_wing_points)
        pygame.draw.polygon(screen, (150, 150, 150), right_wing_points, 2)
        
        # Legs (small lines)
        pygame.draw.line(screen, (100, 60, 30), (x - self.size//4, y + self.size//3), 
                        (x - self.size//4, y + self.size//3 + 10), 3)
        pygame.draw.line(screen, (100, 60, 30), (x + self.size//4, y + self.size//3), 
                        (x + self.size//4, y + self.size//3 + 10), 3)
                        
    def _draw_dead_capybara(self, screen: pygame.Surface):
        """Draw a falling/dead capybara"""
        x, y = int(self.x), int(self.y)
        
        # Draw upside down or tumbling
        angle = (time.time() - self.hit_time) * 360  # Rotate while falling
        
        # Simple X eyes to show it's dead
        eye_size = 5
        eye_x = x - 10 if self.vx < 0 else x + 10
        
        # Body (same as alive but no wings)
        body_rect = pygame.Rect(x - self.size//2, y - self.size//3, self.size, self.size * 2//3)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.ellipse(screen, (100, 60, 30), body_rect, 2)
        
        # Head
        head_size = self.size // 2
        head_x = x - self.size//2 - head_size//2 if self.vx < 0 else x + self.size//2 - head_size//2
        pygame.draw.circle(screen, self.color, (head_x, y - self.size//4), head_size//2)
        pygame.draw.circle(screen, (100, 60, 30), (head_x, y - self.size//4), head_size//2, 2)
        
        # X eyes (dead)
        pygame.draw.line(screen, BLACK, (eye_x - eye_size, y - self.size//3 - eye_size),
                        (eye_x + eye_size, y - self.size//3 + eye_size), 2)
        pygame.draw.line(screen, BLACK, (eye_x - eye_size, y - self.size//3 + eye_size),
                        (eye_x + eye_size, y - self.size//3 - eye_size), 2)


class CapybaraHuntScreen(BaseScreen):
    """Capybara Hunt gameplay screen - Duck Hunt inspired"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        # Initialize base class (handles camera, hand tracker, sound manager, settings)
        super().__init__(screen, camera_manager)

        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        self.huge_font = pygame.font.Font(None, 120)

        # Game state
        self.round_number = 1
        self.score = 0
        self.shots_remaining = 3
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6  # Start with 6/10 required
        self.game_over = False
        self.round_complete = False
        self.round_complete_time = 0
        self.paused = False
        
        # UI Buttons for shooting
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None
        
        # Capybara management
        self.capybaras: List[FlyingCapybara] = []
        self.spawn_timer = 0
        self.spawn_delay = 2.0  # Seconds between spawns
        self.current_wave_capybaras = 0  # Capybaras in current wave (1 or 2)
        self.wave_active = False
        
        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200
        
        # Hit tracking for round
        self.hit_markers = []  # List of booleans for hit/miss display
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        
        # Background
        self.create_background()
        
        # Debug console (for pause menu commands)
        self.console_active = False
        self.console_input = ""
        self.console_message = ""
        self.console_message_time = 0
        
    def create_background(self):
        """Create a nature/hunting background"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Sky gradient
        for y in range(SCREEN_HEIGHT * 2 // 3):
            progress = y / (SCREEN_HEIGHT * 2 // 3)
            color = (
                int(135 + (206 - 135) * progress),  # Sky blue to lighter
                int(206 + (235 - 206) * progress),
                int(235 + (250 - 235) * progress)
            )
            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))
            
        # Ground
        ground_color = (34, 139, 34)  # Forest green
        pygame.draw.rect(self.background, ground_color, 
                        (0, SCREEN_HEIGHT * 2 // 3, SCREEN_WIDTH, SCREEN_HEIGHT // 3))
                        
        # Add some grass texture
        for _ in range(200):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(SCREEN_HEIGHT * 2 // 3, SCREEN_HEIGHT)
            height = random.randint(5, 15)
            pygame.draw.line(self.background, (46, 125, 50), (x, y), (x, y - height), 1)
            
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        if event.type == pygame.KEYDOWN:
            # Handle console input when active
            if self.console_active:
                if event.key == pygame.K_RETURN:
                    self._execute_console_command()
                    self.console_input = ""
                    self.console_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.console_active = False
                    self.console_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.console_input = self.console_input[:-1]
                else:
                    if event.unicode and len(self.console_input) < 30:
                        self.console_input += event.unicode
                return None
            
            # Normal key handling
            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                if not self.game_over and not self.round_complete:
                    self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_RETURN and (self.game_over or self.round_complete):
                if self.game_over:
                    self.reset_game()
                elif self.round_complete:
                    self.start_next_round()
            elif event.key == pygame.K_SLASH and self.paused:  # Open console with /
                self.console_active = True
                self.console_input = "/"
                    
        return None
        
    def reset_game(self) -> None:
        """Reset the entire game"""
        self.round_number = 1
        self.score = 0
        self.shots_remaining = 3
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6
        self.game_over = False
        self.round_complete = False
        self.capybaras.clear()
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False
        self.hand_tracker.reset_tracking_state()
        self.shoot_pos = None
        self.crosshair_pos = None
        # Reset buttons
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None
        
    def start_next_round(self) -> None:
        """Start the next round"""
        self.round_number += 1
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.shots_remaining = 3
        self.round_complete = False
        self.capybaras.clear()
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False
        # Reset continue button for next round
        self.continue_button = None
        
        # Increase difficulty
        self.required_hits = min(10, 6 + (self.round_number - 1) // 3)  # Gradually increase required hits
        self.spawn_delay = max(1.0, 2.0 - self.round_number * 0.1)  # Faster spawns
        
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        # Process hand tracking always (for button shooting)
        self._process_hand_tracking()
        
        # Handle button shooting in round complete or game over states
        if self.round_complete:
            if self.continue_button and self.shoot_detected:
                if self._check_button_hit(self.continue_button):
                    self.shoot_detected = False
                    self.start_next_round()
            return None
            
        if self.game_over:
            if self.shoot_detected:
                if self.retry_button and self._check_button_hit(self.retry_button):
                    self.shoot_detected = False
                    self.reset_game()
                elif self.menu_button and self._check_button_hit(self.menu_button):
                    self.shoot_detected = False
                    return GAME_STATE_MENU
            return None
        
        if self.paused:
            return None
            
        # Spawn capybaras
        if not self.wave_active and self.capybaras_spawned < self.capybaras_per_round:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_wave()
                self.spawn_timer = 0
                
        # Update capybaras
        capybaras_to_remove = []
        for capybara in self.capybaras:
            if capybara.update(dt):
                capybaras_to_remove.append(capybara)
                if capybara.alive:
                    # Missed (escaped)
                    self.hit_markers.append(False)
                    self.wave_active = False
                    self.shots_remaining = 3  # Reset shots for next wave
                    
        for capybara in capybaras_to_remove:
            self.capybaras.remove(capybara)
            
        # Check if wave is complete (all capybaras gone)
        if self.wave_active and len(self.capybaras) == 0:
            self.wave_active = False
            self.shots_remaining = 3  # Reset shots for next wave
            
        # Check round completion
        if self.capybaras_spawned >= self.capybaras_per_round and len(self.capybaras) == 0:
            if self.capybaras_hit >= self.required_hits:
                self.round_complete = True
                self.round_complete_time = time.time()
                # Perfect round bonus
                if self.capybaras_hit == self.capybaras_per_round:
                    self.score += 1000 * self.round_number
            else:
                self.game_over = True
            
        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
        
        return None
        
    def spawn_wave(self):
        """Spawn a wave of 1 or 2 capybaras"""
        self.wave_active = True
        
        # Determine number of capybaras (1 for early rounds, 2 for later)
        if self.round_number <= 2:
            num_capybaras = 1
        else:
            num_capybaras = 2 if self.capybaras_spawned < self.capybaras_per_round - 1 else 1
            
        self.current_wave_capybaras = min(num_capybaras, self.capybaras_per_round - self.capybaras_spawned)
        
        # Spawn capybaras from grass area (2/3 down the screen)
        grass_line = SCREEN_HEIGHT * 2 // 3
        
        for i in range(self.current_wave_capybaras):
            # Spawn in the middle 60% of the screen to give better shooting opportunity
            # Avoid edges: spawn between 20% and 80% of screen width
            start_x = random.randint(int(SCREEN_WIDTH * 0.2), int(SCREEN_WIDTH * 0.8))
            
            # Start just at or slightly below the grass line so they emerge from grass
            start_y = grass_line + random.randint(0, 30)
            
            # Bias directions more upward for better visibility
            # More diagonal_left and diagonal_right for varied but predictable paths
            directions = ['diagonal_left', 'diagonal_right', 'diagonal_left', 'diagonal_right', 'left', 'right']
            direction = random.choice(directions)
            
            # If spawning on the left side, bias toward right movement
            # If spawning on the right side, bias toward left movement
            # This keeps them in play longer
            if start_x < SCREEN_WIDTH * 0.4:
                # On left side, prefer right/diagonal_right
                direction = random.choice(['right', 'diagonal_right', 'diagonal_right'])
            elif start_x > SCREEN_WIDTH * 0.6:
                # On right side, prefer left/diagonal_left
                direction = random.choice(['left', 'diagonal_left', 'diagonal_left'])
            
            # Speed increases with round
            speed_multiplier = 1.0 + (self.round_number - 1) * 0.15
            
            capybara = FlyingCapybara(start_x, start_y, direction, speed_multiplier)
            self.capybaras.append(capybara)
            self.capybaras_spawned += 1
            
    def _process_hand_tracking(self) -> None:
        """Process hand tracking and shooting detection"""
        # Use base class method for tracking
        self.process_finger_gun_tracking()
        
        # Only handle shooting in active game
        if not self.game_over and not self.round_complete and not self.paused:
            # Check if we should shoot
            if self.shoot_detected and self.shots_remaining > 0:
                self._handle_shoot(self.crosshair_pos)
                self.shoot_detected = False  # Reset after handling
                
    def _check_button_hit(self, button: Button) -> bool:
        """Check if crosshair is over button and shooting"""
        if self.crosshair_pos and button and button.rect.collidepoint(self.crosshair_pos):
            # Play shoot sound
            self.sound_manager.play("shoot")
            return True
        return False
            
    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        if self.shots_remaining <= 0 or not self.wave_active:
            return
            
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.shots_remaining -= 1
        
        # Play shoot sound
        self.sound_manager.play("shoot")
        
        # Check for hits
        hit_any = False
        for capybara in self.capybaras:
            if capybara.check_hit(shoot_position[0], shoot_position[1]):
                self.score += 100 * self.round_number
                self.capybaras_hit += 1
                self.hit_markers.append(True)
                self.sound_manager.play("hit")
                hit_any = True
                break
                
        # Check if out of ammo and no hits
        if self.shots_remaining == 0 and not hit_any:
            # Mark remaining capybaras as missed
            for capybara in self.capybaras:
                if capybara.alive:
                    self.hit_markers.append(False)
                    
    def draw(self) -> None:
        """Draw the game screen"""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        if self.paused:
            self._draw_pause_screen()
            return
            
        if self.game_over:
            self._draw_game_over_screen()
            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            self._draw_camera_feed()
            return
            
        if self.round_complete:
            self._draw_round_complete_screen()
            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            self._draw_camera_feed()
            return
            
        # Draw capybaras
        for capybara in self.capybaras:
            capybara.draw(self.screen)
        
        # Draw crosshair
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            
        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
            self._draw_shoot_animation(self.shoot_pos)
            
        # Draw UI
        self._draw_ui()
        
        # Draw camera feed
        self._draw_camera_feed()
        
        # Draw debug overlay if enabled
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()
            
    def _draw_shoot_animation(self, pos: tuple) -> None:
        """Draw shooting animation"""
        current_time = pygame.time.get_ticks()
        time_since_shoot = current_time - self.shoot_animation_time
        animation_progress = time_since_shoot / self.shoot_animation_duration
        
        if animation_progress < 1.0:
            # Bullet impact effect
            for i in range(3):
                radius = int((20 + i * 15) * animation_progress)
                alpha = int(255 * (1 - animation_progress) / (i + 1))
                
                if alpha > 0:
                    impact_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    color = YELLOW if i == 0 else WHITE
                    pygame.draw.circle(impact_surface, (*color, alpha), (radius, radius), radius, max(1, 3 - i))
                    self.screen.blit(impact_surface, (pos[0] - radius, pos[1] - radius))
                    
    def _draw_ui(self) -> None:
        """Draw game UI elements"""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Round
        round_text = self.font.render(f"Round: {self.round_number}", True, WHITE)
        self.screen.blit(round_text, (10, 50))
        
        # Shots remaining
        shot_text = self.font.render(f"Shots: {self.shots_remaining}", True, 
                                    WHITE if self.shots_remaining > 0 else (255, 0, 0))
        self.screen.blit(shot_text, (10, 90))
        
        # Hit/Pass meter (like Duck Hunt)
        meter_x = SCREEN_WIDTH // 2 - 150
        meter_y = SCREEN_HEIGHT - 80
        
        # Draw hit markers
        for i in range(self.capybaras_per_round):
            x = meter_x + i * 30
            if i < len(self.hit_markers):
                color = GREEN if self.hit_markers[i] else (255, 0, 0)
            else:
                color = WHITE
            pygame.draw.rect(self.screen, color, (x, meter_y, 25, 25))
            pygame.draw.rect(self.screen, BLACK, (x, meter_y, 25, 25), 2)
            
        # Draw pass line
        pass_line_x = meter_x + (self.required_hits - 1) * 30 + 25
        pygame.draw.line(self.screen, YELLOW, (pass_line_x, meter_y - 5), 
                        (pass_line_x, meter_y + 30), 3)
        
        # Required hits text
        req_text = self.small_font.render(f"Need {self.required_hits}/{self.capybaras_per_round}", True, WHITE)
        req_rect = req_text.get_rect(center=(SCREEN_WIDTH // 2, meter_y - 20))
        self.screen.blit(req_text, req_rect)
        
        # FPS counter
        fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, GRAY)
        fps_rect = fps_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.screen.blit(fps_text, fps_rect)
        
        # Controls hint (like in Doomsday)
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Reset", True, GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        self.screen.blit(controls_text, controls_rect)
        
    def _draw_camera_feed(self) -> None:
        """Draw camera feed in corner"""
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
        
    def _draw_pause_screen(self) -> None:
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.big_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(pause_text, pause_rect)
        
        # Draw console if active
        if self.console_active:
            # Console background
            console_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 20, 400, 40)
            pygame.draw.rect(self.screen, (40, 40, 40), console_rect)
            pygame.draw.rect(self.screen, WHITE, console_rect, 2)
            
            # Console text
            console_text = self.font.render(self.console_input, True, WHITE)
            self.screen.blit(console_text, (console_rect.x + 10, console_rect.y + 10))
            
            # Console hint
            hint_text = self.small_font.render(
                "Commands: /round #, /score #, /perfect, /miss | ESC to cancel", True, (200, 200, 200)
            )
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, console_rect.bottom + 20))
            self.screen.blit(hint_text, hint_rect)
        else:
            instructions = [
                "Press P or SPACE to resume",
                "Press / to open debug console",
                "Press ESC to return to menu",
                "Press R to reset game",
            ]
            
            for i, instruction in enumerate(instructions):
                text = self.font.render(instruction, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
                self.screen.blit(text, text_rect)
        
        # Show console message if recent
        if self.console_message and time.time() - self.console_message_time < 3:
            msg_text = self.font.render(self.console_message, True, GREEN)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
            self.screen.blit(msg_text, msg_rect)
            
    def _draw_game_over_screen(self):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.huge_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Stats
        stats = [
            f"Final Score: {self.score}",
            f"Rounds Completed: {self.round_number - 1}",
            f"Capybaras Hit: {self.capybaras_hit}/{self.capybaras_per_round}"
        ]
        
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)
            
        # Create shootable buttons
        button_width = 150
        button_height = 50
        button_y = SCREEN_HEIGHT // 2 + 180
        
        # Retry button
        if not self.retry_button:
            self.retry_button = Button(
                SCREEN_WIDTH // 2 - button_width - 20,
                button_y,
                button_width,
                button_height,
                "RETRY",
                self.font
            )
        self.retry_button.draw(self.screen)
        
        # Menu button
        if not self.menu_button:
            self.menu_button = Button(
                SCREEN_WIDTH // 2 + 20,
                button_y,
                button_width,
                button_height,
                "MENU",
                self.font
            )
        self.menu_button.draw(self.screen)
        
        # Highlight buttons if aimed at
        if self.crosshair_pos:
            if self.retry_button.rect.collidepoint(self.crosshair_pos):
                pygame.draw.rect(self.screen, UI_ACCENT, self.retry_button.rect, 3)
            if self.menu_button.rect.collidepoint(self.crosshair_pos):
                pygame.draw.rect(self.screen, UI_ACCENT, self.menu_button.rect, 3)
        
        # Instructions
        instruction_text = self.small_font.render("Shoot a button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, button_y + 70))
        self.screen.blit(instruction_text, instruction_rect)
        
    def _draw_round_complete_screen(self):
        """Draw round complete screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Check for perfect round
        if self.capybaras_hit == self.capybaras_per_round:
            complete_text = self.big_font.render(f"PERFECT!! +{1000 * self.round_number}", True, YELLOW)
        else:
            complete_text = self.big_font.render(f"ROUND {self.round_number} COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(complete_text, complete_rect)
        
        # Stats
        stats_text = self.font.render(f"Hit: {self.capybaras_hit}/{self.capybaras_per_round} | Score: {self.score}", 
                                     True, WHITE)
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(stats_text, stats_rect)
        
        # Create shootable continue button
        button_width = 200
        button_height = 60
        button_y = SCREEN_HEIGHT // 2 + 80
        
        if not self.continue_button:
            self.continue_button = Button(
                SCREEN_WIDTH // 2 - button_width // 2,
                button_y,
                button_width,
                button_height,
                "CONTINUE",
                self.font
            )
        self.continue_button.draw(self.screen)
        
        # Highlight button if aimed at
        if self.crosshair_pos and self.continue_button.rect.collidepoint(self.crosshair_pos):
            pygame.draw.rect(self.screen, UI_ACCENT, self.continue_button.rect, 3)
        
        # Instructions
        instruction_text = self.small_font.render("Shoot the button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, button_y + 80))
        self.screen.blit(instruction_text, instruction_rect)
        
    def _execute_console_command(self):
        """Execute debug console command"""
        command = self.console_input.strip().lower()
        
        if command.startswith("/round "):
            try:
                round_num = int(command.split()[1])
                if round_num > 0:
                    self._jump_to_round(round_num)
                    self.console_message = f"Jumped to Round {round_num}"
                else:
                    self.console_message = "Round number must be positive"
            except Exception:
                self.console_message = "Invalid round number"
                
        elif command.startswith("/score "):
            try:
                score = int(command.split()[1])
                self.score = max(0, score)
                self.console_message = f"Score set to {self.score}"
            except Exception:
                self.console_message = "Invalid score"
                
        elif command == "/perfect":
            # Set current round to perfect score
            self.capybaras_hit = self.capybaras_per_round
            self.hit_markers = [True] * self.capybaras_per_round
            self.console_message = "Perfect round activated"
            
        elif command == "/miss":
            # Force a miss for testing game over
            self.capybaras_hit = 0
            self.hit_markers = [False] * self.capybaras_per_round
            self.console_message = "Forced miss - prepare for game over"
            
        elif command == "/skip":
            # Skip to round complete
            if not self.round_complete and not self.game_over:
                self.capybaras_spawned = self.capybaras_per_round
                self.capybaras.clear()
                self.wave_active = False
                self.console_message = "Skipped to round end"
            else:
                self.console_message = "Cannot skip - round already complete"
                
        else:
            self.console_message = "Unknown command. Try: /round #, /score #, /perfect, /miss, /skip"
            
        self.console_message_time = time.time()
        
    def _jump_to_round(self, round_num: int):
        """Jump directly to a specific round"""
        # Reset game state
        self.round_number = round_num
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.shots_remaining = 3
        self.round_complete = False
        self.game_over = False
        self.capybaras.clear()
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False
        
        # Adjust difficulty for the round
        self.required_hits = min(10, 6 + (round_num - 1) // 3)
        self.spawn_delay = max(1.0, 2.0 - round_num * 0.1)