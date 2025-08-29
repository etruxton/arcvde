# Standard library imports
import time
from typing import Optional

# Third-party imports
import pygame

# Local application imports
from utils.constants import GAME_STATE_MENU


class CapybaraHuntInputHandler:
    """Manages all input handling for Capybara Hunt game mode"""

    def __init__(self):
        # Console state
        self.console_active = False
        self.console_input = ""
        self.console_message = ""
        self.console_message_time = 0

    def handle_events(
        self,
        event: pygame.event.Event,
        state,
        capybara_manager,
        ui_manager,
        hand_tracker,
        shoot_pos_reset_callback,
        crosshair_pos_reset_callback,
    ) -> Optional[str]:
        """Handle keyboard and UI button events"""
        # Handle button shooting first
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state.can_shoot_buttons(capybara_manager):
                action = ui_manager.handle_mouse_button_click(
                    event.pos, capybara_manager.round_complete, state.is_game_over(capybara_manager)
                )

                if action == "continue":
                    state.start_next_round()
                    capybara_manager.start_next_round()
                    hand_tracker.reset_tracking_state()
                    shoot_pos_reset_callback()
                    crosshair_pos_reset_callback()
                    ui_manager.reset_buttons()
                    return None
                elif action == "retry":
                    state.reset_game()
                    capybara_manager.reset_game()
                    hand_tracker.reset_tracking_state()
                    shoot_pos_reset_callback()
                    crosshair_pos_reset_callback()
                    ui_manager.reset_buttons()
                    return None
                elif action == "menu":
                    return GAME_STATE_MENU

        if event.type == pygame.KEYDOWN:
            # Handle console input when active
            if self.console_active:
                if event.key == pygame.K_RETURN:
                    self._execute_console_command(state, capybara_manager)
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
                if not state.is_game_over(capybara_manager) and not capybara_manager.round_complete:
                    state.toggle_pause()
            elif event.key == pygame.K_r:
                state.reset_game()
                capybara_manager.reset_game()
                hand_tracker.reset_tracking_state()
                shoot_pos_reset_callback()
                crosshair_pos_reset_callback()
                ui_manager.reset_buttons()
            elif event.key == pygame.K_RETURN and (
                state.is_game_over(capybara_manager) or capybara_manager.round_complete or capybara_manager.game_over
            ):
                if state.is_game_over(capybara_manager) or capybara_manager.game_over:
                    # Reset entire game
                    state.reset_game()
                    capybara_manager.reset_game()
                    hand_tracker.reset_tracking_state()
                    shoot_pos_reset_callback()
                    crosshair_pos_reset_callback()
                    ui_manager.reset_buttons()
                elif capybara_manager.round_complete:
                    # Start next round
                    state.start_next_round()
                    capybara_manager.start_next_round()
                    hand_tracker.reset_tracking_state()
                    shoot_pos_reset_callback()
                    crosshair_pos_reset_callback()
                    ui_manager.reset_buttons()
            elif event.key == pygame.K_SLASH and state.is_paused():  # Open console with /
                self.console_active = True
                self.console_input = "/"
            elif event.key == pygame.K_d:  # Toggle debug hitboxes
                return "toggle_debug"

        return None

    def _execute_console_command(self, state, capybara_manager):
        """Execute debug console command"""
        command = self.console_input.strip().lower()

        if command.startswith("/round "):
            try:
                round_num = int(command.split()[1])
                if round_num > 0:
                    self._jump_to_round(round_num, state, capybara_manager)
                    self.console_message = f"Jumped to Round {round_num}"
                else:
                    self.console_message = "Round number must be positive"
            except Exception:
                self.console_message = "Invalid round number"

        else:
            self.console_message = "Unknown command. Try: /round #"

        self.console_message_time = time.time()

    def _jump_to_round(self, round_num: int, state, capybara_manager):
        """Jump directly to a specific round"""
        capybara_manager.round_number = round_num
        capybara_manager.capybaras_spawned = 0
        capybara_manager.capybaras_hit = 0
        state.shots_remaining = 3
        state.game_over = False
        capybara_manager.capybaras.clear()
        state.hit_markers.clear()
        capybara_manager.spawn_timer = 0
        capybara_manager.wave_active = False

        # Reset completion flags
        capybara_manager.round_complete = False
        if hasattr(state, "_round_completion_processed"):
            delattr(state, "_round_completion_processed")
        if hasattr(state, "_game_over_processed"):
            delattr(state, "_game_over_processed")

        # Adjust difficulty for the round
        capybara_manager.required_hits = min(9, 6 + (round_num - 1) // 5)
        capybara_manager.spawn_delay = max(1.0, 2.0 - round_num * 0.1)

    def get_console_state(self) -> tuple:
        """Get current console state for rendering"""
        return (self.console_active, self.console_input, self.console_message, self.console_message_time)
