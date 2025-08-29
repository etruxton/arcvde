# Standard library imports
from typing import Dict, List, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from game.capybara_hunt.pond_buddy import PondBuddy


class CapybaraHuntState:
    """Manages game state, transitions, and flow control for Capybara Hunt game mode"""

    def __init__(self):
        # Core game state
        self.score = 0
        self.shots_remaining = 5
        self.game_over = False
        self.paused = False
        self.round_complete_time = 0

        # Round tracking
        self.hit_markers: List[bool] = []

        # Processing flags to prevent duplicate state transitions
        self._game_over_processed = False
        self._round_completion_processed = False

    def reset_game(self) -> None:
        """Reset the entire game to initial state"""
        self.score = 0
        self.shots_remaining = 5
        self.game_over = False
        self.round_complete_time = 0
        self.paused = False
        self.hit_markers.clear()

        # Clear processing flags
        self._game_over_processed = False
        self._round_completion_processed = False

    def start_next_round(self) -> None:
        """Transition to next round state"""
        self.shots_remaining = 5
        self.hit_markers.clear()

        # Clear processing flags for new round
        self._round_completion_processed = False
        self._game_over_processed = False

    def can_shoot(self, capybara_manager) -> bool:
        """Check if player is allowed to shoot based on current game state"""
        return not self.game_over and not capybara_manager.round_complete and not self.paused and self.shots_remaining > 0

    def can_shoot_buttons(self, capybara_manager) -> bool:
        """Check if player can shoot at UI buttons"""
        return (self.game_over or capybara_manager.round_complete) and not self.paused

    def is_paused(self) -> bool:
        """Check if game is currently paused"""
        return self.paused

    def is_game_over(self, capybara_manager) -> bool:
        """Check if game is in game over state"""
        return self.game_over or capybara_manager.game_over

    def is_round_complete(self, capybara_manager) -> bool:
        """Check if current round is complete"""
        return capybara_manager.round_complete

    def toggle_pause(self) -> None:
        """Toggle pause state"""
        self.paused = not self.paused

    def consume_shot(self) -> bool:
        """Consume a shot if available, returns True if shot was consumed"""
        if self.shots_remaining > 0:
            self.shots_remaining -= 1
            return True
        return False

    def add_hit_marker(self, hit: bool) -> None:
        """Add a hit marker to track round progress"""
        self.hit_markers.append(hit)

    def handle_game_over_transition(self, capybara_manager, pond_buddy: PondBuddy) -> None:
        """Handle the transition to game over state"""
        if not self.game_over and capybara_manager.game_over:
            if not self._game_over_processed:
                self._game_over_processed = True
                self.game_over = True
                pond_buddy.set_mood("disappointed", 5.0, 2)

    def handle_round_completion(self, capybara_manager, pond_buddy: PondBuddy) -> None:
        """Handle round completion processing and reactions"""
        if not self._round_completion_processed:
            self._round_completion_processed = True
            self.round_complete_time = pygame.time.get_ticks()

            # Award score and set pond buddy reaction based on performance
            if capybara_manager.capybaras_hit == capybara_manager.capybaras_per_round:
                # Perfect round bonus
                self.score += 1000 * capybara_manager.round_number
                pond_buddy.set_mood("celebration", 4.0, 3)
            elif capybara_manager.capybaras_hit == capybara_manager.required_hits:
                # Just barely made it
                pond_buddy.set_mood("relieved", 3.0, 3)
            else:
                # Good job
                pond_buddy.set_mood("proud", 3.0, 3)

    def should_show_pause_screen(self) -> bool:
        """Check if pause screen should be displayed"""
        return self.paused

    def should_show_game_over_screen(self, capybara_manager) -> bool:
        """Check if game over screen should be displayed"""
        return self.is_game_over(capybara_manager)

    def should_show_round_complete_screen(self, capybara_manager) -> bool:
        """Check if round complete screen should be displayed"""
        return capybara_manager.round_complete

    def should_process_shooting(self, capybara_manager) -> bool:
        """Check if normal shooting mechanics should be processed"""
        return not self.paused and not self.is_game_over(capybara_manager) and not capybara_manager.round_complete

    def get_game_status(self, capybara_manager) -> Dict:
        """Get comprehensive game status dictionary"""
        return {
            "score": self.score,
            "shots_remaining": self.shots_remaining,
            "game_over": self.is_game_over(capybara_manager),
            "paused": self.paused,
            "round_complete": capybara_manager.round_complete,
            "round_number": capybara_manager.round_number,
            "hit_markers": self.hit_markers.copy(),
            "capybaras_hit": capybara_manager.capybaras_hit,
            "capybaras_per_round": capybara_manager.capybaras_per_round,
            "required_hits": capybara_manager.required_hits,
            "can_shoot": self.can_shoot(capybara_manager),
            "can_shoot_buttons": self.can_shoot_buttons(capybara_manager),
        }

    def handle_capybara_shot_penalty(self, capybara_manager) -> int:
        """Handle penalty when capybara is shot instead of balloon"""
        penalty = 200 * capybara_manager.round_number
        self.score = max(0, self.score - penalty)  # Don't let score go negative
        return penalty

    def update_state(self, dt: float, capybara_manager, pond_buddy: PondBuddy) -> None:
        """Update state manager each frame"""
        # Handle game over transition
        if capybara_manager.game_over:
            self.handle_game_over_transition(capybara_manager, pond_buddy)

        # Handle round completion
        if capybara_manager.round_complete:
            self.handle_round_completion(capybara_manager, pond_buddy)
