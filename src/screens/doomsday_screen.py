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
from game.doomsday.renderer import DoomsdayRenderer
from game.doomsday.stage_manager import StageManager
from game.doomsday.ui_manager import DoomsdayUI
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import GAME_STATE_MENU, SCREEN_HEIGHT, SCREEN_WIDTH
from utils.sound_manager import get_sound_manager


class DoomsdayScreen(BaseScreen):
    """Doomsday mode gameplay screen with enemy waves"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Game-specific components
        self.enemy_manager = EnemyManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = DoomsdayRenderer(screen)
        self.ui_manager = DoomsdayUI(screen)

        # Game state
        self.score = 0
        self.player_health = 100
        self.max_health = 100
        self.game_time = 0
        self.paused = False
        self.game_over = False

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

        # Stage management system
        self.stage_manager = StageManager(self.sound_manager, self.trigger_screen_shake)

        # Music tracking
        self.music_started = False

        # Visual effects
        self.screen_shake_time = 0
        self.screen_shake_intensity = 0
        self.damage_flash_time = 0
        self.muzzle_flash_time = 0

        # UI state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200  # Match base screen duration

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle pygame events"""
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

            if event.key == pygame.K_ESCAPE:
                return GAME_STATE_MENU
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                if not self.game_over:
                    self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_SLASH:
                if self.paused:
                    self.console_active = True
                    self.console_input = "/"
            elif event.key == pygame.K_d:
                self.debug_mode = not self.debug_mode
                print(f"Debug mode: {self.debug_mode}")
            elif event.key == pygame.K_RETURN:
                if self.game_over:
                    self.reset_game()

        return None

    def trigger_screen_shake(self, duration: float, intensity: int) -> None:
        """Trigger screen shake effect (called by stage manager)"""
        self.screen_shake_time = duration
        self.screen_shake_intensity = intensity

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        if self.paused or self.game_over:
            return None

        # Process finger gun tracking
        self.process_finger_gun_tracking()

        # Check for shooting
        if self.shoot_detected and self.crosshair_pos:
            self.process_shot(self.crosshair_pos)
            self.shoot_detected = False

        # Update stage progression
        self.stage_manager.update_stage_progression(self.enemy_manager.wave_number)
        self.stage_manager.update(dt)

        # Music will be started by stage manager when needed
        # Don't auto-start music here to avoid conflicts with menu music

        # Update game time
        self.game_time += dt

        # Update enemy manager
        damage, enemies_killed = self.enemy_manager.update(dt, current_time)
        if damage > 0:
            self.player_health -= damage
            self.damage_flash_time = 0.3
            if self.player_health <= 0:
                self.game_over = True

        # Update visual effects
        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt

        if self.damage_flash_time > 0:
            self.damage_flash_time -= dt

        if self.muzzle_flash_time > 0:
            self.muzzle_flash_time -= dt

        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = int(self.fps_counter / self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = 0

        return None

    def draw_shoot_animation(self) -> None:
        """Override base screen shoot animation - doomsday uses renderer instead"""
        # Do nothing - doomsday renderer handles shooting animation
        pass

    def process_shot(self, crosshair_pos: tuple) -> None:
        """Process a shot at the given position"""
        if self.game_over or self.paused:
            return

        # Set doomsday shooting animation variables
        self.shoot_pos = crosshair_pos
        self.shoot_animation_time = pygame.time.get_ticks()
        self.muzzle_flash_time = 0.1

        # Check for enemy hits
        score_gained, enemy_killed = self.enemy_manager.check_hit(crosshair_pos[0], crosshair_pos[1], damage=25)
        if score_gained > 0:
            self.score += score_gained
            if enemy_killed:
                self.sound_manager.play("enemy_death")
            else:
                self.sound_manager.play("hit")
        else:
            self.sound_manager.play("shoot")

    def reset_game(self) -> None:
        """Reset the game to initial state"""
        self.score = 0
        self.player_health = self.max_health
        self.game_time = 0
        self.paused = False
        self.game_over = False

        # Reset enemy manager
        self.enemy_manager.reset()

        # Reset stage system
        self.stage_manager.reset()

        # Reset visual effects
        self.screen_shake_time = 0
        self.damage_flash_time = 0
        self.muzzle_flash_time = 0

        # Start stage 1 music when game begins
        self.stage_manager.stage_audio.start_stage_music(1)
        self.music_started = True

    def draw(self) -> None:
        """Draw the game screen"""
        if self.paused:
            self.renderer.draw_pause_screen(
                self.console_active, self.console_input, self.console_message, self.console_message_time
            )
            return

        if self.game_over:
            draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            # Draw background for game over
            draw_surface.blit(self.stage_manager.get_background(), (0, 0))
            self.renderer.draw_game_over_screen(draw_surface, self.score, self.enemy_manager)
            # Apply screen shake to game over screen too
            shake_offset_x = 0
            shake_offset_y = 0
            if self.screen_shake_time > 0:
                shake_offset_x = int((pygame.time.get_ticks() % 100 - 50) / 50 * self.screen_shake_intensity)
                shake_offset_y = int((pygame.time.get_ticks() % 117 - 58) / 58 * self.screen_shake_intensity)
            self.screen.blit(draw_surface, (shake_offset_x, shake_offset_y))
            self.renderer.draw_camera_feed(self)
            return

        # Main game rendering
        self.renderer.draw_main_game(
            self.stage_manager,
            self.enemy_manager,
            self,
            self.crosshair_pos,
            self.crosshair_color,
            self.shoot_pos,
            self.shoot_animation_time,
            self.shoot_animation_duration,
            self.muzzle_flash_time,
            self.damage_flash_time,
            self.screen_shake_time,
            self.screen_shake_intensity,
            self.player_health,
            self.max_health,
            self.score,
            self.current_fps,
            self.debug_mode,
        )

        # Draw camera feed (not affected by shake)
        self.renderer.draw_camera_feed(self)

        # Draw debug overlay if enabled (using base class method)
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

    def _execute_console_command(self):
        """Execute debug console command"""
        command = self.console_input.strip().lower()
        print(f"Executing console command: '{command}'")  # Debug output

        if command.startswith("/stage "):
            try:
                stage_num = int(command.split()[1])
                print(f"Jumping to stage {stage_num}")  # Debug output
                success, message = self.stage_manager.jump_to_stage(stage_num)
                print(f"Jump result: success={success}, message={message}")  # Debug output
                if success:
                    # Also update wave number in enemy manager
                    wave_num = (stage_num - 1) * 2 + 1
                    self._jump_to_wave(wave_num)
                self.console_message = message
            except Exception as e:
                print(f"Console command error: {e}")  # Debug output
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

        # IMPORTANT: Update difficulty multiplier for proper health scaling
        self.enemy_manager.difficulty_multiplier = 1.0 + (wave_num - 1) * 0.15

        # Update stage theme
        stage = min(4, (wave_num - 1) // 2 + 1)
        if stage != self.stage_manager.current_stage_theme:
            self.stage_manager.current_stage_theme = stage
            self.stage_manager.create_background()
