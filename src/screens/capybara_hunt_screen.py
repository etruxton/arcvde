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
from game.capybara_hunt.input_handler import CapybaraHuntInputHandler
from game.capybara_hunt.pond_buddy import PondBuddy
from game.capybara_hunt.renderer import CapybaraHuntRenderer
from game.capybara_hunt.state_manager import CapybaraHuntState
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

        # Game state manager
        self.state = CapybaraHuntState()

        # UI Manager
        self.ui_manager = CapybaraHuntUI(self.font)

        # Input handler for all keyboard and event processing
        self.input_handler = CapybaraHuntInputHandler()

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

        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0

        # Debug mode for hitbox visualization
        self.debug_mode = False

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        result = self.input_handler.handle_events(
            event,
            self.state,
            self.capybara_manager,
            self.ui_manager,
            self.hand_tracker,
            self._reset_shoot_pos,
            self._reset_crosshair_pos,
        )

        # Handle debug mode toggle
        if result == "toggle_debug":
            self.debug_mode = not self.debug_mode
            return None

        return result

    def _reset_shoot_pos(self):
        """Callback to reset shoot position"""
        self.shoot_pos = None

    def _reset_crosshair_pos(self):
        """Callback to reset crosshair position"""
        self.crosshair_pos = None

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        # Process hand tracking always (for button shooting)
        self._process_hand_tracking()

        # Skip game updates when paused
        if self.state.is_paused():
            return None

        self.pond_buddy.update(dt)
        self.renderer.update_scenery(dt)

        # Update capybara manager
        capybaras_removed, new_wave_spawned, escaped_count = self.capybara_manager.update(dt, current_time)

        # Let state manager handle game over transition
        self.state.handle_game_over_transition(self.capybara_manager, self.pond_buddy)

        # Refresh shots when new wave spawns
        if (
            new_wave_spawned
            and not self.capybara_manager.round_complete
            and not self.state.is_game_over(self.capybara_manager)
        ):
            self.state.shots_remaining = 5

        # Handle escaped capybaras - add to hit_markers as misses (red squares)
        if (
            escaped_count > 0
            and not self.capybara_manager.round_complete
            and not self.state.is_game_over(self.capybara_manager)
        ):
            for _ in range(escaped_count):
                self.state.add_hit_marker(False)
                self.pond_buddy.on_capybara_escape()  # Pond buddy shows worried reaction

        # Handle button shooting in round complete or game over states
        if self.shoot_detected and self.state.can_shoot_buttons(self.capybara_manager):
            action = self.ui_manager.handle_shooting_buttons(
                self.crosshair_pos,
                self.sound_manager,
                self.capybara_manager.round_complete,
                self.state.is_game_over(self.capybara_manager),
            )

            if action == "continue":
                self.shoot_detected = False
                self.state.start_next_round()
                self.capybara_manager.start_next_round()
                self.hand_tracker.reset_tracking_state()
                self.shoot_pos = None
                self.crosshair_pos = None
                self.ui_manager.reset_buttons()
                return None
            elif action == "retry":
                self.shoot_detected = False
                self.state.reset_game()
                self.capybara_manager.reset_game()
                self.hand_tracker.reset_tracking_state()
                self.shoot_pos = None
                self.crosshair_pos = None
                self.ui_manager.reset_buttons()
                return None
            elif action == "menu":
                self.shoot_detected = False
                return GAME_STATE_MENU

        if self.capybara_manager.round_complete or self.state.is_game_over(self.capybara_manager):
            return None

        if self.state.is_paused():
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

        if (
            not self.state.is_game_over(self.capybara_manager)
            and not self.capybara_manager.round_complete
            and not self.state.is_paused()
        ):
            # Check if we should shoot
            if self.shoot_detected and self.state.shots_remaining > 0:
                self._handle_shoot(self.crosshair_pos)
                self.shoot_detected = False  # Reset after handling

    def _handle_shoot(self, shoot_position: tuple) -> None:
        """Handle shooting action"""
        if self.state.shots_remaining <= 0 or self.capybara_manager.round_complete:
            return

        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.state.consume_shot()

        # Play shoot sound
        self.sound_manager.play("shoot")

        hit, target, points = self.capybara_manager.check_hit(shoot_position[0], shoot_position[1])
        hit_any = hit

        if hit:
            if target == "balloon":
                self.state.score += points * self.capybara_manager.round_number
                self.state.add_hit_marker(True)
                self.pond_buddy.on_capybara_hit()  # Pond buddy reacts
                self.sound_manager.play("hit")
            elif target == "capybara":
                # Use state manager to handle penalty
                self.state.handle_capybara_shot_penalty(self.capybara_manager)
                self.state.add_hit_marker(False)
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
        if self.state.shots_remaining == 0:
            flying_in_wave = [c for c in self.capybara_manager.capybaras if c.alive and not hasattr(c, "already_counted")]
            for capybara in flying_in_wave:
                self.state.add_hit_marker(False)
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
        self.capybara_manager.draw(self.screen, self.debug_mode)

        self.pond_buddy.draw(self.screen)

        if self.state.should_show_pause_screen():
            console_active, console_input, console_message, console_message_time = self.input_handler.get_console_state()
            self.renderer.draw_pause_screen(
                self.screen,
                console_active,
                console_input,
                console_message,
                console_message_time,
                self.big_font,
                self.font,
                self.small_font,
            )
            return

        if self.state.should_show_game_over_screen(self.capybara_manager):
            # Let state manager handle any needed processing
            self.state.handle_game_over_transition(self.capybara_manager, self.pond_buddy)

            self.renderer.draw_game_over_screen(
                self.screen,
                self.state.score,
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

        if self.state.should_show_round_complete_screen(self.capybara_manager):
            # Let state manager handle round completion processing
            self.state.handle_round_completion(self.capybara_manager, self.pond_buddy)

            self.renderer.draw_round_complete_screen(
                self.screen,
                self.state.score,
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
            self.state.score,
            self.state.shots_remaining,
            self.capybara_manager.round_number,
            self.state.hit_markers,
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

        # Show debug mode indicator
        if self.debug_mode:
            debug_text = self.small_font.render("DEBUG MODE - Hitboxes Visible", True, (255, 0, 255))
            self.screen.blit(debug_text, (10, 120))

        # Draw camera feed
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

        # Draw debug overlay if enabled
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()
