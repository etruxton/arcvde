"""
Bird class for Winky Bird game.
Handles bird physics, animation, and rendering.
"""

# Standard library imports
import math
from typing import Tuple

# Third-party imports
import pygame


class Bird:
    """
    The player-controlled bird in Winky Bird.

    Features:
    - Physics-based movement with gravity and flapping
    - Smooth rotation based on velocity
    - Animated flapping wings
    - Collision detection
    """

    def __init__(self, x: float, y: float):
        """
        Initialize the bird.

        Args:
            x: Starting x position
            y: Starting y position
        """
        # Position and physics
        self.x = x
        self.y = y
        self.velocity_y = 0
        self.gravity = 0.6
        self.flap_strength = -10  # Increased from -8 for better bounce
        self.max_fall_speed = 10
        self.max_rise_speed = -12  # Slightly reduced max rise speed too

        # Visual properties
        self.radius = 20
        self.rotation = 0
        self.max_rotation_down = 45  # degrees when falling
        self.max_rotation_up = -20  # degrees when rising

        # Animation
        self.flap_animation_time = 0
        self.flap_duration = 0.3  # seconds
        self.is_flapping = False

        # State
        self.is_alive = True

        # Cyberpunk colors for drawing
        self.body_color = (40, 40, 60)  # Dark metallic body
        self.body_accent = (0, 255, 255)  # Cyan neon accents
        self.wing_color = (60, 60, 80)  # Darker metallic wings
        self.wing_accent = (255, 0, 255)  # Magenta neon wing edges
        self.beak_color = (150, 150, 170)  # Silver-ish beak
        self.eye_color = (255, 255, 255)  # White eye (keeping googly eyes)
        self.pupil_color = (0, 255, 150)  # Bright green cyber pupil
        self.glow_color = (0, 255, 255)  # Cyan glow effect

    def flap(self):
        """Make the bird flap (wink detected)."""
        if self.is_alive:
            self.velocity_y = self.flap_strength
            self.is_flapping = True
            self.flap_animation_time = 0

    def update(self, dt: float, apply_physics: bool = True):
        """
        Update bird physics and animation.

        Args:
            dt: Delta time in seconds
            apply_physics: Whether to apply gravity and movement (False during calibration)
        """
        if not self.is_alive:
            return

        # Only apply physics if enabled (disabled during calibration)
        if apply_physics:
            # Apply gravity
            self.velocity_y += self.gravity

            # Clamp velocity
            self.velocity_y = max(self.max_rise_speed, min(self.max_fall_speed, self.velocity_y))

            # Update position
            self.y += self.velocity_y

            # Update rotation based on velocity
            # Map velocity to rotation angle
            velocity_ratio = self.velocity_y / self.max_fall_speed
            if self.velocity_y > 0:  # Falling
                self.rotation = velocity_ratio * self.max_rotation_down
            else:  # Rising
                velocity_ratio = abs(self.velocity_y) / abs(self.max_rise_speed)
                self.rotation = velocity_ratio * self.max_rotation_up

            # Clamp rotation
            self.rotation = max(self.max_rotation_up, min(self.max_rotation_down, self.rotation))
        else:
            # During calibration, keep bird horizontal and still
            self.velocity_y = 0
            self.rotation = 0

        # Update flap animation
        if self.is_flapping:
            self.flap_animation_time += dt
            if self.flap_animation_time >= self.flap_duration:
                self.is_flapping = False

    def get_rect(self) -> pygame.Rect:
        """
        Get collision rectangle for the bird.

        Returns:
            Pygame rectangle for collision detection
        """
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, surface: pygame.Surface):
        """
        Draw the redesigned cyberpunk bird with teardrop shape and layered wings.

        Args:
            surface: Pygame surface to draw on
        """
        if not self.is_alive:
            return

        # Calculate wing flap offset
        wing_offset = 0
        if self.is_flapping:
            flap_progress = self.flap_animation_time / self.flap_duration
            wing_offset = math.sin(flap_progress * math.pi * 4) * 4

        # Draw particle trails when moving
        self._draw_particle_trails(surface)

        # Calculate rotation for directional design
        angle_rad = math.radians(self.rotation)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)

        # Draw cyberpunk glow effect around body
        for i in range(3):
            glow_alpha = 25 - (i * 6)
            glow_offset = 12 + (i * 4)
            glow_surface = pygame.Surface((glow_offset * 2, glow_offset * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surface, (*self.glow_color, glow_alpha), (0, 0, glow_offset * 2, glow_offset * 2))
            surface.blit(glow_surface, (self.x - glow_offset, self.y - glow_offset))

        # Draw right wing BEHIND body (layered effect)
        self._draw_right_wing(surface, wing_offset, angle_rad)

        # Draw asymmetric teardrop body
        self._draw_teardrop_body(surface, angle_rad, cos_angle, sin_angle)

        # Draw left wing IN FRONT of body
        self._draw_left_wing(surface, wing_offset, angle_rad)

        # Draw pointed nose/beak for direction
        self._draw_pointed_nose(surface, angle_rad, cos_angle, sin_angle)

        # Draw cyberpunk googly eyes (keeping these!)
        self._draw_cyber_eyes(surface)

    def _draw_particle_trails(self, surface: pygame.Surface):
        """Draw particle trails behind the bird when moving."""
        if abs(self.velocity_y) > 2:  # Only when moving fast
            # Standard library imports
            import random
            import time

            # Create particle effect based on movement
            for i in range(3):
                # Particles trail behind the bird
                trail_x = self.x - 25 - (i * 8) + random.randint(-3, 3)
                trail_y = self.y + random.randint(-8, 8)

                # Particle size and alpha based on speed
                speed = abs(self.velocity_y)
                particle_size = max(1, int(speed * 0.3))
                alpha = max(20, int(speed * 15))

                # Color varies between cyan and magenta
                if i % 2 == 0:
                    color = (*self.glow_color, alpha)
                else:
                    color = (*self.wing_accent, alpha)

                # Draw particle
                particle_surface = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color, (particle_size, particle_size), particle_size)
                surface.blit(particle_surface, (trail_x - particle_size, trail_y - particle_size))

    def _draw_teardrop_body(self, surface: pygame.Surface, angle_rad: float, cos_angle: float, sin_angle: float):
        """Draw oval body."""
        body_width = self.radius * 1.1
        body_height = self.radius * 1.0

        # Create a surface for the rotated ellipse
        body_surface = pygame.Surface((body_width * 2, body_height * 2), pygame.SRCALPHA)

        # Draw ellipse on the surface
        pygame.draw.ellipse(body_surface, self.body_color, (0, 0, body_width * 2, body_height * 2))

        # Add metallic shine effect
        for i in range(2):
            shine_alpha = 30 - (i * 10)
            shine_size = (body_width * 2 * (0.8 - i * 0.2), body_height * 2 * (0.8 - i * 0.2))
            shine_pos = ((body_width * 2 - shine_size[0]) / 2, (body_height * 2 - shine_size[1]) / 2)

            shine_surface = pygame.Surface(shine_size, pygame.SRCALPHA)
            pygame.draw.ellipse(shine_surface, (255, 255, 255, shine_alpha), (0, 0, shine_size[0], shine_size[1]))
            body_surface.blit(shine_surface, shine_pos)

        # Neon body outline
        pygame.draw.ellipse(body_surface, self.body_accent, (0, 0, body_width * 2, body_height * 2), 2)

        # Rotate and blit the surface
        if abs(angle_rad) > 0.01:
            rotated_surface = pygame.transform.rotate(body_surface, -math.degrees(angle_rad))
            rotated_rect = rotated_surface.get_rect(center=(self.x, self.y))
            surface.blit(rotated_surface, rotated_rect.topleft)
        else:
            body_rect = body_surface.get_rect(center=(self.x, self.y))
            surface.blit(body_surface, body_rect.topleft)

    def _draw_left_wing(self, surface: pygame.Surface, wing_offset: float, angle_rad: float):
        """Draw left wing in front of body."""
        wing_base_x = self.x - 8
        wing_base_y = self.y + wing_offset

        wing_points = [
            (wing_base_x, wing_base_y),
            (wing_base_x - 18, wing_base_y - 12),
            (wing_base_x - 22, wing_base_y - 5),
            (wing_base_x - 20, wing_base_y + 10),
            (wing_base_x - 5, wing_base_y + 8),
        ]

        pygame.draw.polygon(surface, self.wing_color, wing_points)
        pygame.draw.polygon(surface, self.wing_accent, wing_points, 2)

        # Wing glow effect
        glow_surface = pygame.Surface((30, 25), pygame.SRCALPHA)
        adjusted_points = [(p[0] - wing_base_x + 15, p[1] - wing_base_y + 12) for p in wing_points]
        pygame.draw.polygon(glow_surface, (*self.wing_accent, 40), adjusted_points)
        surface.blit(glow_surface, (wing_base_x - 15, wing_base_y - 12))

    def _draw_right_wing(self, surface: pygame.Surface, wing_offset: float, angle_rad: float):
        """Draw right wing behind body."""
        wing_base_x = self.x + 5
        wing_base_y = self.y + wing_offset

        wing_points = [
            (wing_base_x, wing_base_y),
            (wing_base_x + 12, wing_base_y - 8),
            (wing_base_x + 15, wing_base_y - 2),
            (wing_base_x + 14, wing_base_y + 7),
            (wing_base_x + 3, wing_base_y + 6),
        ]

        darker_wing_color = tuple(int(c * 0.7) for c in self.wing_color)
        darker_accent = tuple(int(c * 0.8) for c in self.wing_accent)

        pygame.draw.polygon(surface, darker_wing_color, wing_points)
        pygame.draw.polygon(surface, darker_accent, wing_points, 1)

    def _draw_pointed_nose(self, surface: pygame.Surface, angle_rad: float, cos_angle: float, sin_angle: float):
        """Draw pointed beak."""
        beak_length = 12
        beak_width = 5

        beak_start_x = self.x + (self.radius * 0.8) * cos_angle
        beak_start_y = self.y + (self.radius * 0.8) * sin_angle

        beak_tip_x = beak_start_x + beak_length * cos_angle
        beak_tip_y = beak_start_y + beak_length * sin_angle

        beak_base_top_x = beak_start_x - (beak_width // 2) * sin_angle
        beak_base_top_y = beak_start_y + (beak_width // 2) * cos_angle
        beak_base_bottom_x = beak_start_x + (beak_width // 2) * sin_angle
        beak_base_bottom_y = beak_start_y - (beak_width // 2) * cos_angle

        beak_points = [(beak_tip_x, beak_tip_y), (beak_base_top_x, beak_base_top_y), (beak_base_bottom_x, beak_base_bottom_y)]

        pygame.draw.polygon(surface, self.beak_color, beak_points)
        pygame.draw.polygon(surface, self.body_accent, beak_points, 1)

        glow_surface = pygame.Surface((beak_length + 8, beak_width + 8), pygame.SRCALPHA)
        adjusted_points = [
            (p[0] - beak_start_x + beak_length // 2 + 4, p[1] - beak_start_y + beak_width // 2 + 4) for p in beak_points
        ]
        pygame.draw.polygon(glow_surface, (*self.body_accent, 30), adjusted_points)
        surface.blit(glow_surface, (beak_start_x - beak_length // 2 - 4, beak_start_y - beak_width // 2 - 4))

    def _draw_cyber_eyes(self, surface: pygame.Surface):
        """Draw the cyberpunk googly eyes (keeping these awesome!)."""
        eye_x = self.x + 3
        eye_y = self.y - 3
        eye_radius = 6

        # Eye glow effect
        for i in range(2):
            glow_alpha = 50 - (i * 15)
            glow_radius = eye_radius + 2 + (i * 2)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*self.pupil_color, glow_alpha), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (eye_x - glow_radius, eye_y - glow_radius))

        # White of eye (googly eye base)
        pygame.draw.circle(surface, self.eye_color, (int(eye_x), int(eye_y)), eye_radius)

        # Cyber pupil (moves based on velocity for personality)
        pupil_offset_x = max(-2, min(2, self.velocity_y * 0.2))
        pupil_offset_y = max(-1, min(1, -self.velocity_y * 0.1))
        pupil_x = eye_x + pupil_offset_x
        pupil_y = eye_y + pupil_offset_y
        pupil_radius = 3

        # Glowing cyber pupil
        pygame.draw.circle(surface, self.pupil_color, (int(pupil_x), int(pupil_y)), pupil_radius)

        # Pupil highlight
        highlight_x = pupil_x - 1
        highlight_y = pupil_y - 1
        pygame.draw.circle(surface, (255, 255, 255), (int(highlight_x), int(highlight_y)), 1)

        # Eye outline with neon accent
        pygame.draw.circle(surface, self.body_accent, (int(eye_x), int(eye_y)), eye_radius, 1)

    def reset(self, x: float, y: float):
        """
        Reset bird to starting state.

        Args:
            x: Starting x position
            y: Starting y position
        """
        self.x = x
        self.y = y
        self.velocity_y = 0
        self.rotation = 0
        self.is_alive = True
        self.is_flapping = False
        self.flap_animation_time = 0

    def kill(self):
        """Mark the bird as dead."""
        self.is_alive = False
