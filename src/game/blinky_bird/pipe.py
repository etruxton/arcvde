"""
Cyberpunk skyscraper obstacles for Blinky Bird game.
Handles building generation, movement, and collision detection.
"""

# Standard library imports
import math
import random
import time
from typing import List, Tuple

# Third-party imports
import pygame


class SkyscraperGap:
    """
    A gap between two skyscraper segments that the bird must fly through.

    Features:
    - Configurable gap size
    - Neon lighting effects
    - Smooth movement
    - Collision detection
    - Scoring when passed
    """

    def __init__(self, x: float, screen_height: int, gap_size: int = 150):
        """
        Initialize a skyscraper gap.

        Args:
            x: X position of the gap
            screen_height: Height of the game screen
            gap_size: Size of the gap between building segments
        """
        self.x = x
        self.screen_height = screen_height
        self.width = 80  # Wider buildings than pipes
        self.gap_size = gap_size

        # Random gap position (avoid too high or too low)
        min_gap_center = gap_size // 2 + 80
        max_gap_center = screen_height - gap_size // 2 - 80
        self.gap_center = random.randint(min_gap_center, max_gap_center)

        # Calculate building segment heights
        self.top_height = self.gap_center - gap_size // 2
        self.bottom_y = self.gap_center + gap_size // 2
        self.bottom_height = screen_height - self.bottom_y

        # Movement (from reference Flappy Bird)
        self.speed = 4.3  # 128 pixels/sec at 30fps, will be set by PipeManager

        # Scoring
        self.scored = False

        # Cyberpunk building colors
        self.building_color = (25, 25, 40)  # Dark building
        self.building_edge = (60, 60, 80)  # Lighter building edges
        self.neon_color = random.choice(
            [
                (0, 255, 255),  # Cyan
                (255, 0, 255),  # Magenta
                (255, 255, 0),  # Yellow
                (0, 255, 100),  # Green
                (255, 100, 0),  # Orange
            ]
        )
        self.window_color = tuple(c // 2 for c in self.neon_color)  # Dimmer windows

        # Animation
        self.glow_time = random.uniform(0, 10)
        self.pulse_speed = random.uniform(1.5, 3.0)

    def update(self, dt: float):
        """
        Update building position and animations.

        Args:
            dt: Delta time in seconds
        """
        self.x -= self.speed
        self.glow_time += dt

    def get_top_rect(self) -> pygame.Rect:
        """Get collision rectangle for top pipe."""
        return pygame.Rect(self.x, 0, self.width, self.top_height)

    def get_bottom_rect(self) -> pygame.Rect:
        """Get collision rectangle for bottom pipe."""
        return pygame.Rect(self.x, self.bottom_y, self.width, self.bottom_height)

    def get_rects(self) -> List[pygame.Rect]:
        """Get both collision rectangles."""
        return [self.get_top_rect(), self.get_bottom_rect()]

    def is_off_screen(self) -> bool:
        """Check if pipe is completely off screen."""
        return self.x + self.width < 0

    def can_score(self, bird_x: float) -> bool:
        """
        Check if bird has passed this pipe for scoring.

        Args:
            bird_x: X position of the bird

        Returns:
            True if bird passed and hasn't been scored yet
        """
        if not self.scored and bird_x > self.x + self.width:
            self.scored = True
            return True
        return False

    def draw(self, surface: pygame.Surface):
        """
        Draw the cyberpunk skyscraper segments with neon effects.

        Args:
            surface: Pygame surface to draw on
        """
        # Calculate pulsing glow intensity
        pulse = (math.sin(self.glow_time * self.pulse_speed) + 1) * 0.5  # 0 to 1
        glow_alpha = int(30 + pulse * 50)

        # Draw top building segment
        top_rect = self.get_top_rect()
        if top_rect.height > 0:
            # Main building body
            pygame.draw.rect(surface, self.building_color, top_rect)

            # Draw windows in a grid pattern
            self._draw_building_windows(surface, top_rect, pulse)

            # Neon edge glow on the gap side (bottom edge)
            glow_surface = pygame.Surface((self.width, 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.neon_color, glow_alpha), (0, 0, self.width, 8))
            surface.blit(glow_surface, (self.x, self.top_height - 4))

            # Bright neon edge line
            pygame.draw.line(surface, self.neon_color, (self.x, self.top_height), (self.x + self.width, self.top_height), 3)

            # Building outline
            pygame.draw.rect(surface, self.building_edge, top_rect, 1)

            # Vertical neon accent lines
            for i in range(1, 4):
                line_x = self.x + (self.width // 4) * i
                line_alpha = int(glow_alpha * 0.7)
                line_surface = pygame.Surface((2, top_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(line_surface, (*self.neon_color, line_alpha), (0, 0, 2, top_rect.height))
                surface.blit(line_surface, (line_x, 0))

        # Draw bottom building segment
        bottom_rect = self.get_bottom_rect()
        if bottom_rect.height > 0:
            # Main building body
            pygame.draw.rect(surface, self.building_color, bottom_rect)

            # Draw windows in a grid pattern
            self._draw_building_windows(surface, bottom_rect, pulse)

            # Neon edge glow on the gap side (top edge)
            glow_surface = pygame.Surface((self.width, 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.neon_color, glow_alpha), (0, 0, self.width, 8))
            surface.blit(glow_surface, (self.x, self.bottom_y - 4))

            # Bright neon edge line
            pygame.draw.line(surface, self.neon_color, (self.x, self.bottom_y), (self.x + self.width, self.bottom_y), 3)

            # Building outline
            pygame.draw.rect(surface, self.building_edge, bottom_rect, 1)

            # Vertical neon accent lines
            for i in range(1, 4):
                line_x = self.x + (self.width // 4) * i
                line_alpha = int(glow_alpha * 0.7)
                line_surface = pygame.Surface((2, bottom_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(line_surface, (*self.neon_color, line_alpha), (0, 0, 2, bottom_rect.height))
                surface.blit(line_surface, (line_x, self.bottom_y))

    def _draw_building_windows(self, surface: pygame.Surface, building_rect: pygame.Rect, pulse: float):
        """Draw cyberpunk building windows."""
        window_width = 8
        window_height = 10
        window_spacing = 15

        # Calculate window grid
        cols = (building_rect.width - 10) // window_spacing
        rows = (building_rect.height - 10) // window_spacing

        for row in range(rows):
            for col in range(cols):
                # Random chance for lit windows
                if random.random() < 0.4:  # 40% chance
                    window_x = building_rect.x + 8 + (col * window_spacing)
                    window_y = building_rect.y + 8 + (row * window_spacing)

                    # Vary window brightness based on pulse and randomness
                    brightness = 0.3 + (pulse * 0.7) + random.uniform(-0.2, 0.2)
                    brightness = max(0.1, min(1.0, brightness))

                    window_color = tuple(int(c * brightness) for c in self.window_color)

                    window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
                    pygame.draw.rect(surface, window_color, window_rect)

                    # Occasional window glow effect
                    if brightness > 0.8 and random.random() < 0.1:
                        glow_surface = pygame.Surface((window_width + 4, window_height + 4), pygame.SRCALPHA)
                        pygame.draw.rect(glow_surface, (*self.window_color, 40), (0, 0, window_width + 4, window_height + 4))
                        surface.blit(glow_surface, (window_x - 2, window_y - 2))


class PipeManager:
    """
    Manages multiple skyscraper gaps, spawning, movement, and cleanup.
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize skyscraper gap manager.

        Args:
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pipes: List[SkyscraperGap] = []

        # Spawning configuration (consistent natural spacing)
        self.spawn_distance = 300  # Natural spacing - not too close, not too far
        self.next_spawn_x = screen_width + 50
        self.last_pipe_spawn_x = screen_width + 50

        # Difficulty scaling (larger gap for easier gameplay)
        self.base_gap_size = 225  # Larger than reference for easier flying
        self.min_gap_size = 150  # Keep consistent
        self.gap_reduction_per_score = 0  # No difficulty scaling
        self.max_speed = 4.3  # 128 pixels/sec at 30fps ≈ 4.3 pixels/frame
        self.base_speed = 4.3  # Constant speed like reference

    def update(self, dt: float, score: int):
        """
        Update all pipes and spawn new ones as needed.

        Args:
            dt: Delta time in seconds
            score: Current game score for difficulty scaling
        """
        # Update existing pipes
        for pipe in self.pipes:
            pipe.update(dt)

        # Remove off-screen pipes
        self.pipes = [pipe for pipe in self.pipes if not pipe.is_off_screen()]

        # Spawn new pipes - only when we need one and there's enough distance
        should_spawn = False
        if len(self.pipes) == 0:
            # No pipes exist, spawn the first one
            should_spawn = True
        else:
            # Check if the last pipe has moved far enough left to spawn a new one
            rightmost_pipe_x = max(pipe.x for pipe in self.pipes)
            if rightmost_pipe_x <= self.screen_width - self.spawn_distance:
                should_spawn = True

        if should_spawn:
            self.spawn_pipe(score)

    def spawn_pipe(self, score: int):
        """
        Spawn a new skyscraper gap with difficulty scaling.

        Args:
            score: Current game score
        """
        # Calculate difficulty-scaled parameters
        gap_size = max(self.min_gap_size, self.base_gap_size - (score * self.gap_reduction_per_score))

        # Create new skyscraper gap with consistent spacing
        if len(self.pipes) == 0:
            # First pipe starts closer for immediate action
            spawn_x = self.screen_width * 0.8
        else:
            # Subsequent pipes spawn at consistent distance from the rightmost pipe
            rightmost_pipe_x = max(pipe.x for pipe in self.pipes)
            spawn_x = rightmost_pipe_x + self.spawn_distance
        skyscraper_gap = SkyscraperGap(spawn_x, self.screen_height, gap_size)

        # Scale speed with score (but cap it)
        speed_increase = score * 0.1
        skyscraper_gap.speed = min(self.max_speed, self.base_speed + speed_increase)

        self.pipes.append(skyscraper_gap)

    def check_collisions(self, bird_rect: pygame.Rect) -> bool:
        """
        Check if bird collides with any skyscraper segments.

        Args:
            bird_rect: Bird's collision rectangle

        Returns:
            True if collision detected
        """
        for skyscraper_gap in self.pipes:
            for building_rect in skyscraper_gap.get_rects():
                if bird_rect.colliderect(building_rect):
                    return True
        return False

    def check_scoring(self, bird_x: float) -> int:
        """
        Check if bird passed any skyscraper gaps for scoring.

        Args:
            bird_x: X position of the bird

        Returns:
            Number of gaps passed (usually 0 or 1)
        """
        score_increase = 0
        for skyscraper_gap in self.pipes:
            if skyscraper_gap.can_score(bird_x):
                score_increase += 1
        return score_increase

    def draw(self, surface: pygame.Surface):
        """
        Draw all skyscraper gaps.

        Args:
            surface: Pygame surface to draw on
        """
        for skyscraper_gap in self.pipes:
            skyscraper_gap.draw(surface)

    def reset(self):
        """Reset pipe manager to initial state."""
        self.pipes.clear()
        self.next_spawn_x = self.screen_width + 50
        self.last_pipe_spawn_x = self.screen_width + 50

    def get_next_pipe(self) -> Tuple[float, float, float]:
        """
        Get information about the next pipe for AI/debugging.

        Returns:
            Tuple of (pipe_x, gap_top, gap_bottom) or (0, 0, 0) if no pipes
        """
        for pipe in self.pipes:
            if pipe.x > 0:  # First pipe that's still on screen
                gap_top = pipe.gap_center - pipe.gap_size // 2
                gap_bottom = pipe.gap_center + pipe.gap_size // 2
                return (pipe.x, gap_top, gap_bottom)
        return (0, 0, 0)
