"""
Doomsday mode game screen with doom-style enemy waves
"""

import pygame
import cv2
import time
import math
import random
from typing import Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from utils.sound_manager import get_sound_manager
from game.hand_tracker import HandTracker
from game.enemy import EnemyManager

class DoomsdayScreen:
    """Doomsday mode gameplay screen with enemy waves"""
    
    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        self.screen = screen
        self.camera_manager = camera_manager
        
        # Initialize game components
        self.hand_tracker = HandTracker()
        self.enemy_manager = EnemyManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.sound_manager = get_sound_manager()
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        self.huge_font = pygame.font.Font(None, 120)
        
        # Game state
        self.score = 0
        self.player_health = 100
        self.max_health = 100
        self.game_time = 0
        self.paused = False
        self.game_over = False
        self.game_over_time = 0
        
        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200
        self.muzzle_flash_time = 0
        self.last_shoot_time = 0
        self.rapid_fire_count = 0
        
        # Crosshair state
        self.crosshair_pos = None
        self.crosshair_color = GREEN
        
        # Screen effects
        self.damage_flash_time = 0
        self.screen_shake_time = 0
        self.screen_shake_intensity = 0
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        
        # Debug mode
        self.debug_mode = False
        
        # Debug console
        self.console_active = False
        self.console_input = ""
        self.console_message = ""
        self.console_message_time = 0
        
        # Background gradient for doom-like atmosphere
        self.current_stage_theme = 1
        self.create_background()
        
        # Music management for stages
        self.current_music_track = None
        self.stage4_alternating_mode = False
        self.music_started = False
        self.current_stage_ambient = None
    
    def create_background(self):
        """Create a doom-like background with gradient based on current stage"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Define color themes for different stages
        themes = {
            1: {  # Stage 1-2: Classic Doom brown/gray
                'sky_base': (30, 20, 20),
                'sky_end': (50, 35, 35),
                'ground_base': (40, 30, 25),
                'ground_end': (70, 50, 40),
                'horizon': (60, 40, 40),
                'grid': (40, 30, 30)
            },
            2: {  # Stage 3-4: Hellish red
                'sky_base': (40, 10, 10),
                'sky_end': (80, 20, 20),
                'ground_base': (60, 20, 15),
                'ground_end': (100, 40, 30),
                'horizon': (120, 30, 30),
                'grid': (60, 20, 20)
            },
            3: {  # Stage 5-6: Demonic purple/dark
                'sky_base': (20, 10, 30),
                'sky_end': (40, 20, 60),
                'ground_base': (30, 15, 40),
                'ground_end': (60, 30, 80),
                'horizon': (80, 40, 100),
                'grid': (40, 20, 50)
            },
            4: {  # Stage 7+: Apocalyptic orange/black
                'sky_base': (30, 15, 5),
                'sky_end': (60, 30, 10),
                'ground_base': (40, 20, 5),
                'ground_end': (80, 40, 15),
                'horizon': (100, 50, 20),
                'grid': (50, 25, 10)
            }
        }
        
        # Get current theme based on wave
        theme = themes.get(self.current_stage_theme, themes[1])
        
        # Create gradient from theme colors
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            
            if y < SCREEN_HEIGHT * 0.4:  # Sky
                sky_progress = y / (SCREEN_HEIGHT * 0.4)
                color = (
                    int(theme['sky_base'][0] + (theme['sky_end'][0] - theme['sky_base'][0]) * sky_progress),
                    int(theme['sky_base'][1] + (theme['sky_end'][1] - theme['sky_base'][1]) * sky_progress),
                    int(theme['sky_base'][2] + (theme['sky_end'][2] - theme['sky_base'][2]) * sky_progress)
                )
            else:  # Ground
                ground_progress = (y - SCREEN_HEIGHT * 0.4) / (SCREEN_HEIGHT * 0.6)
                color = (
                    int(theme['ground_base'][0] + (theme['ground_end'][0] - theme['ground_base'][0]) * ground_progress),
                    int(theme['ground_base'][1] + (theme['ground_end'][1] - theme['ground_base'][1]) * ground_progress),
                    int(theme['ground_base'][2] + (theme['ground_end'][2] - theme['ground_base'][2]) * ground_progress)
                )
            
            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))
        
        # Add horizon line
        pygame.draw.line(self.background, theme['horizon'], 
                        (0, int(SCREEN_HEIGHT * 0.4)), 
                        (SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.4)), 2)
        
        # Store grid color for later use
        self.grid_color = theme['grid']
    
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
                if not self.game_over:
                    self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_RETURN and self.game_over:
                self.reset_game()
            elif event.key == pygame.K_d:
                self.debug_mode = not self.debug_mode
            elif event.key == pygame.K_SLASH and self.paused:  # Open console with /
                self.console_active = True
                self.console_input = "/"
        
        return None
    
    def reset_game(self) -> None:
        """Reset the game state"""
        self.score = 0
        self.player_health = self.max_health
        self.game_time = 0
        self.game_over = False
        self.game_over_time = 0
        self.enemy_manager.clear_all_enemies()
        self.hand_tracker.reset_tracking_state()
        self.shoot_pos = None
        self.crosshair_pos = None
        self.damage_flash_time = 0
        self.screen_shake_time = 0
        
        # Reset stage and music
        self.current_stage_theme = 1
        self.stage4_alternating_mode = False
        self.music_started = False
        self.current_stage_ambient = None
        self.sound_manager.stop_stage_effect()  # Stop any ambient effects
        self.create_background()
    
    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        if self.paused or self.game_over:
            return None
        
        # Start music on first update when game is active
        if not self.music_started:
            self.music_started = True
            self._start_stage_music(1)
        
        self.game_time += dt
        
        # Update enemies and check for damage
        damage, enemies_killed = self.enemy_manager.update(dt, current_time / 1000.0)
        
        if damage > 0:
            self.take_damage(damage)
        
        # Update stage theme based on wave
        new_theme = min(4, (self.enemy_manager.wave_number - 1) // 2 + 1)
        if new_theme != self.current_stage_theme:
            self.current_stage_theme = new_theme
            self.create_background()
            self._start_stage_music(new_theme)
        
        # Handle Stage 4+ alternating music
        if self.current_stage_theme >= 4 and self.stage4_alternating_mode:
            self._handle_stage4_music_alternation()
        
        # Update screen effects
        if self.damage_flash_time > 0:
            self.damage_flash_time -= dt
        
        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt
        
        if self.muzzle_flash_time > 0:
            self.muzzle_flash_time -= dt
        
        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
        
        # Process hand tracking
        self._process_hand_tracking()
        
        return None
    
    def take_damage(self, damage: int):
        """Player takes damage"""
        self.player_health -= damage
        self.damage_flash_time = 0.3
        self.screen_shake_time = 0.2
        self.screen_shake_intensity = 10
        
        if self.player_health <= 0:
            self.player_health = 0
            self.game_over = True
            self.game_over_time = time.time()
    
    def _process_hand_tracking(self) -> None:
        """Process hand tracking and shooting detection"""
        ret, frame = self.camera_manager.read_frame()
        if not ret or frame is None:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
            return
        
        # Process frame for hand detection
        processed_frame, results = self.hand_tracker.process_frame(frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on camera frame
                self.hand_tracker.draw_landmarks(processed_frame, hand_landmarks)
                
                # Detect finger gun
                is_gun, index_coords, thumb_tip, middle_mcp, thumb_middle_dist, confidence = \
                    self.hand_tracker.detect_finger_gun(
                        hand_landmarks, 
                        self.camera_manager.frame_width, 
                        self.camera_manager.frame_height
                    )
                
                if is_gun and index_coords:
                    cv2.circle(processed_frame, index_coords, 15, (0, 255, 0), -1)
                    
                    # Map finger position to game screen
                    game_x = int((index_coords[0] / self.camera_manager.frame_width) * SCREEN_WIDTH)
                    game_y = int((index_coords[1] / self.camera_manager.frame_height) * SCREEN_HEIGHT)
                    self.crosshair_pos = (game_x, game_y)
                    
                    # Set crosshair color based on detection mode
                    if self.hand_tracker.detection_mode == "standard":
                        self.crosshair_color = GREEN
                    elif self.hand_tracker.detection_mode == "depth":
                        self.crosshair_color = YELLOW
                    elif self.hand_tracker.detection_mode == "wrist_angle":
                        self.crosshair_color = PURPLE
                    else:
                        self.crosshair_color = WHITE
                    
                    # Detect shooting gesture
                    shoot_this_frame = self.hand_tracker.detect_shooting_gesture(thumb_tip, thumb_middle_dist)
                    if shoot_this_frame:
                        self._handle_shoot(self.crosshair_pos)
                        cv2.putText(processed_frame, "SHOOT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    self.crosshair_pos = None
        else:
            self.hand_tracker.reset_tracking_state()
            self.crosshair_pos = None
        
        # Store processed frame for display
        self._processed_camera_frame = processed_frame
    
    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        current_time = time.time()
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.muzzle_flash_time = 0.1
        
        # Play shoot sound
        self.sound_manager.play('shoot')
        
        # Check for rapid fire (panic mode)
        if current_time - self.last_shoot_time < 0.3:
            self.rapid_fire_count += 1
        else:
            self.rapid_fire_count = 0
        self.last_shoot_time = current_time
        
        # If rapid firing and enemies are close, push them all back
        if self.rapid_fire_count >= 3:
            closest_distance = self.enemy_manager.get_closest_enemy_distance()
            if closest_distance < 0.3:
                # Panic mode - push all close enemies back
                for enemy in self.enemy_manager.enemies:
                    if enemy.alive and enemy.z < 0.4:
                        enemy.z = min(0.6, enemy.z + 0.2)
                # Big screen shake for panic mode
                self.screen_shake_time = 0.3
                self.screen_shake_intensity = 8
                self.rapid_fire_count = 0
        
        self.screen_shake_time = 0.05
        self.screen_shake_intensity = 3
        
        # Check for enemy hits (increased damage for better gameplay)
        score_gained, killed = self.enemy_manager.check_hit(
            shoot_position[0], shoot_position[1], damage=25
        )
        
        if score_gained > 0:
            self.score += score_gained
            if killed:
                # Bigger shake for kills
                self.screen_shake_time = 0.1
                self.screen_shake_intensity = 5
                self.sound_manager.play('enemy_death')
            else:
                self.sound_manager.play('enemy_hit')
    
    def draw(self) -> None:
        """Draw the game screen"""
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake_time > 0:
            shake_offset_x = int((pygame.time.get_ticks() % 100 - 50) / 50 * self.screen_shake_intensity)
            shake_offset_y = int((pygame.time.get_ticks() % 117 - 58) / 58 * self.screen_shake_intensity)
        
        # Create drawing surface with shake
        draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Draw background
        draw_surface.blit(self.background, (0, 0))
        
        if self.paused:
            self._draw_pause_screen()
            return
        
        if self.game_over:
            self._draw_game_over_screen(draw_surface)
            self.screen.blit(draw_surface, (shake_offset_x, shake_offset_y))
            self._draw_camera_feed()
            return
        
        # Draw 3D floor grid for depth perception
        self._draw_floor_grid(draw_surface)
        
        # Add atmospheric effects based on stage
        self._draw_stage_effects(draw_surface)
        
        # Draw enemies with blood physics
        self.enemy_manager.draw(draw_surface, self.debug_mode, dt=1.0/60.0)
        
        # Draw crosshair
        if self.crosshair_pos:
            self._draw_crosshair(draw_surface, self.crosshair_pos, self.crosshair_color)
        
        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if (self.shoot_pos and 
            current_time - self.shoot_animation_time < self.shoot_animation_duration):
            self._draw_shoot_animation(draw_surface, self.shoot_pos)
        
        # Draw muzzle flash
        if self.muzzle_flash_time > 0:
            self._draw_muzzle_flash(draw_surface)
        
        # Apply damage flash
        if self.damage_flash_time > 0:
            damage_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            damage_surface.set_alpha(int(100 * (self.damage_flash_time / 0.3)))
            damage_surface.fill((255, 0, 0))
            draw_surface.blit(damage_surface, (0, 0))
        
        # Draw UI
        self._draw_ui(draw_surface)
        
        # Blit everything with shake
        self.screen.blit(draw_surface, (shake_offset_x, shake_offset_y))
        
        # Draw camera feed (not affected by shake)
        self._draw_camera_feed()
    
    def _draw_stage_effects(self, surface: pygame.Surface):
        """Draw atmospheric effects based on current stage"""
        if self.current_stage_theme == 2:
            # Hell's Gates - add fire particles
            for i in range(5):
                x = random.randint(0, SCREEN_WIDTH)
                y = SCREEN_HEIGHT - random.randint(0, 100)
                size = random.randint(2, 6)
                color = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0)])
                pygame.draw.circle(surface, color, (x, y), size)
                
                # Occasionally play fire crackle sound for variety alongside ambient
                if size >= 5 and random.random() < 0.003:  # 0.3% chance per frame for large particles
                    self.sound_manager.play_one_shot_effect('stage2_fire_crackle', volume=0.1)
        
        elif self.current_stage_theme == 3:
            # Demon Realm - add purple mist
            mist_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(3):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(int(SCREEN_HEIGHT * 0.4), SCREEN_HEIGHT)
                radius = random.randint(50, 150)
                mist_surface.fill((100, 50, 150, 20), (x - radius, y - radius, radius * 2, radius * 2))
            surface.blit(mist_surface, (0, 0))
        
        elif self.current_stage_theme == 4:
            # FINAL APOCALYPSE
            
            # 1. Falling meteors/debris
            for i in range(8):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, int(SCREEN_HEIGHT * 0.6))
                # Create fiery meteor effect
                meteor_size = random.randint(3, 8)
                # Meteor core
                pygame.draw.circle(surface, (255, 100, 0), (x, y), meteor_size)
                # Fiery trail
                for j in range(5):
                    trail_x = x - j * 3
                    trail_y = y - j * 5
                    trail_size = meteor_size - j
                    if trail_size > 0:
                        color = (255 - j * 30, 50 + j * 20, 0)
                        pygame.draw.circle(surface, color, (trail_x, trail_y), trail_size)
            
            # 2. Ash particles falling
            for i in range(15):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                pygame.draw.circle(surface, (150, 150, 150), (x, y), 1)
            
            # 3. Intense lightning with screen flash
            if random.random() < 0.04:  # 4% chance
                # Play lightning sound effect
                if random.random() < 0.7:  # 70% chance for lightning sound
                    self.sound_manager.play_one_shot_effect('stage4_lightning', volume=0.4)
                else:  # 30% chance for just thunder
                    self.sound_manager.play_one_shot_effect('stage4_thunder', volume=0.3)
                
                # Draw actual lightning bolt
                lightning_x = random.randint(100, SCREEN_WIDTH - 100)
                current_x = lightning_x
                current_y = 0
                for i in range(10):
                    next_x = current_x + random.randint(-30, 30)
                    next_y = current_y + SCREEN_HEIGHT // 10
                    pygame.draw.line(surface, (255, 255, 255), 
                                   (current_x, current_y), (next_x, next_y), 3)
                    pygame.draw.line(surface, (200, 200, 255), 
                                   (current_x, current_y), (next_x, next_y), 1)
                    current_x, current_y = next_x, next_y
                
                # Screen flash
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.set_alpha(60)
                flash_surface.fill((255, 200, 150))
                surface.blit(flash_surface, (0, 0))
            
            # 4. Dark smoke clouds at top
            smoke_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(4):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, int(SCREEN_HEIGHT * 0.3))
                radius = random.randint(40, 100)
                smoke_surface.fill((50, 30, 20, 30), (x - radius, y - radius, radius * 2, radius * 2))
            surface.blit(smoke_surface, (0, 0))
    
    def _draw_floor_grid(self, surface: pygame.Surface):
        """Draw 3D floor grid for perspective"""
        horizon_y = int(SCREEN_HEIGHT * 0.4)
        
        # Use the theme's grid color
        grid_color = self.grid_color if hasattr(self, 'grid_color') else (40, 30, 30)
        
        # Vertical lines (perspective)
        for i in range(-10, 11):
            x_start = SCREEN_WIDTH // 2 + i * 100
            x_end = SCREEN_WIDTH // 2 + i * 20
            pygame.draw.line(surface, grid_color,
                           (x_start, SCREEN_HEIGHT),
                           (x_end, horizon_y), 1)
        
        # Horizontal lines (depth)
        for i in range(10):
            y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (i / 10) ** 0.7
            pygame.draw.line(surface, grid_color,
                           (0, int(y)),
                           (SCREEN_WIDTH, int(y)), 1)
    
    def _draw_crosshair(self, surface: pygame.Surface, pos: tuple, color: tuple) -> None:
        """Draw crosshair at given position"""
        x, y = pos
        size = 25
        thickness = 3
        gap = 8
        
        # Outer circle
        pygame.draw.circle(surface, color, pos, size, thickness)
        
        # Cross lines with gap in center
        pygame.draw.line(surface, color, (x - size - 10, y), (x - gap, y), thickness)
        pygame.draw.line(surface, color, (x + gap, y), (x + size + 10, y), thickness)
        pygame.draw.line(surface, color, (x, y - size - 10), (x, y - gap), thickness)
        pygame.draw.line(surface, color, (x, y + gap), (x, y + size + 10), thickness)
        
        # Center dot
        pygame.draw.circle(surface, color, pos, 2)
    
    def _draw_shoot_animation(self, surface: pygame.Surface, pos: tuple) -> None:
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
                    pygame.draw.circle(impact_surface, (*color, alpha), 
                                     (radius, radius), radius, max(1, 3 - i))
                    surface.blit(impact_surface, (pos[0] - radius, pos[1] - radius))
    
    def _draw_muzzle_flash(self, surface: pygame.Surface):
        """Draw muzzle flash effect at bottom of screen"""
        flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 3), pygame.SRCALPHA)
        
        # Create radial gradient for muzzle flash
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 3
        
        for radius in range(0, SCREEN_HEIGHT // 3, 5):
            alpha = int(255 * (1 - radius / (SCREEN_HEIGHT // 3)) * (self.muzzle_flash_time / 0.1))
            if alpha > 0:
                pygame.draw.circle(flash_surface, (255, 200, 100, alpha), 
                                 (center_x, center_y), radius)
        
        surface.blit(flash_surface, (0, SCREEN_HEIGHT - SCREEN_HEIGHT // 3))
    
    def _draw_ui(self, surface: pygame.Surface) -> None:
        """Draw game UI elements"""
        # Health bar
        health_bar_width = 300
        health_bar_height = 30
        health_bar_x = 10
        health_bar_y = SCREEN_HEIGHT - 40
        
        # Health bar background
        pygame.draw.rect(surface, (50, 0, 0),
                        (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        # Health bar fill
        health_percent = self.player_health / self.max_health
        health_color = (255, 0, 0) if health_percent < 0.3 else (255, 255, 0) if health_percent < 0.6 else (0, 255, 0)
        pygame.draw.rect(surface, health_color,
                        (health_bar_x, health_bar_y, 
                         int(health_bar_width * health_percent), health_bar_height))
        
        # Health bar border
        pygame.draw.rect(surface, WHITE,
                        (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        
        # Health text
        health_text = self.small_font.render(f"{self.player_health}/{self.max_health}", True, WHITE)
        health_text_rect = health_text.get_rect(center=(health_bar_x + health_bar_width // 2, 
                                                        health_bar_y + health_bar_height // 2))
        surface.blit(health_text, health_text_rect)
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (10, 10))
        
        # Wave info with stage indicator
        stage_names = {
            1: "The Beginning",
            2: "Hell's Gates", 
            3: "Demon Realm",
            4: "Final Apocalypse"
        }
        stage_name = stage_names.get(self.current_stage_theme, "Unknown")
        wave_text = self.font.render(f"Wave {self.enemy_manager.wave_number}: {stage_name}", True, WHITE)
        surface.blit(wave_text, (10, 50))
        
        # Enemy count
        enemy_count = len([e for e in self.enemy_manager.enemies if e.alive])
        enemies_text = self.small_font.render(f"Enemies: {enemy_count}", True, WHITE)
        surface.blit(enemies_text, (10, 90))
        
        # Combo indicator
        if self.enemy_manager.current_combo > 1:
            combo_color = (255, 255, 0) if self.enemy_manager.current_combo < 5 else (255, 128, 0)
            combo_text = self.font.render(f"COMBO x{self.enemy_manager.current_combo}", True, combo_color)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            surface.blit(combo_text, combo_rect)
        
        # Wave complete message
        if self.enemy_manager.wave_complete:
            wave_complete_text = self.big_font.render(f"WAVE {self.enemy_manager.wave_number} COMPLETE!", 
                                                     True, (0, 255, 0))
            wave_rect = wave_complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(wave_complete_text, wave_rect)
            
            # Check if entering new stage
            next_wave = self.enemy_manager.wave_number + 1
            next_theme = min(4, (next_wave - 1) // 2 + 1)
            if next_theme != self.current_stage_theme:
                stage_names = {
                    2: "ENTERING HELL'S GATES",
                    3: "DESCENDING TO DEMON REALM",
                    4: "THE FINAL APOCALYPSE BEGINS"
                }
                if next_theme in stage_names:
                    stage_text = self.big_font.render(stage_names[next_theme], True, (255, 100, 0))
                    stage_rect = stage_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
                    surface.blit(stage_text, stage_rect)
            else:
                next_wave_text = self.font.render(f"Next wave starting...", True, WHITE)
                next_rect = next_wave_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                surface.blit(next_wave_text, next_rect)
        
        # FPS counter 
        fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, GRAY)
        fps_rect = fps_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        surface.blit(fps_text, fps_rect)
        
        # Controls hint
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Reset | D: Debug", True, GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        surface.blit(controls_text, controls_rect)
        
        # Debug info
        if self.debug_mode:
            debug_text = self.small_font.render("DEBUG MODE - Hitboxes Visible", True, (255, 0, 255))
            surface.blit(debug_text, (10, 120))
        
        # Danger indicator if enemies are close
        closest_distance = self.enemy_manager.get_closest_enemy_distance()
        if closest_distance < 0.3:
            danger_alpha = int(255 * (1 - closest_distance / 0.3))
            danger_surface = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
            danger_surface.fill((255, 0, 0, danger_alpha // 4))
            surface.blit(danger_surface, (0, 0))
            surface.blit(danger_surface, (0, SCREEN_HEIGHT - 60))
            
            if closest_distance < 0.1:
                danger_text = self.big_font.render("DANGER!", True, (255, 0, 0))
                danger_rect = danger_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
                surface.blit(danger_text, danger_rect)
    
    def _draw_camera_feed(self) -> None:
        """Draw camera feed in corner"""
        if hasattr(self, '_processed_camera_frame') and self._processed_camera_frame is not None:
            camera_surface = self.camera_manager.frame_to_pygame_surface(
                self._processed_camera_frame, (CAMERA_WIDTH, CAMERA_HEIGHT)
            )
        else:
            ret, frame = self.camera_manager.read_frame()
            if ret and frame is not None:
                camera_surface = self.camera_manager.frame_to_pygame_surface(
                    frame, (CAMERA_WIDTH, CAMERA_HEIGHT)
                )
            else:
                camera_surface = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT))
                camera_surface.fill(DARK_GRAY)
                no_cam_text = self.small_font.render("No Camera", True, WHITE)
                text_rect = no_cam_text.get_rect(center=(CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2))
                camera_surface.blit(no_cam_text, text_rect)
        
        # Draw border
        border_color = self.crosshair_color if self.crosshair_pos else WHITE
        border_rect = pygame.Rect(CAMERA_X - 2, CAMERA_Y - 2, CAMERA_WIDTH + 4, CAMERA_HEIGHT + 4)
        pygame.draw.rect(self.screen, border_color, border_rect, 2)
        
        # Draw camera feed
        self.screen.blit(camera_surface, (CAMERA_X, CAMERA_Y))
    
    def _execute_console_command(self):
        """Execute debug console command"""
        command = self.console_input.strip().lower()
        
        if command.startswith("/stage "):
            try:
                stage_num = int(command.split()[1])
                # Calculate wave number from stage (2 waves per stage)
                wave_num = (stage_num - 1) * 2 + 1
                self._jump_to_wave(wave_num)
                self.console_message = f"Jumped to Stage {stage_num} (Wave {wave_num})"
            except:
                self.console_message = "Invalid stage number"
        
        elif command.startswith("/wave "):
            try:
                wave_num = int(command.split()[1])
                self._jump_to_wave(wave_num)
                self.console_message = f"Jumped to Wave {wave_num}"
            except:
                self.console_message = "Invalid wave number"
        
        elif command == "/heal":
            self.player_health = self.max_health
            self.console_message = "Health restored to full"
        
        elif command == "/kill":
            # Kill all enemies on screen
            for enemy in self.enemy_manager.enemies:
                enemy.alive = False
                enemy.death_time = time.time()
            self.console_message = "All enemies killed"
        
        elif command == "/god":
            # TODO god mode
            self.console_message = "God mode not yet implemented"
        
        else:
            self.console_message = "Unknown command. Try: /stage #, /wave #, /heal, /kill"
        
        self.console_message_time = time.time()
    
    def _jump_to_wave(self, wave_num: int):
        """Jump directly to a specific wave"""
        # Clear current enemies
        self.enemy_manager.enemies.clear()
        
        # Set wave number
        self.enemy_manager.wave_number = wave_num
        self.enemy_manager.wave_complete = False
        self.enemy_manager.enemies_spawned_this_wave = 0
        self.enemy_manager.enemies_per_wave = 5 + wave_num * 2
        self.enemy_manager.time_between_spawns = max(1.5, 3.0 - wave_num * 0.15)
        self.enemy_manager.difficulty_multiplier = 1.0 + (wave_num - 1) * 0.10
        
        # Update stage theme
        new_theme = min(4, (wave_num - 1) // 2 + 1)
        if new_theme != self.current_stage_theme:
            self.current_stage_theme = new_theme
            self.create_background()
            # Start the appropriate music and sound effects for the new stage
            self._start_stage_music(new_theme)
    
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
            hint_text = self.small_font.render("Commands: /stage #, /wave #, /heal, /kill | ESC to cancel", True, (200, 200, 200))
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, console_rect.bottom + 20))
            self.screen.blit(hint_text, hint_rect)
        else:
            instructions = [
                "Press P or SPACE to resume",
                "Press / to open debug console",
                "Press ESC to return to menu",
                "Press R to reset game"
            ]
            
            for i, instruction in enumerate(instructions):
                text = self.font.render(instruction, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
                self.screen.blit(text, text_rect)
        
        # Show console message if recent
        if self.console_message and time.time() - self.console_message_time < 3:
            msg_text = self.font.render(self.console_message, True, (0, 255, 0))
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
            self.screen.blit(msg_text, msg_rect)
    
    def _draw_game_over_screen(self, surface: pygame.Surface):
        """Draw game over screen"""
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.huge_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        surface.blit(game_over_text, game_over_rect)
        
        # Stats
        stats = [
            f"Final Score: {self.score}",
            f"Waves Survived: {self.enemy_manager.wave_number - 1}",
            f"Enemies Defeated: {self.enemy_manager.total_kills}",
            f"Best Combo: {self.enemy_manager.current_combo}"
        ]
        
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            surface.blit(text, text_rect)
        
        # Restart instructions
        restart_text = self.font.render("Press ENTER or R to restart | ESC to return to menu", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
        surface.blit(restart_text, restart_rect)
    
    def _start_stage_music(self, stage: int):
        """Start the appropriate music for a given stage"""
        if stage >= 4:
            # Stage 4+ uses alternating tracks
            self.stage4_alternating_mode = True
            # For stage 4+, play tracks without loops so we can detect when they finish
            self.current_music_track = self.sound_manager.get_stage_music(stage)
            self.sound_manager.play_ambient(self.current_music_track, loops=0)  # Play once
        else:
            # Stages 1-3 use single tracks on loop
            self.stage4_alternating_mode = False
            self.current_music_track = self.sound_manager.play_stage_music(stage, loops=-1)
        
        # Start stage-specific ambient effects
        if stage == 2:
            # Play fire ambient loop for Stage 2
            self.current_stage_ambient = 'stage2_fire_ambient'
            self.sound_manager.play_stage_effect('stage2_fire_ambient', loops=-1, volume=0.25)
            print(f"Starting Stage 2 fire ambient")
        elif stage == 3:
            # Play static/mist ambient for Stage 3
            self.current_stage_ambient = 'stage3_static_mist'
            self.sound_manager.play_stage_effect('stage3_static_mist', loops=-1, volume=0.2)
            print(f"Starting Stage 3 static ambient")
        elif stage >= 4:
            # No continuous ambient for Stage 4, just one-shot lightning
            self.current_stage_ambient = None
            self.sound_manager.stop_stage_effect()
        else:
            # Stop any stage effects for Stage 1
            self.current_stage_ambient = None
            self.sound_manager.stop_stage_effect()
    
    def _handle_stage4_music_alternation(self):
        """Handle the alternating music logic for Stage 4+"""
        # Check if current track has finished
        if self.sound_manager.is_ambient_finished():
            # Switch to the next track in the alternation
            self.current_music_track = self.sound_manager.get_next_stage4_track(self.current_music_track)
            self.sound_manager.play_ambient(self.current_music_track, loops=0)  # Play once