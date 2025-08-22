"""
Target class for the shooting game
"""

# Standard library imports
import math
import random
import time

# Third-party imports
import pygame

# Local application imports
from utils.constants import (
    MAX_TARGETS,
    RED,
    TARGET_SIZE,
    TARGET_SPAWN_TIME,
    WHITE,
    YELLOW,
)


class Target:
    """A target that can be shot"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.radius = TARGET_SIZE // 2
        self.hit = False
        self.hit_time = 0
        self.spawn_time = time.time()

        # Animation properties
        self.pulse_time = 0
        self.hit_animation_duration = 0.3

    def update(self, dt: float) -> None:
        """Update target state"""
        self.pulse_time += dt

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the target"""
        if not self.hit:
            # Pulsing effect
            pulse_factor = 1 + 0.1 * math.sin(self.pulse_time * 3)
            current_radius = int(self.radius * pulse_factor)

            # Draw target circles (bullseye pattern)
            pygame.draw.circle(screen, RED, (self.x, self.y), current_radius)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), current_radius - 10)
            pygame.draw.circle(screen, RED, (self.x, self.y), current_radius - 20)
            pygame.draw.circle(screen, WHITE, (self.x, self.y), 5)
        else:
            # Hit animation
            time_since_hit = time.time() - self.hit_time
            if time_since_hit < self.hit_animation_duration:
                # Expanding circles animation
                animation_progress = time_since_hit / self.hit_animation_duration

                # First explosion ring
                ring1_radius = int(self.radius + 20 * animation_progress)
                ring1_alpha = int(255 * (1 - animation_progress))

                # Second explosion ring
                ring2_radius = int(self.radius + 40 * animation_progress)
                ring2_alpha = int(128 * (1 - animation_progress))

                # Create surfaces for alpha blending
                if ring1_alpha > 0:
                    ring1_surface = pygame.Surface((ring1_radius * 2, ring1_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring1_surface, (*YELLOW, ring1_alpha), (ring1_radius, ring1_radius), ring1_radius, 3)
                    screen.blit(ring1_surface, (self.x - ring1_radius, self.y - ring1_radius))

                if ring2_alpha > 0:
                    ring2_surface = pygame.Surface((ring2_radius * 2, ring2_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring2_surface, (*WHITE, ring2_alpha), (ring2_radius, ring2_radius), ring2_radius, 2)
                    screen.blit(ring2_surface, (self.x - ring2_radius, self.y - ring2_radius))

    def check_hit(self, x: int, y: int) -> bool:
        """Check if the target was hit at the given coordinates"""
        if self.hit:
            return False

        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        if distance <= self.radius:
            self.hit = True
            self.hit_time = time.time()
            return True

        return False

    def is_expired(self) -> bool:
        """Check if hit animation is finished"""
        if not self.hit:
            return False

        return time.time() - self.hit_time > self.hit_animation_duration

    def get_score_value(self) -> int:
        """Get the score value for hitting this target"""
        # Could add different scoring based on target type, time to hit, etc.
        return 10


class TargetManager:
    """Manages all targets in the game"""

    def __init__(self, screen_width: int, screen_height: int, camera_area: tuple):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.camera_area = camera_area  # (x, y, width, height)

        self.targets = []
        self.last_spawn_time = 0
        self.spawn_interval = TARGET_SPAWN_TIME
        self.max_targets = MAX_TARGETS

    def update(self, dt: float, current_time: int) -> None:
        """Update all targets"""
        # Update existing targets
        for target in self.targets:
            target.update(dt)

        # Remove expired targets
        self.targets = [t for t in self.targets if not t.is_expired()]

        # Spawn new targets
        if current_time - self.last_spawn_time > self.spawn_interval and len(self.targets) < self.max_targets:
            self.spawn_target()
            self.last_spawn_time = current_time

    def spawn_target(self) -> None:
        """Spawn a new target at a random location"""
        attempts = 0
        max_attempts = 50

        # Define spawn area - 600x400 rectangle in the middle of screen
        spawn_width = 600
        spawn_height = 400
        spawn_x = (self.screen_width - spawn_width) // 2
        spawn_y = (self.screen_height - spawn_height) // 2

        while attempts < max_attempts:
            # Generate random position within the spawn rectangle
            x = random.randint(spawn_x + TARGET_SIZE, spawn_x + spawn_width - TARGET_SIZE)
            y = random.randint(spawn_y + TARGET_SIZE, spawn_y + spawn_height - TARGET_SIZE)

            # Check if position conflicts with existing targets
            too_close = False
            for existing_target in self.targets:
                if not existing_target.hit:
                    distance = math.sqrt((x - existing_target.x) ** 2 + (y - existing_target.y) ** 2)
                    if distance < TARGET_SIZE * 2:  # Minimum distance between targets
                        too_close = True
                        break

            if not too_close:
                self.targets.append(Target(x, y))
                break

            attempts += 1

    def draw(self, screen: pygame.Surface) -> None:
        """Draw all targets"""
        for target in self.targets:
            target.draw(screen)

    def check_hit(self, x: int, y: int) -> int:
        """Check if any target was hit, return score gained"""
        for target in self.targets:
            if target.check_hit(x, y):
                return target.get_score_value()
        return 0

    def get_active_target_count(self) -> int:
        """Get number of active (non-hit) targets"""
        return len([t for t in self.targets if not t.hit])

    def clear_all_targets(self) -> None:
        """Clear all targets"""
        self.targets.clear()
        self.last_spawn_time = 0
