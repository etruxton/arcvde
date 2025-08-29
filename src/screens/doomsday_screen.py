"""
Doomsday mode game screen with doom-style enemy waves
"""

# Standard library imports
import math
import random
import time
from typing import Optional

# Third-party imports
import cv2
import pygame

# Local application imports
from game.doomsday.enemy import EnemyManager
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    BLACK,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    DARK_GRAY,
    GAME_STATE_MENU,
    GRAY,
    GREEN,
    PURPLE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from utils.sound_manager import get_sound_manager


class DoomsdayScreen(BaseScreen):
    """Doomsday mode gameplay screen with enemy waves"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Game-specific components
        self.enemy_manager = EnemyManager(SCREEN_WIDTH, SCREEN_HEIGHT)

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

        self.current_stage_theme = 1
        self.create_background()

        self.current_music_track = None
        self.stage4_alternating_mode = False
        self.music_started = False
        self.current_stage_ambient = None

        # Stage transition effects
        self.stage_transition_active = False
        self.stage_transition_time = 0
        self.stage_transition_duration = 1.2  # 1.2 seconds
        self.stage_transition_type = "fade"  # fade, slide, flash
        self.old_background = None
        self.new_background = None

    def create_background(self):
        """Create a doom-like background with gradient based on current stage"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Define color themes for different stages
        themes = {
            1: {  # Stage 1-2: Classic Doom brown/gray
                "sky_base": (30, 20, 20),
                "sky_end": (50, 35, 35),
                "ground_base": (40, 30, 25),
                "ground_end": (70, 50, 40),
                "horizon": (60, 40, 40),
                "grid": (40, 30, 30),
            },
            2: {  # Stage 3-4: Hellish red
                "sky_base": (40, 10, 10),
                "sky_end": (80, 20, 20),
                "ground_base": (60, 20, 15),
                "ground_end": (100, 40, 30),
                "horizon": (120, 30, 30),
                "grid": (60, 20, 20),
            },
            3: {  # Stage 5-6: Demonic purple/dark
                "sky_base": (20, 10, 30),
                "sky_end": (40, 20, 60),
                "ground_base": (30, 15, 40),
                "ground_end": (60, 30, 80),
                "horizon": (80, 40, 100),
                "grid": (40, 20, 50),
            },
            4: {  # Stage 7+: Apocalyptic orange/black
                "sky_base": (30, 15, 5),
                "sky_end": (60, 30, 10),
                "ground_base": (40, 20, 5),
                "ground_end": (80, 40, 15),
                "horizon": (100, 50, 20),
                "grid": (50, 25, 10),
            },
        }

        theme = themes.get(self.current_stage_theme, themes[1])

        for y in range(SCREEN_HEIGHT):
            # progress = y / SCREEN_HEIGHT

            if y < SCREEN_HEIGHT * 0.4:  # Sky
                sky_progress = y / (SCREEN_HEIGHT * 0.4)
                color = (
                    int(theme["sky_base"][0] + (theme["sky_end"][0] - theme["sky_base"][0]) * sky_progress),
                    int(theme["sky_base"][1] + (theme["sky_end"][1] - theme["sky_base"][1]) * sky_progress),
                    int(theme["sky_base"][2] + (theme["sky_end"][2] - theme["sky_base"][2]) * sky_progress),
                )
            else:  # Ground
                ground_progress = (y - SCREEN_HEIGHT * 0.4) / (SCREEN_HEIGHT * 0.6)
                color = (
                    int(theme["ground_base"][0] + (theme["ground_end"][0] - theme["ground_base"][0]) * ground_progress),
                    int(theme["ground_base"][1] + (theme["ground_end"][1] - theme["ground_base"][1]) * ground_progress),
                    int(theme["ground_base"][2] + (theme["ground_end"][2] - theme["ground_base"][2]) * ground_progress),
                )

            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))

        pygame.draw.line(
            self.background, theme["horizon"], (0, int(SCREEN_HEIGHT * 0.4)), (SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.4)), 2
        )

        self.grid_color = theme["grid"]

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        if event.type == pygame.KEYDOWN:
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
            elif event.key == pygame.K_SLASH and self.paused:
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

        self.current_stage_theme = 1
        self.stage4_alternating_mode = False
        self.music_started = False
        self.current_stage_ambient = None
        self.sound_manager.stop_stage_effect()
        self.create_background()

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        if self.paused or self.game_over:
            return None

        if not self.music_started:
            self.music_started = True
            self._start_stage_music(1)

        self.game_time += dt

        damage, enemies_killed = self.enemy_manager.update(dt, current_time / 1000.0)

        if damage > 0:
            self.take_damage(damage)

        new_theme = min(4, (self.enemy_manager.wave_number - 1) // 2 + 1)
        if new_theme != self.current_stage_theme and not self.stage_transition_active:
            self._start_stage_transition(new_theme)

        if self.current_stage_theme >= 4 and self.stage4_alternating_mode:
            self._handle_stage4_music_alternation()

        if self.damage_flash_time > 0:
            self.damage_flash_time -= dt

        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt

        if self.muzzle_flash_time > 0:
            self.muzzle_flash_time -= dt

        if self.stage_transition_active:
            self.stage_transition_time += dt
            if self.stage_transition_time >= self.stage_transition_duration:
                self._complete_stage_transition()

        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0

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
        self.process_finger_gun_tracking()

        if self.shoot_detected:
            self._handle_shoot(self.crosshair_pos)
            self.shoot_detected = False

    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        current_time = time.time()
        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.muzzle_flash_time = 0.1

        # Play shoot sound
        self.sound_manager.play("shoot")

        # Rapid fire detection
        if current_time - self.last_shoot_time < 0.3:
            self.rapid_fire_count += 1
        else:
            self.rapid_fire_count = 0
        self.last_shoot_time = current_time

        # Rapid fire panic mode
        if self.rapid_fire_count >= 3:
            closest_distance = self.enemy_manager.get_closest_enemy_distance()
            if closest_distance < 0.3:
                # Panic mode - push all close enemies back
                for enemy in self.enemy_manager.enemies:
                    if enemy.alive and enemy.z < 0.4:
                        enemy.z = min(0.6, enemy.z + 0.2)
                self.screen_shake_time = 0.3
                self.screen_shake_intensity = 8
                self.rapid_fire_count = 0

        self.screen_shake_time = 0.05
        self.screen_shake_intensity = 3

        # Check for enemy hits
        score_gained, killed = self.enemy_manager.check_hit(shoot_position[0], shoot_position[1], damage=25)

        if score_gained > 0:
            self.score += score_gained
            if killed:
                self.screen_shake_time = 0.1
                self.screen_shake_intensity = 5
                self.sound_manager.play("enemy_death")
            else:
                self.sound_manager.play("enemy_hit")

    def _start_stage_transition(self, new_theme: int):
        """Start a smooth transition to a new stage"""
        # Store the old background
        self.old_background = self.background.copy()

        # Create the new background
        old_theme = self.current_stage_theme
        self.current_stage_theme = new_theme
        self.create_background()
        self.new_background = self.background.copy()

        self.current_stage_theme = old_theme
        self.background = self.old_background.copy()

        if new_theme == 2:
            self.stage_transition_type = "flash"  # Hell's gates - dramatic flash
        elif new_theme == 3:
            self.stage_transition_type = "fade"
        elif new_theme == 4:
            self.stage_transition_type = "slide"  # Final apocalypse - sliding destruction
        else:
            self.stage_transition_type = "fade"

        self.stage_transition_active = True
        self.stage_transition_time = 0

        self.screen_shake_time = 1.0
        self.screen_shake_intensity = 15

        print(f"Starting stage transition from {old_theme} to {new_theme} with {self.stage_transition_type} effect")

    def _complete_stage_transition(self):
        """Complete the stage transition"""
        # Apply the new theme
        self.current_stage_theme = min(4, (self.enemy_manager.wave_number - 1) // 2 + 1)
        self.background = self.new_background.copy()
        self._start_stage_music(self.current_stage_theme)

        self.stage_transition_active = False
        self.stage_transition_time = 0
        self.old_background = None
        self.new_background = None

        print(f"Stage transition completed to theme {self.current_stage_theme}")

    def _draw_stage_transition(self, surface: pygame.Surface):
        """Draw the stage transition effect"""
        if not self.stage_transition_active or not self.old_background or not self.new_background:
            return

        progress = self.stage_transition_time / self.stage_transition_duration
        progress = min(1.0, progress)

        if self.stage_transition_type == "fade":
            # Create a copy of old background
            transition_surface = self.old_background.copy()

            new_with_alpha = self.new_background.copy()
            alpha = int(255 * progress)
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(alpha)

            # Blend new background
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            temp_surface.blit(self.new_background, (0, 0))
            temp_surface.set_alpha(alpha)

            transition_surface.blit(temp_surface, (0, 0))
            surface.blit(transition_surface, (0, 0))

        elif self.stage_transition_type == "flash":
            if progress < 0.3:
                # Flash phase - bright white
                flash_intensity = int(255 * (progress / 0.3))
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill((255, 255, 255))
                surface.blit(self.old_background, (0, 0))
                flash_surface.set_alpha(flash_intensity)
                surface.blit(flash_surface, (0, 0))
            else:
                # Reveal phase - show new background
                reveal_progress = (progress - 0.3) / 0.7
                if reveal_progress < 1.0:
                    surface.blit(self.new_background, (0, 0))
                    white_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                    white_overlay.fill((255, 255, 255))
                    white_overlay.set_alpha(int(255 * (1 - reveal_progress)))
                    surface.blit(white_overlay, (0, 0))
                else:
                    surface.blit(self.new_background, (0, 0))

        elif self.stage_transition_type == "slide":
            slide_offset = int(SCREEN_WIDTH * (1 - progress))

            surface.blit(self.old_background, (0, 0))

            if slide_offset < SCREEN_WIDTH:
                surface.blit(self.new_background, (slide_offset, 0))

        self._draw_transition_text(surface, progress)

    def _draw_transition_text(self, surface: pygame.Surface, progress: float):
        """Draw dramatic text during stage transitions"""
        stage_names = {2: "ENTERING HELL'S GATES", 3: "DESCENDING TO DEMON REALM", 4: "THE FINAL APOCALYPSE BEGINS"}

        new_theme = min(4, (self.enemy_manager.wave_number - 1) // 2 + 1)
        stage_text = stage_names.get(new_theme, "STAGE CHANGE")

        text_alpha = 255

        if self.stage_transition_type == "flash":
            if progress < 0.2:
                text_alpha = int(255 * (progress / 0.2))
            elif progress < 0.8:
                text_alpha = 255
            else:
                text_alpha = int(255 * (1 - (progress - 0.8) / 0.2))
        elif self.stage_transition_type == "fade":
            if progress < 0.15:
                text_alpha = int(255 * (progress / 0.15))
            elif progress < 0.85:
                text_alpha = 255
            else:
                text_alpha = int(255 * (1 - (progress - 0.85) / 0.15))
        elif self.stage_transition_type == "slide":
            slide_progress = min(1.0, progress * 1.2)  # Slightly faster than background
            text_x_offset = int(SCREEN_WIDTH * (1 - slide_progress))
            if text_x_offset < SCREEN_WIDTH * 0.1:  # When mostly visible
                text_alpha = 255
            else:
                text_alpha = 0

        if text_alpha > 0:
            text_surface = self.big_font.render(stage_text, True, (255, 100, 0))

            glow_surface = self.big_font.render(stage_text, True, (255, 200, 100))

            if self.stage_transition_type == "slide":
                text_x = max(text_x_offset, SCREEN_WIDTH // 2 - text_surface.get_width() // 2)
            else:
                text_x = SCREEN_WIDTH // 2 - text_surface.get_width() // 2

            text_y = SCREEN_HEIGHT // 2 - text_surface.get_height() // 2

            # Apply alpha
            text_surface.set_alpha(text_alpha)
            glow_surface.set_alpha(text_alpha // 2)

            surface.blit(glow_surface, (text_x + 2, text_y + 2))
            surface.blit(glow_surface, (text_x - 2, text_y - 2))

            surface.blit(text_surface, (text_x, text_y))

    def draw(self) -> None:
        """Draw the game screen"""
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake_time > 0:
            shake_offset_x = int((pygame.time.get_ticks() % 100 - 50) / 50 * self.screen_shake_intensity)
            shake_offset_y = int((pygame.time.get_ticks() % 117 - 58) / 58 * self.screen_shake_intensity)

        draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.stage_transition_active:
            self._draw_stage_transition(draw_surface)
        else:
            draw_surface.blit(self.background, (0, 0))

        if self.paused:
            self._draw_pause_screen()
            return

        if self.game_over:
            self._draw_game_over_screen(draw_surface)
            self.screen.blit(draw_surface, (shake_offset_x, shake_offset_y))
            self._draw_camera_feed()
            return

        # Draw stage-specific background elements
        self._draw_stage_background(draw_surface)

        self._draw_floor_grid(draw_surface)

        self._draw_stage_effects(draw_surface)

        # Draw enemies with blood physics
        self.enemy_manager.draw(draw_surface, self.debug_mode, dt=1.0 / 60.0)

        # Draw crosshair
        if self.crosshair_pos:
            self.draw_crosshair_on_surface(draw_surface, self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
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

        # Draw debug overlay if enabled (using base class method)
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

    def _get_stage_object_alpha(self):
        """Calculate alpha for stage objects during transitions"""
        if not self.stage_transition_active:
            return 255

        progress = self.stage_transition_time / self.stage_transition_duration
        if progress < 0.5:
            # First half: fade out old objects
            return int(255 * (1 - progress * 2))
        else:
            return int(255 * ((progress - 0.5) * 2))

    def _draw_stage_background(self, surface: pygame.Surface):
        """Draw stage-specific background elements"""
        horizon_y = int(SCREEN_HEIGHT * 0.4)

        # Calculate object alpha during transitions
        object_alpha = self._get_stage_object_alpha()

        # Create a temporary surface for alpha blending if needed
        if object_alpha < 255:
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            temp_surface.set_alpha(object_alpha)
            draw_target = temp_surface
        else:
            draw_target = surface

        if self.current_stage_theme == 1:
            # Stage 1: The Beginning

            for i in range(18):
                building_x = i * 70
                building_height = 60 + (i % 4) * 10
                building_width = 35 + (i % 3) * 5
                building_y = horizon_y - building_height + 10

                # Far building silhouette
                color = (35, 30, 30)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                max_floors = (building_height - 20) // 20
                max_windows_per_floor = (building_width - 10) // 12
                for floor in range(max_floors):
                    for window in range(max_windows_per_floor):
                        win_x = building_x + 5 + window * 12
                        win_y = building_y + 10 + floor * 20
                        if win_x + 6 <= building_x + building_width - 5:
                            # Use deterministic pattern for dark/lit windows
                            if (i + floor + window) % 3 == 0:
                                if int(pygame.time.get_ticks() / 500) % 2 == 0 or (i + floor) % 4 != 0:
                                    pygame.draw.rect(draw_target, (15, 15, 15), (win_x, win_y, 6, 8))
                                else:
                                    pygame.draw.rect(draw_target, (60, 50, 30), (win_x, win_y, 6, 8))  # Lit window
                            else:
                                pygame.draw.rect(draw_target, (15, 15, 15), (win_x, win_y, 6, 8))

            for i in range(10):
                tower_x = 30 + i * 120
                tower_height = 100 + (i % 3) * 15
                tower_width = 55 + (i % 2) * 10
                tower_y = horizon_y - tower_height

                # Tower silhouette with more detail
                color = (28, 23, 23)
                pygame.draw.rect(draw_target, color, (tower_x, tower_y, tower_width, tower_height))

                # Side shadow for depth
                shadow_width = 8
                pygame.draw.rect(
                    draw_target, (20, 18, 18), (tower_x + tower_width - shadow_width, tower_y, shadow_width, tower_height)
                )

                if i % 2 == 0:
                    points = [
                        (tower_x, tower_y),
                        (tower_x + tower_width // 3, tower_y - 15),
                        (tower_x + tower_width * 2 // 3, tower_y + 10),
                        (tower_x + tower_width, tower_y - 5),
                        (tower_x + tower_width, tower_y + 20),
                        (tower_x, tower_y + 20),
                    ]
                    pygame.draw.polygon(draw_target, color, points)

                # Windows with proper bounds checking
                max_floors = (tower_height - 30) // 25
                max_windows = (tower_width - 20) // 15
                for floor in range(min(4, max_floors)):
                    for window in range(min(3, max_windows)):
                        win_x = tower_x + 8 + window * 15
                        win_y = tower_y + 25 + floor * 25
                        if win_x + 10 <= tower_x + tower_width - 8 and win_y + 12 <= tower_y + tower_height - 10:
                            if (i + floor * 3 + window) % 4 == 0:
                                # Flashing emergency lights
                                if int(pygame.time.get_ticks() / 300 + i) % 3 == 0:
                                    pygame.draw.rect(draw_target, (80, 20, 20), (win_x, win_y, 10, 12))  # Red emergency light
                                else:
                                    pygame.draw.rect(draw_target, (10, 10, 10), (win_x, win_y, 10, 12))
                            else:
                                pygame.draw.rect(draw_target, (10, 10, 10), (win_x, win_y, 10, 12))

            for i in range(7):
                building_x = i * 175
                building_height = 140 + (i % 3) * 25
                building_width = 80 + (i % 2) * 15
                building_y = horizon_y - building_height + 5

                color = (22, 18, 18)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                # Strong side shadow for depth
                shadow_width = 12
                pygame.draw.rect(
                    draw_target,
                    (15, 12, 12),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                if i == 1 or i == 3:
                    hole_y = building_y + building_height // 3
                    hole_size = 25
                    pygame.draw.ellipse(
                        draw_target,
                        (30, 20, 20),
                        (building_x + building_width // 2 - hole_size // 2, hole_y, hole_size, hole_size * 2),
                    )

                # Detailed windows with bounds checking
                max_floors = (building_height - 30) // 26
                max_windows = (building_width - 25) // 18
                for floor in range(min(5, max_floors)):
                    for window in range(min(4, max_windows)):
                        win_x = building_x + 10 + window * 18
                        win_y = building_y + 20 + floor * 26
                        if win_x + 12 <= building_x + building_width - 10 and win_y + 15 <= building_y + building_height - 15:
                            if (i * 7 + floor * 5 + window) % 5 == 0:
                                # Flickering lights
                                flicker = int(pygame.time.get_ticks() / 200 + i + floor) % 4
                                if flicker == 0:
                                    pygame.draw.rect(draw_target, (60, 50, 30), (win_x, win_y, 12, 15))  # Lit
                                else:
                                    pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))
                            elif (i + floor + window) % 3 != 0:
                                pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))
                                if (floor * window) % 7 == 0:
                                    pygame.draw.line(draw_target, (15, 15, 15), (win_x, win_y), (win_x + 12, win_y + 15), 1)
                            else:
                                pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))

            fence_y = horizon_y + 50
            # Fence posts
            for x in range(0, SCREEN_WIDTH, 80):
                pygame.draw.line(draw_target, (40, 35, 35), (x, fence_y - 30), (x, fence_y + 30), 3)
            # Wire
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y - 20), (SCREEN_WIDTH, fence_y - 20), 2)
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y), (SCREEN_WIDTH, fence_y), 2)
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y + 20), (SCREEN_WIDTH, fence_y + 20), 2)

            # Scattered debris and rubble
            for _ in range(8):
                debris_x = random.randint(50, SCREEN_WIDTH - 50)
                debris_y = random.randint(horizon_y + 80, SCREEN_HEIGHT - 100)
                debris_size = random.randint(10, 30)
                pygame.draw.polygon(
                    draw_target,
                    (35, 30, 25),
                    [
                        (debris_x, debris_y),
                        (debris_x - debris_size // 2, debris_y + debris_size // 3),
                        (debris_x + debris_size // 3, debris_y + debris_size // 2),
                        (debris_x + debris_size, debris_y + debris_size // 4),
                    ],
                )

        elif self.current_stage_theme == 2:
            # Stage 2: Hell's Gates

            for i in range(4):
                volcano_x = 150 + i * 250
                volcano_base_width = 120
                volcano_height = 80
                volcano_y = horizon_y + 10

                # Distant volcano
                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 20, volcano_y - volcano_height),
                    (volcano_x + 20, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (70, 35, 30), points)

            for i in range(3):
                volcano_x = 100 + i * 350
                volcano_base_width = 160
                volcano_height = 110
                volcano_y = horizon_y + 5

                # Medium volcano
                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 25, volcano_y - volcano_height),
                    (volcano_x + 25, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (65, 30, 25), points)

                glow_radius = 15
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 100, 0, 60), (glow_radius, glow_radius), glow_radius)
                draw_target.blit(glow_surface, (volcano_x - glow_radius, volcano_y - volcano_height - glow_radius))

            for i in range(2):
                volcano_x = 200 + i * 500
                volcano_base_width = 200
                volcano_height = 150
                volcano_y = horizon_y

                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 30, volcano_y - volcano_height),
                    (volcano_x + 30, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (60, 25, 20), points)

                # Lava glow at top
                for j in range(3):
                    glow_radius = 20 - j * 5
                    glow_alpha = 100 - j * 30
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (255, 100, 0, glow_alpha), (glow_radius, glow_radius), glow_radius)
                    draw_target.blit(glow_surface, (volcano_x - glow_radius, volcano_y - volcano_height - glow_radius))

                # Smoke plume
                for smoke in range(5):
                    smoke_y = volcano_y - volcano_height - 20 - smoke * 15
                    smoke_x = volcano_x + math.sin(smoke * 0.5 + pygame.time.get_ticks() * 0.001) * 10
                    smoke_size = 15 + smoke * 3
                    smoke_alpha = max(20, 80 - smoke * 15)
                    smoke_surface = pygame.Surface((smoke_size * 2, smoke_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surface, (80, 80, 80, smoke_alpha), (smoke_size, smoke_size), smoke_size)
                    draw_target.blit(smoke_surface, (smoke_x - smoke_size, smoke_y - smoke_size))

            # Flowing lava river
            river_start_x = -50
            river_y = horizon_y + 60  # Moved closer

            river_points = []
            for i in range(30):
                x = river_start_x + i * 45
                # Create a winding river path
                y_offset = math.sin(i * 0.3) * 25
                flow_offset = math.sin(pygame.time.get_ticks() * 0.0005 + i * 0.5) * 3
                river_points.append((x, river_y + y_offset + flow_offset))

            # Draw river with multiple passes for depth
            # Dark outer edge
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (100, 20, 0), river_points[i], river_points[i + 1], 25)
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (200, 50, 0), river_points[i], river_points[i + 1], 20)
            # Bright inner flow
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (255, 100, 0), river_points[i], river_points[i + 1], 15)
            # Hot center line
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (255, 200, 50), river_points[i], river_points[i + 1], 5)

            # Add flowing lava streaks
            for i in range(8):
                streak_pos = (pygame.time.get_ticks() * 0.05 + i * 100) % (SCREEN_WIDTH + 100)
                river_index = int((streak_pos - river_start_x) / 45)
                if 0 <= river_index < len(river_points) - 1:
                    t = ((streak_pos - river_start_x) % 45) / 45.0
                    y1 = river_points[river_index][1]
                    y2 = river_points[river_index + 1][1] if river_index + 1 < len(river_points) else y1
                    y_at_pos = y1 + (y2 - y1) * t
                    pygame.draw.ellipse(draw_target, (255, 255, 100), (int(streak_pos), int(y_at_pos) - 2, 20, 4))

            # Static lava pools
            lava_pool_positions = [
                (150, horizon_y + 140, 90, 35),
                (450, horizon_y + 120, 110, 40),
                (700, horizon_y + 150, 80, 30),
                (950, horizon_y + 130, 100, 35),
                (1050, horizon_y + 145, 70, 25),
            ]

            for pool_x, pool_y, pool_width, pool_height in lava_pool_positions:
                # Lava pool with glow
                lava_rect = pygame.Rect(pool_x, pool_y, pool_width, pool_height)
                pygame.draw.ellipse(draw_target, (200, 50, 0), lava_rect)
                pygame.draw.ellipse(draw_target, (255, 100, 0), (pool_x + 2, pool_y + 2, pool_width - 4, pool_height - 4))

                bubble_positions = [
                    (pool_x + pool_width // 3, pool_y + pool_height // 2),
                    (pool_x + pool_width * 2 // 3, pool_y + pool_height // 3),
                ]
                for bx, by in bubble_positions:
                    bubble_size = 3 + math.sin(pygame.time.get_ticks() * 0.003) * 1
                    pygame.draw.circle(draw_target, (255, 200, 0), (int(bx), int(by)), int(bubble_size))

            # Static charred trees
            tree_positions = [
                (120, horizon_y + 40),
                (320, horizon_y + 60),
                (520, horizon_y + 30),
                (720, horizon_y + 70),
                (880, horizon_y + 50),
            ]

            for stake_x, stake_y in tree_positions:
                # Burnt tree trunk
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y), (stake_x, stake_y - 40), 4)
                # Broken branches
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y - 30), (stake_x - 15, stake_y - 35), 2)
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y - 20), (stake_x + 10, stake_y - 28), 2)

        elif self.current_stage_theme == 3:
            # Stage 3: Demon Realm

            for crystal in range(15):
                crystal_x = crystal * 80
                crystal_y = horizon_y - 30 + math.sin(pygame.time.get_ticks() * 0.001 + crystal * 0.7) * 10

                # Smaller crystal
                size_mult = 0.5
                points = [
                    (crystal_x, crystal_y - 30 * size_mult),
                    (crystal_x - 10 * size_mult, crystal_y),
                    (crystal_x - 7 * size_mult, crystal_y + 20 * size_mult),
                    (crystal_x, crystal_y + 25 * size_mult),
                    (crystal_x + 7 * size_mult, crystal_y + 20 * size_mult),
                    (crystal_x + 10 * size_mult, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (60, 30, 90), points)

            # Main floating crystal formations
            for crystal in range(10):
                crystal_x = crystal * 120
                crystal_y = horizon_y - 50 + math.sin(pygame.time.get_ticks() * 0.001 + crystal) * 20

                # Main crystal body
                points = [
                    (crystal_x, crystal_y - 60),
                    (crystal_x - 20, crystal_y),
                    (crystal_x - 15, crystal_y + 40),
                    (crystal_x, crystal_y + 50),
                    (crystal_x + 15, crystal_y + 40),
                    (crystal_x + 20, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (80, 40, 120), points)
                pygame.draw.polygon(draw_target, (120, 60, 180), points, 2)

                # Inner glow
                inner_points = [
                    (crystal_x, crystal_y - 50),
                    (crystal_x - 10, crystal_y),
                    (crystal_x, crystal_y + 40),
                    (crystal_x + 10, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (150, 100, 200), inner_points)

                # Energy particles around crystal
                for particle in range(4):
                    angle = pygame.time.get_ticks() * 0.003 + particle * 1.5
                    particle_x = crystal_x + math.cos(angle) * 30
                    particle_y = crystal_y + math.sin(angle) * 30
                    pygame.draw.circle(draw_target, (200, 150, 255), (int(particle_x), int(particle_y)), 2)

            # Twisted portal/vortex in background
            portal_x = SCREEN_WIDTH // 2
            portal_y = horizon_y - 30
            for ring in range(5):
                ring_size = 60 - ring * 10
                ring_alpha = 40 + ring * 15
                ring_surface = pygame.Surface((ring_size * 4, ring_size * 2), pygame.SRCALPHA)
                color = (100 + ring * 20, 50 + ring * 10, 150 + ring * 15, ring_alpha)
                pygame.draw.ellipse(ring_surface, color, (0, 0, ring_size * 4, ring_size * 2))
                draw_target.blit(ring_surface, (portal_x - ring_size * 2, portal_y - ring_size))

            tentacle_positions = [
                (80, horizon_y + 160),
                (220, horizon_y + 150),
                (360, horizon_y + 165),
                (500, horizon_y + 155),
                (640, horizon_y + 160),
                (780, horizon_y + 150),
                (920, horizon_y + 165),
                (1060, horizon_y + 155),
                (1150, horizon_y + 160),
            ]

            for tentacle_x, tentacle_base_y in tentacle_positions:
                # Draw segmented tentacle
                for segment in range(5):
                    segment_y = tentacle_base_y - segment * 15
                    wave_offset = math.sin(segment * 0.5 + pygame.time.get_ticks() * 0.002) * 10
                    segment_x = tentacle_x + wave_offset
                    segment_width = 15 - segment * 2
                    if segment_width > 0:
                        pygame.draw.circle(draw_target, (60, 30, 80), (int(segment_x), segment_y), segment_width)
                        # Sucker detail
                        if segment % 2 == 0:
                            pygame.draw.circle(draw_target, (40, 20, 60), (int(segment_x), segment_y), segment_width - 2)

            # Many more floating geometric shapes in background
            for shape in range(16):
                shape_x = shape * 75
                shape_y = horizon_y + 20 + math.sin(shape * 0.8) * 15
                rotation = pygame.time.get_ticks() * 0.0008 + shape * 0.5

                # Smaller background triangles
                size = 15
                points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * size
                    py = shape_y + math.sin(angle) * size
                    points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (80, 40, 120), points, 1)

            for shape in range(9):
                shape_x = shape * 135
                shape_y = horizon_y - 10 + math.sin(shape) * 20
                rotation = pygame.time.get_ticks() * 0.001 + shape

                # Rotating triangular prism outline
                size = 25
                points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * size
                    py = shape_y + math.sin(angle) * size
                    points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (100, 50, 150), points, 2)

                # Inner triangle
                inner_points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * (size - 5)
                    py = shape_y + math.sin(angle) * (size - 5)
                    inner_points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (150, 80, 200), inner_points, 1)

        elif self.current_stage_theme == 4:
            # Stage 4: Final Apocalypse

            for building in range(20):
                building_x = building * 60
                building_width = 40 + (building % 3) * 10
                building_height = 50 + (building % 4) * 15
                building_y = horizon_y - building_height + 15

                # Distant buildings
                color = (40, 35, 35)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                if building % 3 == 0:
                    points = [
                        (building_x, building_y),
                        (building_x + building_width // 3, building_y - 10),
                        (building_x + building_width * 2 // 3, building_y + 5),
                        (building_x + building_width, building_y),
                        (building_x + building_width, building_y + 10),
                        (building_x, building_y + 10),
                    ]
                    pygame.draw.polygon(draw_target, color, points)

            for building in range(13):
                building_x = building * 92
                building_width = 60 + (building % 3) * 15
                building_height = 80 + (building % 4) * 20
                building_y = horizon_y - building_height + 10

                color = (32, 27, 27)

                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                # Side shadow for depth
                shadow_width = 6
                pygame.draw.rect(
                    draw_target,
                    (25, 20, 20),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                # Structural damage
                if building % 2 == 1:
                    # Hole blown through
                    hole_y = building_y + building_height // 2
                    hole_size = 20
                    pygame.draw.ellipse(
                        draw_target,
                        (50, 35, 35),
                        (building_x + building_width // 2 - hole_size // 2, hole_y, hole_size, hole_size),
                    )

                # Windows (many broken)
                for floor in range(building_height // 20):
                    for window in range(building_width // 18):
                        win_x = building_x + 8 + window * 18
                        win_y = building_y + 8 + floor * 20
                        if win_y < building_y + building_height - 15:
                            if (building + floor + window) % 3 != 0:
                                pygame.draw.rect(draw_target, (8, 5, 5), (win_x, win_y, 7, 10))

            for building in range(8):
                building_x = building * 150
                building_width = 100 + (building % 2) * 30
                building_height = 120 + (building % 3) * 40
                building_y = horizon_y - building_height + 5

                color = (25, 20, 20)

                # Draw building with heavy damage
                if building % 2 == 0:
                    # Broken/collapsed top
                    points = [
                        (building_x, building_y + 40),
                        (building_x + building_width // 4, building_y + 10),
                        (building_x + building_width // 2, building_y + 25),
                        (building_x + building_width * 3 // 4, building_y),
                        (building_x + building_width, building_y + 30),
                        (building_x + building_width, building_y + building_height),
                        (building_x, building_y + building_height),
                    ]
                    pygame.draw.polygon(draw_target, color, points)
                else:
                    pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                    # Multiple holes
                    for hole_num in range(2):
                        hole_y = building_y + (hole_num + 1) * building_height // 3
                        hole_x = building_x + building_width // 2 + (hole_num - 0.5) * 20
                        hole_size = 25 + hole_num * 5
                        pygame.draw.ellipse(
                            draw_target, (45, 30, 30), (int(hole_x - hole_size // 2), hole_y, hole_size, int(hole_size * 1.5))
                        )

                # Strong shadow for depth
                shadow_width = 10
                pygame.draw.rect(
                    draw_target,
                    (15, 12, 12),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                # Detailed broken windows
                for floor in range(building_height // 22):
                    for window in range(building_width // 16):
                        win_x = building_x + 10 + window * 16
                        win_y = building_y + 10 + floor * 22
                        if win_y < building_y + building_height - 20:
                            if (building * floor + window) % 4 != 0:
                                pygame.draw.rect(draw_target, (5, 3, 3), (win_x, win_y, 10, 13))
                                # Cracks in some windows
                                if (floor + window) % 5 == 0:
                                    pygame.draw.line(draw_target, (10, 8, 8), (win_x, win_y), (win_x + 10, win_y + 13), 1)

                # Fire in some buildings
                if building in [1, 3]:
                    fire_floors = [building_height // 3, building_height * 2 // 3]
                    for fire_y_offset in fire_floors:
                        fire_y = building_y + fire_y_offset
                        for flame in range(3):
                            flame_offset = (flame - 1) * 15
                            flame_x = building_x + building_width // 2 + flame_offset
                            # Flame animation using time
                            flame_height = 20 + math.sin(pygame.time.get_ticks() * 0.003 + flame) * 5
                            flame_width = 15 + math.cos(pygame.time.get_ticks() * 0.004 + flame) * 3
                            pygame.draw.ellipse(
                                draw_target,
                                (255, 150 + flame * 20, 0),
                                (
                                    int(flame_x - flame_width // 2),
                                    int(fire_y - flame_height),
                                    int(flame_width),
                                    int(flame_height),
                                ),
                            )

            # Background ground cracks
            back_crack_positions = [
                [(150, horizon_y + 80), (170, horizon_y + 100), (160, horizon_y + 120), (180, horizon_y + 140)],
                [(400, horizon_y + 70), (420, horizon_y + 95), (410, horizon_y + 115), (430, horizon_y + 135)],
                [(650, horizon_y + 90), (670, horizon_y + 110), (660, horizon_y + 130), (680, horizon_y + 150)],
            ]

            for crack_segments in back_crack_positions:
                if len(crack_segments) > 1:
                    # Thin background cracks
                    pygame.draw.lines(draw_target, (15, 8, 5), False, crack_segments, 2)
                    pygame.draw.lines(draw_target, (180, 40, 10), False, crack_segments, 1)

            # Foreground ground cracks
            main_crack_positions = [
                [
                    (50, SCREEN_HEIGHT),
                    (80, SCREEN_HEIGHT - 60),
                    (70, SCREEN_HEIGHT - 120),
                    (100, SCREEN_HEIGHT - 180),
                    (90, SCREEN_HEIGHT - 220),
                ],
                [
                    (350, SCREEN_HEIGHT),
                    (370, SCREEN_HEIGHT - 70),
                    (360, SCREEN_HEIGHT - 130),
                    (380, SCREEN_HEIGHT - 190),
                    (375, SCREEN_HEIGHT - 230),
                ],
                [
                    (700, SCREEN_HEIGHT),
                    (720, SCREEN_HEIGHT - 50),
                    (710, SCREEN_HEIGHT - 110),
                    (730, SCREEN_HEIGHT - 160),
                    (725, SCREEN_HEIGHT - 200),
                ],
                [(900, SCREEN_HEIGHT), (920, SCREEN_HEIGHT - 80), (910, SCREEN_HEIGHT - 140), (925, SCREEN_HEIGHT - 180)],
            ]

            for crack_segments in main_crack_positions:
                if len(crack_segments) > 1:
                    # Main crack
                    pygame.draw.lines(draw_target, (10, 5, 0), False, crack_segments, 4)
                    # Glow from within
                    pygame.draw.lines(draw_target, (255, 50, 0), False, crack_segments, 2)
                    # Inner bright line
                    pygame.draw.lines(draw_target, (255, 150, 50), False, crack_segments, 1)

    def _draw_stage_effects(self, surface: pygame.Surface):
        """Draw atmospheric effects based on current stage"""
        # Calculate object alpha during transitions
        object_alpha = self._get_stage_object_alpha()

        # Create a temporary surface for alpha blending if needed
        if object_alpha < 255:
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            temp_surface.set_alpha(object_alpha)
            draw_target = temp_surface
        else:
            draw_target = surface
        if self.current_stage_theme == 2:
            # Fire particles
            for i in range(5):
                x = random.randint(0, SCREEN_WIDTH)
                y = SCREEN_HEIGHT - random.randint(0, 100)
                size = random.randint(2, 6)
                color = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0)])
                pygame.draw.circle(draw_target, color, (x, y), size)

                if size >= 5 and random.random() < 0.001:
                    self.sound_manager.play_one_shot_effect("stage2_fire_crackle", volume=0.05)

        elif self.current_stage_theme == 3:
            mist_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(3):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(int(SCREEN_HEIGHT * 0.4), SCREEN_HEIGHT)
                radius = random.randint(50, 150)
                mist_surface.fill((100, 50, 150, 20), (x - radius, y - radius, radius * 2, radius * 2))
            draw_target.blit(mist_surface, (0, 0))

        elif self.current_stage_theme == 4:
            # FINAL APOCALYPSE

            # 1. Falling meteors/debris
            for i in range(8):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, int(SCREEN_HEIGHT * 0.6))
                meteor_size = random.randint(3, 8)
                # Meteor core
                pygame.draw.circle(draw_target, (255, 100, 0), (x, y), meteor_size)
                # Fiery trail
                for j in range(5):
                    trail_x = x - j * 3
                    trail_y = y - j * 5
                    trail_size = meteor_size - j
                    if trail_size > 0:
                        color = (255 - j * 30, 50 + j * 20, 0)
                        pygame.draw.circle(draw_target, color, (trail_x, trail_y), trail_size)

            # 2. Ash particles falling
            for i in range(15):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                pygame.draw.circle(draw_target, (150, 150, 150), (x, y), 1)

            # 3. Intense lightning with screen flash
            if random.random() < 0.04:  # 4% chance
                # Play lightning sound effect
                if random.random() < 0.7:  # 70% chance for lightning sound
                    self.sound_manager.play_one_shot_effect("stage4_lightning", volume=0.4)
                else:  # 30% chance for just thunder
                    self.sound_manager.play_one_shot_effect("stage4_thunder", volume=0.3)

                # Draw actual lightning bolt
                lightning_x = random.randint(100, SCREEN_WIDTH - 100)
                current_x = lightning_x
                current_y = 0
                for i in range(10):
                    next_x = current_x + random.randint(-30, 30)
                    next_y = current_y + SCREEN_HEIGHT // 10
                    pygame.draw.line(draw_target, (255, 255, 255), (current_x, current_y), (next_x, next_y), 3)
                    pygame.draw.line(draw_target, (200, 200, 255), (current_x, current_y), (next_x, next_y), 1)
                    current_x, current_y = next_x, next_y

                # Screen flash
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.set_alpha(60)
                flash_surface.fill((255, 200, 150))
                draw_target.blit(flash_surface, (0, 0))

            # 4. Dark smoke clouds at top
            smoke_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(4):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, int(SCREEN_HEIGHT * 0.3))
                radius = random.randint(40, 100)
                smoke_surface.fill((50, 30, 20, 30), (x - radius, y - radius, radius * 2, radius * 2))
            draw_target.blit(smoke_surface, (0, 0))

        # Blit the temporary surface if using alpha blending
        if object_alpha < 255:
            surface.blit(temp_surface, (0, 0))

    def _draw_floor_grid(self, surface: pygame.Surface):
        """Draw 3D floor grid for perspective"""
        horizon_y = int(SCREEN_HEIGHT * 0.4)

        # Use the theme's grid color
        grid_color = self.grid_color if hasattr(self, "grid_color") else (40, 30, 30)

        # Vertical lines (perspective)
        for i in range(-10, 11):
            x_start = SCREEN_WIDTH // 2 + i * 100
            x_end = SCREEN_WIDTH // 2 + i * 20
            pygame.draw.line(surface, grid_color, (x_start, SCREEN_HEIGHT), (x_end, horizon_y), 1)

        # Horizontal lines (depth)
        for i in range(10):
            y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (i / 10) ** 0.7
            pygame.draw.line(surface, grid_color, (0, int(y)), (SCREEN_WIDTH, int(y)), 1)

    # Note: _draw_crosshair removed - using base class draw_crosshair method
    # If we need special drawing to a surface, we temporarily swap the screen
    def draw_crosshair_on_surface(self, surface: pygame.Surface, pos: tuple, color: tuple) -> None:
        """Draw crosshair on a specific surface"""
        original_screen = self.screen
        self.screen = surface
        self.draw_crosshair(pos, color)
        self.screen = original_screen

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
                    pygame.draw.circle(impact_surface, (*color, alpha), (radius, radius), radius, max(1, 3 - i))
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
                pygame.draw.circle(flash_surface, (255, 200, 100, alpha), (center_x, center_y), radius)

        surface.blit(flash_surface, (0, SCREEN_HEIGHT - SCREEN_HEIGHT // 3))

    def _draw_ui(self, surface: pygame.Surface) -> None:
        """Draw game UI elements"""
        # Health bar
        health_bar_width = 300
        health_bar_height = 30
        health_bar_x = 10
        health_bar_y = SCREEN_HEIGHT - 40

        # Health bar background
        pygame.draw.rect(surface, (50, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))

        # Health bar fill
        health_percent = self.player_health / self.max_health
        health_color = (255, 0, 0) if health_percent < 0.3 else (255, 255, 0) if health_percent < 0.6 else (0, 255, 0)
        pygame.draw.rect(
            surface, health_color, (health_bar_x, health_bar_y, int(health_bar_width * health_percent), health_bar_height)
        )

        # Health bar border
        pygame.draw.rect(surface, WHITE, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)

        # Health text
        health_text = self.small_font.render(f"{self.player_health}/{self.max_health}", True, WHITE)
        health_text_rect = health_text.get_rect(
            center=(health_bar_x + health_bar_width // 2, health_bar_y + health_bar_height // 2)
        )
        surface.blit(health_text, health_text_rect)

        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (10, 10))

        stage_names = {1: "The Beginning", 2: "Hell's Gates", 3: "Demon Realm", 4: "Final Apocalypse"}
        stage_name = stage_names.get(self.current_stage_theme, "Unknown")
        wave_text = self.font.render(f"Wave {self.enemy_manager.wave_number}: {stage_name}", True, WHITE)
        surface.blit(wave_text, (10, 50))

        # Combo indicator
        if self.enemy_manager.current_combo > 1:
            combo_color = (255, 255, 0) if self.enemy_manager.current_combo < 5 else (255, 128, 0)
            combo_text = self.font.render(f"COMBO x{self.enemy_manager.current_combo}", True, combo_color)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            surface.blit(combo_text, combo_rect)

        if self.enemy_manager.wave_complete:
            wave_complete_text = self.big_font.render(f"WAVE {self.enemy_manager.wave_number} COMPLETE!", True, (0, 255, 0))
            wave_rect = wave_complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(wave_complete_text, wave_rect)

            # Check if entering new stage
            next_wave = self.enemy_manager.wave_number + 1
            next_theme = min(4, (next_wave - 1) // 2 + 1)
            if next_theme != self.current_stage_theme:
                stage_names = {2: "ENTERING HELL'S GATES", 3: "DESCENDING TO DEMON REALM", 4: "THE FINAL APOCALYPSE BEGINS"}
                if next_theme in stage_names:
                    stage_text = self.big_font.render(stage_names[next_theme], True, (255, 100, 0))
                    stage_rect = stage_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
                    surface.blit(stage_text, stage_rect)
            else:
                next_wave_text = self.font.render("Next wave starting...", True, WHITE)
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
        # Use base class method
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

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
            except Exception:
                self.console_message = "Invalid stage number"

        elif command.startswith("/wave "):
            try:
                wave_num = int(command.split()[1])
                self._jump_to_wave(wave_num)
                self.console_message = f"Jumped to Wave {wave_num}"
            except Exception:
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

        # Update stage theme with transition effect
        new_theme = min(4, (wave_num - 1) // 2 + 1)
        if new_theme != self.current_stage_theme:
            self._start_stage_transition(new_theme)
        else:
            # If same stage, just update background without transition
            self.create_background()
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
            hint_text = self.small_font.render(
                "Commands: /stage #, /wave #, /heal, /kill | ESC to cancel", True, (200, 200, 200)
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
            f"Best Combo: {self.enemy_manager.current_combo}",
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
            self.stage4_alternating_mode = True
            # For stage 4+, play tracks without loops so we can detect when they finish
            self.current_music_track = self.sound_manager.get_stage_music(stage)
            self.sound_manager.play_ambient(self.current_music_track, loops=0)  # Play once
        else:
            self.stage4_alternating_mode = False
            self.current_music_track = self.sound_manager.play_stage_music(stage, loops=-1)

        # Start stage-specific ambient effects
        if stage == 2:
            self.current_stage_ambient = "stage2_fire_ambient"
            self.sound_manager.play_stage_effect("stage2_fire_ambient", loops=-1, volume=0.08)
            print("Starting Stage 2 fire ambient")
        elif stage == 3:
            # Play static/mist ambient for Stage 3
            self.current_stage_ambient = "stage3_static_mist"
            self.sound_manager.play_stage_effect("stage3_static_mist", loops=-1, volume=0.2)
            print("Starting Stage 3 static ambient")
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
