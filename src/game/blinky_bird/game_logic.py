"""
Main game logic for Blinky Bird.
Coordinates all game elements and handles game states.
"""

# Standard library imports
import time
from enum import Enum
from typing import Optional, Tuple

# Third-party imports
import pygame

from .background import Background
from .bird import Bird
from .pipe import PipeManager


class GameState(Enum):
    """Game states for Blinky Bird."""

    WAITING_FOR_CALIBRATION = "waiting_for_calibration"
    CALIBRATING = "calibrating"
    READY = "ready"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class BlinkyBirdGame:
    """
    Main game logic coordinator for Blinky Bird.

    Manages:
    - Game states (calibration, playing, game over)
    - Score tracking
    - Collision detection
    - Game reset
    - Difficulty scaling
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the Blinky Bird game.

        Args:
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Game state
        self.state = GameState.WAITING_FOR_CALIBRATION
        self.score = 0
        self.high_score = 0

        # Initialize game objects
        bird_start_x = screen_width // 4
        bird_start_y = screen_height // 2

        self.bird = Bird(bird_start_x, bird_start_y)
        self.pipe_manager = PipeManager(screen_width, screen_height)
        self.background = Background(screen_width, screen_height)

        # Game timing
        self.game_start_time = 0
        self.game_over_time = 0
        self.ready_time = 0

        # Game settings
        self.ground_collision = True

        # Store initial positions for reset
        self.bird_start_x = bird_start_x
        self.bird_start_y = bird_start_y

    def handle_blink(self, blink_type: str) -> bool:
        """
        Handle blink input from the blink detector.

        Args:
            blink_type: Type of blink ("Blink", "Calibrating", "None")

        Returns:
            True if blink was handled, False otherwise
        """
        if blink_type == "Calibrating":
            self.state = GameState.CALIBRATING
            return True

        if blink_type == "Blink":
            if self.state == GameState.CALIBRATING:
                # Calibration complete, move to ready state
                self.state = GameState.READY
                self.ready_time = time.time()
                return True

            elif self.state == GameState.READY:
                # Start the game
                self.start_game()
                self.bird.flap()
                return True

            elif self.state == GameState.PLAYING:
                # Make bird flap
                self.bird.flap()
                return True

            elif self.state == GameState.GAME_OVER:
                # Restart game
                self.reset_game()
                return True

        return False

    def start_game(self):
        """Start a new game session."""
        self.state = GameState.PLAYING
        self.score = 0
        self.game_start_time = time.time()

    def update(self, dt: float) -> GameState:
        """
        Update game logic.

        Args:
            dt: Delta time in seconds

        Returns:
            Current game state
        """
        # Always update background for visual continuity
        self.background.update(dt)

        if self.state == GameState.PLAYING:
            # Update game objects with physics enabled
            self.bird.update(dt, apply_physics=True)
            self.pipe_manager.update(dt, self.score)

            # Check for scoring
            score_increase = self.pipe_manager.check_scoring(self.bird.x)
            self.score += score_increase

            # Update high score
            if self.score > self.high_score:
                self.high_score = self.score

            # Check collisions
            if self.check_collisions():
                self.game_over()

        elif self.state == GameState.CALIBRATING:
            # During calibration, keep bird completely still
            self.bird.update(dt, apply_physics=False)

        elif self.state in [GameState.READY, GameState.GAME_OVER]:
            # Bird physics still active but no pipes
            self.bird.update(dt, apply_physics=True)

            # Keep bird from falling through ground in ready state
            ground_y = self.background.get_ground_y()
            if self.bird.y + self.bird.radius > ground_y:
                self.bird.y = ground_y - self.bird.radius
                self.bird.velocity_y = 0

        elif self.state == GameState.WAITING_FOR_CALIBRATION:
            # Before calibration starts, keep bird still
            self.bird.update(dt, apply_physics=False)

        return self.state

    def check_collisions(self) -> bool:
        """
        Check for collisions between bird and obstacles.

        Returns:
            True if collision detected
        """
        bird_rect = self.bird.get_rect()

        # Check pipe collisions
        if self.pipe_manager.check_collisions(bird_rect):
            return True

        # Check ground collision
        if self.ground_collision:
            ground_y = self.background.get_ground_y()
            if self.bird.y + self.bird.radius > ground_y:
                return True

        # Check ceiling collision
        if self.bird.y - self.bird.radius < 0:
            return True

        return False

    def game_over(self):
        """Handle game over state."""
        self.state = GameState.GAME_OVER
        self.bird.kill()
        self.game_over_time = time.time()

    def reset_game(self):
        """Reset game to initial state."""
        # Reset game objects
        self.bird.reset(self.bird_start_x, self.bird_start_y)
        self.pipe_manager.reset()
        self.background.reset()

        # Reset game state
        self.state = GameState.READY
        self.ready_time = time.time()
        self.score = 0

    def draw(self, surface: pygame.Surface):
        """
        Draw all game elements.

        Args:
            surface: Pygame surface to draw on
        """
        # Draw background (sky, clouds, ground)
        self.background.draw(surface)

        # Draw pipes (only during gameplay)
        if self.state == GameState.PLAYING:
            self.pipe_manager.draw(surface)

        # Draw bird (except during initial calibration wait)
        if self.state != GameState.WAITING_FOR_CALIBRATION:
            self.bird.draw(surface)

    def get_game_info(self) -> dict:
        """
        Get current game information for UI display.

        Returns:
            Dictionary with game information
        """
        current_time = time.time()

        info = {
            "state": self.state,
            "score": self.score,
            "high_score": self.high_score,
            "bird_alive": self.bird.is_alive,
            "bird_y": self.bird.y,
            "bird_velocity": self.bird.velocity_y,
        }

        # Add time-based information
        if self.state == GameState.PLAYING and self.game_start_time > 0:
            info["play_time"] = current_time - self.game_start_time

        if self.state == GameState.GAME_OVER and self.game_over_time > 0:
            info["death_time"] = current_time - self.game_over_time

        if self.state == GameState.READY and self.ready_time > 0:
            info["ready_time"] = current_time - self.ready_time

        # Add next pipe info for debugging/assistance
        next_pipe = self.pipe_manager.get_next_pipe()
        if next_pipe[0] > 0:  # Valid pipe data
            info["next_pipe"] = {
                "x": next_pipe[0],
                "gap_top": next_pipe[1],
                "gap_bottom": next_pipe[2],
                "gap_center": (next_pipe[1] + next_pipe[2]) / 2,
            }

        return info

    def get_difficulty_info(self) -> dict:
        """
        Get current difficulty settings.

        Returns:
            Dictionary with difficulty information
        """
        # Get current pipe parameters
        current_gap = max(
            self.pipe_manager.min_gap_size,
            self.pipe_manager.base_gap_size - (self.score * self.pipe_manager.gap_reduction_per_score),
        )

        current_speed = min(self.pipe_manager.max_speed, self.pipe_manager.base_speed + (self.score * 0.1))

        return {
            "score": self.score,
            "gap_size": current_gap,
            "pipe_speed": current_speed,
            "difficulty_level": min(10, self.score // 5 + 1),  # Level 1-10
        }
