"""
Cyberpunk city background rendering for Blinky Bird.
Creates a scrolling neon cityscape with glowing skyscrapers.
"""

# Standard library imports
import math
import random
import time
from typing import List, Tuple

# Third-party imports
import pygame


class Skyscraper:
    """A single skyscraper building with neon effects."""

    def __init__(self, x: float, y: float, width: float, height: float, speed_factor: float):
        """
        Initialize a skyscraper.

        Args:
            x: X position
            y: Y position (ground level)
            width: Building width
            height: Building height
            speed_factor: How fast this building moves (for parallax)
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed_factor = speed_factor
        self.base_speed = 0.75

        # Building colors
        self.building_color = (20, 20, 35)  # Dark building
        self.window_color = random.choice(
            [
                (0, 255, 255),  # Cyan
                (255, 0, 255),  # Magenta
                (255, 255, 0),  # Yellow
                (0, 255, 0),  # Green
                (255, 100, 100),  # Red
            ]
        )
        self.window_dim = tuple(c // 3 for c in self.window_color)  # Dimmed version

        # Window pattern
        self.window_rows = int(height // 25)
        self.window_cols = int(width // 15)
        self.window_pattern = []
        for row in range(self.window_rows):
            row_pattern = []
            for col in range(self.window_cols):
                # Random chance for lit windows, more at top floors
                chance = 0.3 + (row / self.window_rows) * 0.4
                row_pattern.append(random.random() < chance)
            self.window_pattern.append(row_pattern)

        # Neon accent colors
        self.neon_color = random.choice(
            [
                (0, 255, 255),  # Cyan
                (255, 0, 255),  # Magenta
                (255, 255, 0),  # Yellow
            ]
        )

        # Animation for flickering
        self.flicker_time = random.uniform(0, 10)

    def update(self, dt: float):
        """Update building position and animations."""
        self.x -= self.base_speed * self.speed_factor
        self.flicker_time += dt

    def is_off_screen(self, screen_width: int) -> bool:
        """Check if building is off screen."""
        return self.x < -self.width

    def draw(self, surface: pygame.Surface):
        """Draw the skyscraper with neon effects."""
        building_rect = pygame.Rect(int(self.x), int(self.y - self.height), int(self.width), int(self.height))

        # Draw main building
        pygame.draw.rect(surface, self.building_color, building_rect)

        # Draw windows
        window_width = 8
        window_height = 12
        for row in range(self.window_rows):
            for col in range(self.window_cols):
                if col < len(self.window_pattern[row]) and self.window_pattern[row][col]:
                    window_x = self.x + 8 + (col * 15)
                    window_y = self.y - self.height + 8 + (row * 25)

                    # Flickering effect
                    flicker_phase = math.sin(self.flicker_time * 3 + col + row)
                    is_bright = flicker_phase > -0.8  # Most of the time bright

                    color = self.window_color if is_bright else self.window_dim

                    window_rect = pygame.Rect(int(window_x), int(window_y), window_width, window_height)
                    pygame.draw.rect(surface, color, window_rect)

                    # Window glow effect for bright windows
                    if is_bright and random.random() < 0.3:  # Only some windows glow
                        glow_surface = pygame.Surface((window_width + 6, window_height + 6), pygame.SRCALPHA)
                        pygame.draw.rect(glow_surface, (*color[:3], 30), (0, 0, window_width + 6, window_height + 6))
                        surface.blit(glow_surface, (window_x - 3, window_y - 3))

        # Clean neon building outline - draw each side separately for precision
        pygame.draw.line(
            surface, self.neon_color, (int(self.x), int(self.y - self.height)), (int(self.x), int(self.y)), 1
        )  # Left
        pygame.draw.line(
            surface,
            self.neon_color,
            (int(self.x + self.width), int(self.y - self.height)),
            (int(self.x + self.width), int(self.y)),
            1,
        )  # Right
        pygame.draw.line(
            surface,
            self.neon_color,
            (int(self.x), int(self.y - self.height)),
            (int(self.x + self.width), int(self.y - self.height)),
            1,
        )  # Top
        pygame.draw.line(
            surface, self.neon_color, (int(self.x), int(self.y)), (int(self.x + self.width), int(self.y)), 1
        )  # Bottom


class CyberGround:
    """Cyberpunk city street with neon reflections."""

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the cyber ground.

        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ground_height = 80
        self.ground_y = screen_height - self.ground_height

        # Scrolling
        self.scroll_x = 0
        self.scroll_speed = 1.5

        # Cyberpunk colors
        self.street_color = (15, 15, 25)  # Dark street
        self.line_color = (0, 255, 255)  # Cyan street lines
        self.glow_color = (255, 0, 255)  # Magenta glow
        self.reflection_color = (40, 40, 60)  # Subtle reflections

        # Animation
        self.glow_time = 0

    def update(self, dt: float):
        """Update ground scrolling and animations."""
        self.scroll_x += self.scroll_speed
        self.glow_time += dt
        # Reset scroll when it reaches tile width
        if self.scroll_x >= 60:  # Tile width
            self.scroll_x = 0

    def draw(self, surface: pygame.Surface):
        """Draw the cyberpunk street."""
        # Fill street area
        street_rect = pygame.Rect(0, self.ground_y, self.screen_width, self.ground_height)
        pygame.draw.rect(surface, self.street_color, street_rect)

        # Draw animated neon street lines
        tile_width = 60
        glow_intensity = (math.sin(self.glow_time * 2) + 1) * 0.5  # 0 to 1

        for x in range(-tile_width, self.screen_width + tile_width, tile_width):
            offset_x = x - self.scroll_x

            # Main street line
            line_y = self.ground_y + 20
            line_color_with_glow = tuple(int(c * (0.5 + glow_intensity * 0.5)) for c in self.line_color)
            pygame.draw.line(surface, line_color_with_glow, (offset_x, line_y), (offset_x + 40, line_y), 3)

            # Side lane markers
            for i in range(3):
                marker_x = offset_x + (i * 20)
                marker_y = self.ground_y + 40
                pygame.draw.rect(surface, self.line_color, (marker_x, marker_y, 15, 3))

        # Street glow effect on top edge
        glow_surface = pygame.Surface((self.screen_width, 10), pygame.SRCALPHA)
        glow_alpha = int(30 + glow_intensity * 20)
        pygame.draw.rect(glow_surface, (*self.glow_color, glow_alpha), (0, 0, self.screen_width, 10))
        surface.blit(glow_surface, (0, self.ground_y - 5))

        # Main street outline
        pygame.draw.line(surface, self.line_color, (0, self.ground_y), (self.screen_width, self.ground_y), 2)


class Background:
    """
    Manages the complete cyberpunk cityscape with skyline, buildings, and street.
    Implements parallax scrolling for depth effect.
    """

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the cyberpunk background.

        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Night sky colors (gradient from top to bottom)
        self.sky_top = (5, 5, 15)  # Very dark purple/black
        self.sky_middle = (15, 10, 30)  # Dark purple
        self.sky_bottom = (25, 15, 40)  # Lighter purple near horizon

        # Initialize cyber ground
        self.ground = CyberGround(screen_width, screen_height)

        # Initialize skyscrapers with different layers for parallax
        self.skyscrapers_far: List[Skyscraper] = []  # Far background buildings
        self.skyscrapers_near: List[Skyscraper] = []  # Near background buildings
        self.spawn_skyscrapers()

        # Particle effects for atmosphere
        self.stars = []
        self.spawn_stars()

    def spawn_skyscrapers(self):
        """Spawn initial skyscrapers across the screen with parallax layers."""
        # Far layer skyscrapers (smaller, slower)
        num_far = 6
        for i in range(num_far):
            x = random.randint(-200, self.screen_width + 400)
            width = random.randint(60, 120)
            height = random.randint(200, 400)
            speed_factor = random.uniform(0.3, 0.6)  # Slower for distance

            skyscraper = Skyscraper(x, self.ground.ground_y, width, height, speed_factor)
            self.skyscrapers_far.append(skyscraper)

        # Near layer skyscrapers (larger, faster)
        num_near = 4
        for i in range(num_near):
            x = random.randint(-100, self.screen_width + 200)
            width = random.randint(80, 150)
            height = random.randint(300, 600)
            speed_factor = random.uniform(0.8, 1.2)  # Faster for foreground

            skyscraper = Skyscraper(x, self.ground.ground_y, width, height, speed_factor)
            self.skyscrapers_near.append(skyscraper)

    def spawn_stars(self):
        """Spawn twinkling stars in the sky."""
        num_stars = 50
        for i in range(num_stars):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.ground.ground_y // 2)
            brightness = random.uniform(0.3, 1.0)
            twinkle_speed = random.uniform(0.5, 2.0)

            self.stars.append(
                {
                    "x": x,
                    "y": y,
                    "brightness": brightness,
                    "twinkle_speed": twinkle_speed,
                    "twinkle_time": random.uniform(0, 10),
                }
            )

    def update(self, dt: float):
        """
        Update all background elements.

        Args:
            dt: Delta time in seconds
        """
        # Update ground
        self.ground.update(dt)

        # Update far skyscrapers
        for skyscraper in self.skyscrapers_far:
            skyscraper.update(dt)

        # Update near skyscrapers
        for skyscraper in self.skyscrapers_near:
            skyscraper.update(dt)

        # Remove off-screen skyscrapers and spawn new ones
        self.skyscrapers_far = [s for s in self.skyscrapers_far if not s.is_off_screen(self.screen_width)]
        self.skyscrapers_near = [s for s in self.skyscrapers_near if not s.is_off_screen(self.screen_width)]

        # Maintain building population
        while len(self.skyscrapers_far) < 6:
            x = self.screen_width + random.randint(50, 200)
            width = random.randint(60, 120)
            height = random.randint(200, 400)
            speed_factor = random.uniform(0.3, 0.6)

            skyscraper = Skyscraper(x, self.ground.ground_y, width, height, speed_factor)
            self.skyscrapers_far.append(skyscraper)

        while len(self.skyscrapers_near) < 4:
            x = self.screen_width + random.randint(50, 200)
            width = random.randint(80, 150)
            height = random.randint(300, 600)
            speed_factor = random.uniform(0.8, 1.2)

            skyscraper = Skyscraper(x, self.ground.ground_y, width, height, speed_factor)
            self.skyscrapers_near.append(skyscraper)

        # Update stars
        for star in self.stars:
            star["twinkle_time"] += dt

    def draw(self, surface: pygame.Surface):
        """
        Draw the complete cyberpunk cityscape.

        Args:
            surface: Pygame surface to draw on
        """
        # Draw night sky gradient
        self._draw_night_sky_gradient(surface)

        # Draw stars
        self._draw_stars(surface)

        # Draw far skyscrapers (background layer)
        for skyscraper in self.skyscrapers_far:
            skyscraper.draw(surface)

        # Draw near skyscrapers (foreground layer)
        for skyscraper in self.skyscrapers_near:
            skyscraper.draw(surface)

        # Draw street (in front of buildings)
        self.ground.draw(surface)

    def _draw_night_sky_gradient(self, surface: pygame.Surface):
        """Draw a cyberpunk night sky gradient."""
        sky_height = self.ground.ground_y

        for y in range(sky_height):
            # Create a gradient from top to middle to bottom
            if y < sky_height // 2:
                # Top to middle
                ratio = y / (sky_height // 2)
                r = int(self.sky_top[0] + (self.sky_middle[0] - self.sky_top[0]) * ratio)
                g = int(self.sky_top[1] + (self.sky_middle[1] - self.sky_top[1]) * ratio)
                b = int(self.sky_top[2] + (self.sky_middle[2] - self.sky_top[2]) * ratio)
            else:
                # Middle to bottom
                ratio = (y - sky_height // 2) / (sky_height // 2)
                r = int(self.sky_middle[0] + (self.sky_bottom[0] - self.sky_middle[0]) * ratio)
                g = int(self.sky_middle[1] + (self.sky_bottom[1] - self.sky_middle[1]) * ratio)
                b = int(self.sky_middle[2] + (self.sky_bottom[2] - self.sky_middle[2]) * ratio)

            color = (r, g, b)
            pygame.draw.line(surface, color, (0, y), (self.screen_width, y))

    def _draw_stars(self, surface: pygame.Surface):
        """Draw twinkling stars in the night sky."""
        for star in self.stars:
            # Calculate twinkling effect
            twinkle = math.sin(star["twinkle_time"] * star["twinkle_speed"])
            alpha = int((star["brightness"] * 150) * (0.7 + 0.3 * twinkle))

            if alpha > 50:  # Only draw bright enough stars
                star_color = (200, 200, 255, alpha)  # Slightly blue-white
                star_surface = pygame.Surface((3, 3), pygame.SRCALPHA)
                pygame.draw.circle(star_surface, star_color, (1, 1), 1)
                surface.blit(star_surface, (star["x"], star["y"]))

    def get_ground_y(self) -> int:
        """Get the Y position of the ground surface."""
        return self.ground.ground_y

    def reset(self):
        """Reset background to initial state."""
        self.ground.scroll_x = 0
        self.ground.glow_time = 0
        self.skyscrapers_far.clear()
        self.skyscrapers_near.clear()
        self.spawn_skyscrapers()

        # Reset star twinkle times
        for star in self.stars:
            star["twinkle_time"] = random.uniform(0, 10)
