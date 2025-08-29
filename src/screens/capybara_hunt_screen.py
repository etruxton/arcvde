"""
Capybara Hunt - Duck Hunt inspired game mode with capybaras on balloons.
"""

# Standard library imports
import math
import os
import random
import time
from typing import List, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from game.capybara_hunt.capybara import CapybaraManager, FlyingCapybara
from game.capybara_hunt.pond_buddy import PondBuddy
from game.capybara_hunt.renderer import CapybaraHuntRenderer
from game.capybara_hunt.ui_manager import CapybaraHuntUI
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


class CapybaraHuntScreen(BaseScreen):
    """Capybara Hunt gameplay screen - Duck Hunt inspired"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        self.huge_font = pygame.font.Font(None, 120)

        # Game state
        self.score = 0
        self.shots_remaining = 5
        self.game_over = False
        self.round_complete_time = 0
        self.paused = False

        # UI Manager
        self.ui_manager = CapybaraHuntUI(self.font)

        # Renderer for all drawing operations
        self.renderer = CapybaraHuntRenderer()

        # Pond companion
        self.pond_buddy = PondBuddy(100, SCREEN_HEIGHT - 70)

        self.capybara_manager = CapybaraManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200
        self.capybara_shot_message_time = 0

        # Hit tracking for round
        self.hit_markers = []

        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0

        # Debug console
        self.console_active = False
        self.console_input = ""
        self.console_message = ""
        self.console_message_time = 0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle mouse clicks for buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()

                # Handle UI button clicks
                action = self.ui_manager.handle_mouse_button_click(
                    mouse_pos, self.capybara_manager.round_complete, self.game_over
                )

                if action == "continue":
                    self.start_next_round()
                    return None
                elif action == "retry":
                    self.reset_game()
                    return None
                elif action == "menu":
                    return GAME_STATE_MENU

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
                if not self.game_over and not self.capybara_manager.round_complete:
                    self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_RETURN and (
                self.game_over or self.capybara_manager.round_complete or self.capybara_manager.game_over
            ):
                if self.game_over or self.capybara_manager.game_over:
                    # Process game over reaction if not already done
                    if self.capybara_manager.game_over and not hasattr(self, "_game_over_processed"):
                        self._game_over_processed = True
                        self.game_over = True
                        self.pond_buddy.set_mood("disappointed", 5.0, 2)
                    self.reset_game()
                elif self.capybara_manager.round_complete:
                    self.start_next_round()
            elif event.key == pygame.K_SLASH and self.paused:  # Open console with /
                self.console_active = True
                self.console_input = "/"

        return None

    def reset_game(self) -> None:
        """Reset the entire game"""
        self.score = 0
        self.shots_remaining = 5  # Reset to 5 shots
        self.game_over = False
        self.round_complete_time = 0
        self.capybara_manager.reset_game()
        self.hit_markers.clear()
        self.hand_tracker.reset_tracking_state()
        self.shoot_pos = None
        self.crosshair_pos = None
        self.ui_manager.reset_buttons()

    def start_next_round(self) -> None:
        """Start the next round"""
        self.capybara_manager.start_next_round()
        self.shots_remaining = 5
        if hasattr(self, "_round_completion_processed"):
            delattr(self, "_round_completion_processed")
        if hasattr(self, "_game_over_processed"):
            delattr(self, "_game_over_processed")
        self.hit_markers.clear()
        # Reset UI buttons for next round
        self.ui_manager.reset_buttons()

        # Pond buddy gets excited for new round
        if self.capybara_manager.round_number > 1:
            if self.capybara_manager.round_number % 5 == 0:
                # Milestone round!
                self.pond_buddy.set_mood("celebration", 2.0, 3)
            else:
                self.pond_buddy.set_mood("excited", 1.5, 2)

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        # Process hand tracking always (for button shooting)
        self._process_hand_tracking()

        self.pond_buddy.update(dt)
        self.renderer.update_scenery(dt)

        # Update capybara manager
        capybaras_removed, new_wave_spawned, escaped_count = self.capybara_manager.update(dt, current_time)

        # Check if manager signaled game over
        if self.capybara_manager.game_over and not hasattr(self, "_game_over_processed"):
            self._game_over_processed = True
            self.game_over = True
            self.pond_buddy.set_mood("disappointed", 5.0, 2)

        # Refresh shots when new wave spawns
        if new_wave_spawned and not self.capybara_manager.round_complete and not self.game_over:
            self.shots_remaining = 5

        # Handle escaped capybaras - add to hit_markers as misses (red squares)
        if escaped_count > 0 and not self.capybara_manager.round_complete and not self.game_over:
            for _ in range(escaped_count):
                self.hit_markers.append(False)
                self.pond_buddy.on_capybara_escape()  # Pond buddy shows worried reaction

        # Handle button shooting in round complete or game over states
        if self.shoot_detected and (self.capybara_manager.round_complete or self.game_over):
            action = self.ui_manager.handle_shooting_buttons(
                self.crosshair_pos, self.sound_manager, self.capybara_manager.round_complete, self.game_over
            )

            if action == "continue":
                self.shoot_detected = False
                self.start_next_round()
                return None
            elif action == "retry":
                self.shoot_detected = False
                self.reset_game()
                return None
            elif action == "menu":
                self.shoot_detected = False
                return GAME_STATE_MENU

        if self.capybara_manager.round_complete or self.game_over:
            return None

        if self.paused:
            return None

        # Round completion processing is handled in draw() method

        # Round completion processing is handled in draw() method

        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0

        return None

    def spawn_wave(self):
        """DEPRECATED: Spawning is now handled by CapybaraManager"""
        # This method is no longer used - CapybaraManager handles all spawning
        pass

    def _old_spawn_wave_logic(self):
        """Old spawning logic - kept for reference"""
        self.wave_active = True

        # Determine number of capybaras based on round with increasing chance
        if self.capybara_manager.round_number <= 2:
            num_capybaras = 1
        else:
            # Calculate chance for multiple spawn (increases with rounds)
            # Round 3: 30% chance, Round 4: 40%, Round 5: 50%, etc.
            multi_spawn_chance = min(0.3 + (self.capybara_manager.round_number - 3) * 0.1, 0.8)  # Cap at 80%

            # Check if we should spawn 2 (and if we have at least 2 capybaras left to spawn)
            if (
                random.random() < multi_spawn_chance
                and self.capybara_manager.capybaras_spawned < self.capybara_manager.capybaras_per_round - 1
            ):
                num_capybaras = 2
            else:
                num_capybaras = 1

        self.current_wave_capybaras = min(
            num_capybaras, self.capybara_manager.capybaras_per_round - self.capybara_manager.capybaras_spawned
        )

        grass_line = SCREEN_HEIGHT * 2 // 3

        for i in range(self.current_wave_capybaras):
            start_x = random.randint(int(SCREEN_WIDTH * 0.2), int(SCREEN_WIDTH * 0.8))

            # Start just at or slightly below the grass line so they emerge from grass
            start_y = grass_line + random.randint(0, 30)

            # Bias directions more upward for better visibility
            # More diagonal_left and diagonal_right for varied but predictable paths
            directions = ["diagonal_left", "diagonal_right", "diagonal_left", "diagonal_right", "left", "right"]
            direction = random.choice(directions)

            # If spawning on the left side, bias toward right movement
            # If spawning on the right side, bias toward left movement
            # This keeps them in play longer
            if start_x < SCREEN_WIDTH * 0.4:
                # On left side, prefer right/diagonal_right
                direction = random.choice(["right", "diagonal_right", "diagonal_right"])
            elif start_x > SCREEN_WIDTH * 0.6:
                # On right side, prefer left/diagonal_left
                direction = random.choice(["left", "diagonal_left", "diagonal_left"])

            # Speed increases with round (more gradual)
            speed_multiplier = 1.0 + (self.capybara_manager.round_number - 1) * 0.08

            capybara = FlyingCapybara(start_x, start_y, direction, speed_multiplier)
            self.capybara_manager.capybaras.append(capybara)
            self.capybara_manager.capybaras_spawned += 1

    def _process_hand_tracking(self) -> None:
        """Process hand tracking and shooting detection"""
        # Use base class method for tracking
        self.process_finger_gun_tracking()

        if not self.game_over and not self.capybara_manager.round_complete and not self.paused:
            # Check if we should shoot
            if self.shoot_detected and self.shots_remaining > 0:
                self._handle_shoot(self.crosshair_pos)
                self.shoot_detected = False  # Reset after handling

    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        if self.shots_remaining <= 0 or self.capybara_manager.round_complete:
            return

        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.shots_remaining -= 1

        # Play shoot sound
        self.sound_manager.play("shoot")

        hit, target, points = self.capybara_manager.check_hit(shoot_position[0], shoot_position[1])
        hit_any = hit

        if hit:
            if target == "balloon":
                self.score += points * self.capybara_manager.round_number
                self.hit_markers.append(True)
                self.pond_buddy.on_capybara_hit()  # Pond buddy reacts
                self.sound_manager.play("hit")
            elif target == "capybara":
                self.score -= points * self.capybara_manager.round_number  # Penalty for shooting capybara
                self.hit_markers.append(False)
                self.pond_buddy.on_capybara_miss()  # Pond buddy reacts
                self.sound_manager.play("error")  # Play error sound
                self.shoot_animation_time = pygame.time.get_ticks() - 100  # Make animation last longer
                self.capybara_shot_message_time = pygame.time.get_ticks()  # Show warning message

        # If we didn't hit anything, it's a complete miss
        if not hit_any:
            # 1/4 chance for snarky speech when missing completely
            if random.random() < 1 / 4:
                self.pond_buddy.set_mood("laughing", 2.5, 2)
                # This will automatically use snarky speech since it's the default

        # Check if wave should end (out of ammo)
        if self.shots_remaining == 0:
            flying_in_wave = [c for c in self.capybara_manager.capybaras if c.alive and not hasattr(c, "already_counted")]
            for capybara in flying_in_wave:
                self.hit_markers.append(False)
                capybara.already_counted = True  # Mark so we don't count it again when it escapes
                # Force them to escape
                capybara.flight_time = 10  # Make them fly away immediately

    def draw(self) -> None:
        """Draw the game screen"""
        # Draw background
        self.screen.blit(self.renderer.background, (0, 0))

        # Draw animated scenery (behind capybaras)
        self.renderer.draw_scenery(self.screen)

        # Draw capybaras (sorted by Y position for depth layering)
        self.capybara_manager.draw(self.screen)

        self.pond_buddy.draw(self.screen)

        if self.paused:
            self.renderer.draw_pause_screen(
                self.screen,
                self.console_active,
                self.console_input,
                self.console_message,
                self.console_message_time,
                self.big_font,
                self.font,
                self.small_font,
            )
            return

        if self.game_over or self.capybara_manager.game_over:
            if not self.game_over and self.capybara_manager.game_over:
                if not hasattr(self, "_game_over_processed"):
                    self._game_over_processed = True
                    self.game_over = True
                    self.pond_buddy.set_mood("disappointed", 5.0, 2)

            self.renderer.draw_game_over_screen(
                self.screen,
                self.score,
                self.capybara_manager.round_number,
                self.capybara_manager.capybaras_hit,
                self.capybara_manager.capybaras_per_round,
                self.huge_font,
                self.font,
                self.small_font,
            )
            # Always ensure game over buttons are created fresh
            self.ui_manager.create_game_over_buttons(SCREEN_HEIGHT)
            self.ui_manager.draw_game_over_buttons(self.screen, self.crosshair_pos)

            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.renderer.draw_crosshair(self.screen, self.crosshair_pos, self.crosshair_color)
            self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
            return

        if self.capybara_manager.round_complete:
            # Process round completion reaction if not already done
            if not hasattr(self, "_round_completion_processed"):
                self._round_completion_processed = True
                self.round_complete_time = pygame.time.get_ticks()

                if self.capybara_manager.capybaras_hit == self.capybara_manager.capybaras_per_round:
                    self.score += 1000 * self.capybara_manager.round_number
                    # Pond buddy celebrates perfect round
                    self.pond_buddy.set_mood("celebration", 4.0, 3)
                elif self.capybara_manager.capybaras_hit == self.capybara_manager.required_hits:
                    # Just barely made it
                    self.pond_buddy.set_mood("relieved", 3.0, 3)
                else:
                    # Good job
                    self.pond_buddy.set_mood("proud", 3.0, 3)

            self.renderer.draw_round_complete_screen(
                self.screen,
                self.score,
                self.capybara_manager.round_number,
                self.capybara_manager.capybaras_hit,
                self.capybara_manager.capybaras_per_round,
                self.big_font,
                self.font,
                self.small_font,
            )
            # Always ensure continue button is created fresh
            self.ui_manager.create_continue_button(SCREEN_HEIGHT)
            self.ui_manager.draw_continue_button(self.screen, self.crosshair_pos)

            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.renderer.draw_crosshair(self.screen, self.crosshair_pos, self.crosshair_color)
            self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)
            return

        # Draw crosshair
        if self.crosshair_pos:
            self.renderer.draw_crosshair(self.screen, self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
            self.renderer.draw_shoot_animation(
                self.screen, self.shoot_pos, self.shoot_animation_time, self.shoot_animation_duration
            )

        # Draw UI
        self.renderer.draw_hud(
            self.screen,
            self.score,
            self.shots_remaining,
            self.capybara_manager.round_number,
            self.hit_markers,
            self.capybara_manager.capybaras_per_round,
            self.capybara_manager.required_hits,
            self.current_fps,
            self.font,
            self.small_font,
        )

        # Show punishment message if capybara was shot
        self.renderer.draw_punishment_message(
            self.screen, self.capybara_shot_message_time, self.capybara_manager.round_number, self.big_font, self.font
        )

        # Draw camera feed
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

        # Draw debug overlay if enabled
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

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
            self.capybara_manager.capybaras_hit = self.capybara_manager.capybaras_per_round
            self.hit_markers = [True] * self.capybara_manager.capybaras_per_round
            self.console_message = "Perfect round activated"

        elif command == "/miss":
            # Force a miss for testing game over
            self.capybara_manager.capybaras_hit = 0
            self.hit_markers = [False] * self.capybara_manager.capybaras_per_round
            self.console_message = "Forced miss - prepare for game over"

        elif command == "/skip":
            # Skip to round complete
            if not self.capybara_manager.round_complete and not self.game_over:
                # Force completion in the manager
                self.capybara_manager.capybaras_spawned = self.capybara_manager.capybaras_per_round
                self.capybara_manager.capybaras.clear()
                self.capybara_manager.wave_active = False
                self.console_message = "Skipped to round end"
            else:
                self.console_message = "Cannot skip - round already complete"

        else:
            self.console_message = "Unknown command. Try: /round #, /score #, /perfect, /miss, /skip"

        self.console_message_time = time.time()

    def _jump_to_round(self, round_num: int):
        """Jump directly to a specific round"""
        self.capybara_manager.round_number = round_num
        self.capybara_manager.capybaras_spawned = 0
        self.capybara_manager.capybaras_hit = 0
        self.shots_remaining = 3
        self.game_over = False
        self.capybara_manager.capybaras.clear()
        self.hit_markers.clear()
        self.capybara_manager.spawn_timer = 0
        self.capybara_manager.wave_active = False

        # Reset completion flags
        self.capybara_manager.round_complete = False
        if hasattr(self, "_round_completion_processed"):
            delattr(self, "_round_completion_processed")
        if hasattr(self, "_game_over_processed"):
            delattr(self, "_game_over_processed")

        # Adjust difficulty for the round
        self.capybara_manager.required_hits = min(9, 6 + (round_num - 1) // 5)
        self.capybara_manager.spawn_delay = max(1.0, 2.0 - round_num * 0.1)
