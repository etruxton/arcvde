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
from utils.ui_components import Button


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

        # UI Buttons
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None

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

        # Background
        self.create_background()

        # Animated scenery elements
        self.init_scenery()

        # Debug console
        self.console_active = False
        self.console_input = ""
        self.console_message = ""
        self.console_message_time = 0

    def create_background(self):
        """Create a nature/hunting background"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Sky gradient
        for y in range(SCREEN_HEIGHT * 2 // 3):
            progress = y / (SCREEN_HEIGHT * 2 // 3)
            color = (
                int(135 + (206 - 135) * progress),
                int(206 + (235 - 206) * progress),
                int(235 + (250 - 235) * progress),
            )
            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))

        # Draw distant mountains
        self.draw_mountain_layer(
            self.background,
            color=(170, 180, 200),
            peak_heights=[200, 280, 250, 300, 220],
            base_y=SCREEN_HEIGHT * 2 // 3 - 50,
            peak_variance=30,
        )

        # Draw middle mountains
        self.draw_mountain_layer(
            self.background,
            color=(140, 150, 180),  # Slightly darker blue-gray
            peak_heights=[180, 240, 200, 260],
            base_y=SCREEN_HEIGHT * 2 // 3 - 30,
            peak_variance=25,
        )

        # Draw rolling hills
        self.draw_hills_layer(
            self.background,
            color=(120, 130, 100),
            base_y=SCREEN_HEIGHT * 2 // 3,
            hill_count=5,
            max_height=80,
        )

        # Ground
        ground_color = (34, 139, 34)
        pygame.draw.rect(self.background, ground_color, (0, SCREEN_HEIGHT * 2 // 3, SCREEN_WIDTH, SCREEN_HEIGHT // 3))

        for _ in range(200):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(SCREEN_HEIGHT * 2 // 3, SCREEN_HEIGHT)
            height = random.randint(5, 15)
            pygame.draw.line(self.background, (46, 125, 50), (x, y), (x, y - height), 1)

        # Draw pond in bottom left corner
        pond_center_x = 100
        pond_center_y = SCREEN_HEIGHT - 40
        pond_width = 280
        pond_height = 140

        pond_rect = pygame.Rect(pond_center_x - pond_width // 2, pond_center_y - pond_height // 2, pond_width, pond_height)

        for i in range(pond_height // 2):
            color_factor = i / (pond_height // 2)
            water_color = (
                int(64 + 20 * color_factor),
                int(140 + 30 * color_factor),
                int(180 + 40 * color_factor),
            )
            pygame.draw.ellipse(
                self.background,
                water_color,
                (
                    pond_center_x - pond_width // 2 + i,
                    pond_center_y - pond_height // 2 + i,
                    pond_width - i * 2,
                    pond_height - i * 2,
                ),
            )

        pygame.draw.ellipse(self.background, (40, 90, 120), pond_rect, 3)

    def draw_mountain_layer(self, surface, color, peak_heights, base_y, peak_variance):
        """Draw a layer of mountains with jagged peaks"""
        points = [(0, base_y)]

        # Create mountain peaks
        num_peaks = len(peak_heights)
        for i, height in enumerate(peak_heights):
            x = (i + 1) * (SCREEN_WIDTH // (num_peaks + 1))

            if i > 0:
                mid_x = x - (SCREEN_WIDTH // (num_peaks + 1)) // 2
                mid_height = height - peak_variance - random.randint(20, 40)
                points.append((mid_x, base_y - mid_height))

            # Main peak with slight random variance
            peak_y = base_y - height + random.randint(-peak_variance, peak_variance)
            points.append((x, peak_y))

        # Complete the polygon
        points.append((SCREEN_WIDTH, base_y))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        points.append((0, SCREEN_HEIGHT))

        pygame.draw.polygon(surface, color, points)

        darker_color = tuple(max(0, c - 20) for c in color)
        pygame.draw.lines(surface, darker_color, False, points[: len(peak_heights) * 2 + 2], 2)

    def draw_hills_layer(self, surface, color, base_y, hill_count, max_height):
        """Draw rolling hills using smooth curves"""
        points = [(0, base_y)]

        # Create smooth rolling hills using sine waves
        for x in range(0, SCREEN_WIDTH + 10, 10):
            y = base_y
            for i in range(hill_count):
                amplitude = max_height * (0.5 + 0.5 * math.sin(i * 1.3))
                frequency = (i + 1) * 0.003
                phase = i * math.pi / 3
                y -= amplitude * (0.5 + 0.5 * math.sin(x * frequency + phase))

            points.append((x, y))

        # Complete the polygon
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        points.append((0, SCREEN_HEIGHT))

        pygame.draw.polygon(surface, color, points)

        lighter_color = tuple(min(255, c + 10) for c in color)
        for i in range(1, len(points) - 2):
            if points[i][1] < points[i - 1][1] and points[i][1] < points[i + 1][1]:  # Peak point
                pygame.draw.circle(surface, lighter_color, (int(points[i][0]), int(points[i][1])), 3)

    def init_scenery(self):
        """Initialize animated scenery elements"""
        # Define pond parameters
        self.pond_center_x = 100
        self.pond_center_y = SCREEN_HEIGHT - 40
        self.pond_width = 280
        self.pond_height = 140

        # Clouds
        self.clouds = []
        for i in range(5):
            cloud = {
                "x": random.randint(-200, SCREEN_WIDTH),
                "y": random.randint(30, 150),
                "speed": random.uniform(10, 30),
                "size": random.uniform(0.8, 1.5),
                "opacity": random.randint(180, 255),
                "type": random.randint(0, 2),  # Different cloud shapes
            }
            self.clouds.append(cloud)

        # Birds
        self.birds = []
        for i in range(3):
            bird = {
                "x": random.randint(-100, SCREEN_WIDTH + 100),
                "y": random.randint(50, 250),
                "speed": random.uniform(40, 80),
                "direction": random.choice([-1, 1]),
                "wing_phase": random.uniform(0, math.pi * 2),
                "size": random.uniform(0.8, 1.2),
            }
            self.birds.append(bird)

        # Floating particles (pollen/dandelion seeds)
        self.particles = []
        for i in range(30):
            particle = {
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "vx": random.uniform(-10, 10),
                "vy": random.uniform(5, 20),
                "size": random.uniform(2, 5),
                "opacity": random.randint(100, 200),
                "rotation": random.uniform(0, math.pi * 2),
                "rotation_speed": random.uniform(-2, 2),
            }
            self.particles.append(particle)

        # Swaying flowers (reduced count and better positioning)
        self.flowers = []
        ground_line = SCREEN_HEIGHT * 2 // 3  # Where capybaras walk
        pond_left = self.pond_center_x - self.pond_width // 2
        pond_right = self.pond_center_x + self.pond_width // 2
        pond_top = self.pond_center_y - self.pond_height // 2

        for i in range(12):
            # Calculate max height so flower doesn't extend above ground line
            # Flower position is its base, so we need to ensure top doesn't go above ground
            max_flower_height = 30  # Maximum height a flower can be
            min_y = ground_line + max_flower_height + 10  # Add buffer so flowers don't poke above
            min_spacing = 30  # Minimum distance between flowers

            # Keep trying until we get a position not in the pond and not overlapping other flowers
            attempts = 0
            valid_position = False
            x, y = 0, 0

            while attempts < 20 and not valid_position:  # Increased attempts for better placement
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(min_y, SCREEN_HEIGHT - 20)

                # Check if this position is in the pond area (with some margin)
                if pond_left - 20 < x < pond_right + 20 and y > pond_top - 20:
                    attempts += 1
                    continue

                # Check if too close to existing flowers
                too_close = False
                for existing_flower in self.flowers:
                    distance = math.sqrt((x - existing_flower["x"]) ** 2 + (y - existing_flower["y"]) ** 2)
                    if distance < min_spacing:
                        too_close = True
                        break

                if not too_close:
                    valid_position = True
                    break

                attempts += 1

                if valid_position:
                    flower = {
                        "x": x,
                        "y": y,
                        "sway_phase": random.uniform(0, math.pi * 2),
                        "sway_speed": random.uniform(0.5, 1.5),
                        "height": random.randint(15, 25),  # Reduced height range
                        "color": random.choice(
                            [
                                (255, 105, 180),  # Hot pink
                                (255, 255, 0),  # Yellow
                                (238, 130, 238),  # Violet
                                (255, 165, 0),  # Orange
                                (147, 112, 219),  # Purple
                            ]
                        ),
                        "petal_count": random.randint(5, 8),
                        "size": random.randint(8, 15),
                    }
                self.flowers.append(flower)

        # Animated grass tufts
        self.grass_tufts = []
        ground_line = SCREEN_HEIGHT * 2 // 3
        pond_left = self.pond_center_x - self.pond_width // 2
        pond_right = self.pond_center_x + self.pond_width // 2
        pond_top = self.pond_center_y - self.pond_height // 2

        # Create fewer but more visible grass tufts
        for _ in range(80):
            # Keep trying until we get a position not in the pond
            attempts = 0
            while attempts < 10:
                x = random.randint(10, SCREEN_WIDTH - 10)
                y = random.randint(ground_line + 10, SCREEN_HEIGHT - 10)

                # Check if this position is in the pond area (with some margin)
                if not (pond_left - 20 < x < pond_right + 20 and y > pond_top - 20):
                    # Not in pond, we can use this position
                    break
                attempts += 1

            grass = {
                "x": x,
                "y": y,
                "type": random.choice(["tall", "medium", "bushy"]),  # Different grass types
                "sway_phase": random.uniform(0, math.pi * 2),
                "sway_speed": random.uniform(0.6, 1.2),
                "color_variation": random.choice(
                    [
                        (46, 125, 50),  # Standard green
                        (56, 135, 60),  # Slightly brighter
                        (36, 115, 40),  # Slightly darker
                        (66, 145, 70),  # Light green
                    ]
                ),
                "size": random.uniform(0.8, 1.2),  # Size variation
            }
            self.grass_tufts.append(grass)

        # Sun rays
        self.sun_ray_angle = 0
        self.sun_x = SCREEN_WIDTH - 150
        self.sun_y = 100

        # Pond ripples
        self.pond_ripples = []
        self.ripple_spawn_timer = 0

        # Initialize a few ripples
        for i in range(3):
            # Keep ripples well within pond bounds
            ripple = {
                "x": self.pond_center_x + random.randint(-60, 60),
                "y": self.pond_center_y + random.randint(-40, 20),
                "radius": random.uniform(0, 20),
                "max_radius": random.uniform(25, 40),  # Smaller max radius to stay in bounds
                "speed": random.uniform(15, 25),
                "opacity": 255,
            }
            self.pond_ripples.append(ripple)

    def update_scenery(self, dt: float):
        """Update animated scenery elements"""
        current_time = pygame.time.get_ticks() / 1000.0

        for cloud in self.clouds:
            cloud["x"] += cloud["speed"] * dt
            if cloud["x"] > SCREEN_WIDTH + 200:
                cloud["x"] = -200
                cloud["y"] = random.randint(30, 150)  # Match initial spawn height

        for bird in self.birds:
            bird["x"] += bird["speed"] * bird["direction"] * dt
            bird["y"] += math.sin(current_time * 2 + bird["wing_phase"]) * 10 * dt
            bird["wing_phase"] += dt * 8

            # Wrap around
            if bird["direction"] > 0 and bird["x"] > SCREEN_WIDTH + 100:
                bird["x"] = -100
                bird["y"] = random.randint(50, 250)
            elif bird["direction"] < 0 and bird["x"] < -100:
                bird["x"] = SCREEN_WIDTH + 100
                bird["y"] = random.randint(50, 250)

        for particle in self.particles:
            # Gentle floating movement
            particle["x"] += particle["vx"] * dt + math.sin(current_time * 2 + particle["rotation"]) * 10 * dt
            particle["y"] += particle["vy"] * dt
            particle["rotation"] += particle["rotation_speed"] * dt

            if particle["y"] > SCREEN_HEIGHT + 10:
                particle["y"] = -10
                particle["x"] = random.randint(0, SCREEN_WIDTH)

        self.sun_ray_angle += dt * 0.1

        self.ripple_spawn_timer += dt
        if self.ripple_spawn_timer > random.uniform(1.5, 3.0):
            self.ripple_spawn_timer = 0
            # Spawn new ripple within pond bounds
            # Calculate safe spawn area considering ripple max size
            max_ripple_radius = 40
            safe_x_range = (self.pond_width // 2 - max_ripple_radius) * 0.8  # 80% to be safe
            safe_y_range = (self.pond_height // 2 - max_ripple_radius) * 0.8

            new_ripple = {
                "x": self.pond_center_x + random.randint(-int(safe_x_range), int(safe_x_range)),
                "y": self.pond_center_y + random.randint(-int(safe_y_range), int(safe_y_range // 2)),  # Less range below
                "radius": 0,
                "max_radius": random.uniform(25, 40),  # Smaller to stay in bounds
                "speed": random.uniform(15, 25),
                "opacity": 255,
            }
            self.pond_ripples.append(new_ripple)

        ripples_to_remove = []
        for ripple in self.pond_ripples:
            ripple["radius"] += ripple["speed"] * dt
            # Fade out as ripple expands
            ripple["opacity"] = max(0, 255 * (1 - ripple["radius"] / ripple["max_radius"]))

            if ripple["radius"] >= ripple["max_radius"]:
                ripples_to_remove.append(ripple)

        # Remove dead ripples
        for ripple in ripples_to_remove:
            self.pond_ripples.remove(ripple)

    def draw_scenery(self):
        """Draw animated scenery elements"""
        current_time = pygame.time.get_ticks() / 1000.0

        self.draw_sun_rays()

        # Draw clouds (behind everything)
        for cloud in self.clouds:
            self.draw_cloud(cloud)

        # Draw birds
        for bird in self.birds:
            self.draw_bird(bird, current_time)

        # Draw floating particles
        for particle in self.particles:
            self.draw_particle(particle)

        # Draw animated grass tufts
        for grass in self.grass_tufts:
            self.draw_grass_tuft(grass, current_time)

        # Draw pond ripples
        for ripple in self.pond_ripples:
            self.draw_pond_ripple(ripple)

        # Draw flowers (foreground)
        for flower in self.flowers:
            self.draw_flower(flower, current_time)

    def draw_sun_rays(self):
        """Draw animated sun rays"""
        # Draw sun
        pygame.draw.circle(self.screen, (255, 253, 184), (self.sun_x, self.sun_y), 40)
        pygame.draw.circle(self.screen, (255, 255, 224), (self.sun_x, self.sun_y), 35)

        # Draw rotating rays
        ray_count = 12
        for i in range(ray_count):
            angle = self.sun_ray_angle + (i * math.pi * 2 / ray_count)
            length = 60 + math.sin(angle * 3) * 20
            end_x = self.sun_x + math.cos(angle) * length
            end_y = self.sun_y + math.sin(angle) * length

            # Create gradient effect for rays
            for j in range(3):
                alpha = 100 - j * 30
                width = 3 - j
                color = (255, 253, 184)
                start_radius = 40 + j * 5
                start_x = self.sun_x + math.cos(angle) * start_radius
                start_y = self.sun_y + math.sin(angle) * start_radius

                pygame.draw.line(self.screen, color, (start_x, start_y), (end_x, end_y), width)

    def draw_cloud(self, cloud):
        """Draw a fluffy cloud"""
        x, y = int(cloud["x"]), int(cloud["y"])
        size = cloud["size"]

        # Create cloud with multiple circles
        cloud_surface = pygame.Surface((int(150 * size), int(80 * size)), pygame.SRCALPHA)

        # Cloud puffs
        puffs = [(30, 40, 35), (60, 35, 40), (90, 40, 35), (45, 50, 30), (75, 50, 30), (50, 30, 25), (70, 30, 25)]

        for px, py, radius in puffs:
            color = (255, 255, 255, cloud["opacity"])
            pygame.draw.circle(cloud_surface, color, (int(px * size), int(py * size)), int(radius * size))

        self.screen.blit(cloud_surface, (x, y))

    def draw_grass_tuft(self, grass, current_time):
        """Draw an animated grass tuft with pixel art style"""
        # Calculate sway based on time and unique phase
        sway = math.sin(current_time * grass["sway_speed"] + grass["sway_phase"]) * 4

        x = grass["x"]
        y = grass["y"]
        color = grass["color_variation"]
        size = grass["size"]

        if grass["type"] == "tall":
            # Tall grass with 3-5 blades in a cluster
            blade_count = 4
            for i in range(blade_count):
                offset_x = (i - blade_count // 2) * 3
                height = int(20 * size - abs(i - blade_count // 2) * 3)

                # Draw each blade as a triangle/diamond shape
                blade_sway = sway * (1 - abs(i - blade_count // 2) * 0.2)

                # Base of blade (wider)
                pygame.draw.polygon(
                    self.screen,
                    color,
                    [
                        (x + offset_x - 2, y),
                        (x + offset_x + 2, y),
                        (x + offset_x + int(blade_sway), y - height),
                    ],
                )

                # Highlight on one side for depth
                if i < blade_count // 2:
                    lighter = tuple(min(255, c + 20) for c in color)
                    pygame.draw.line(
                        self.screen, lighter, (x + offset_x - 1, y), (x + offset_x + int(blade_sway) - 1, y - height), 1
                    )

        elif grass["type"] == "medium":
            # Medium grass with wider blades
            for i in range(3):
                offset_x = (i - 1) * 5
                height = int(12 * size)
                blade_sway = sway * (1 - abs(i - 1) * 0.3)

                # Draw as filled triangular shapes
                points = [
                    (x + offset_x - 3, y),
                    (x + offset_x + 3, y),
                    (x + offset_x + int(blade_sway) + 1, y - height + 2),
                    (x + offset_x + int(blade_sway), y - height),
                ]
                pygame.draw.polygon(self.screen, color, points)

        else:  # bushy
            # Bushy grass - circular cluster of short blades
            for angle in range(0, 180, 30):
                rad = math.radians(angle)
                end_x = x + math.cos(rad) * 8 * size
                end_y = y - abs(math.sin(rad)) * 10 * size

                # Add sway to endpoints
                end_x += sway * math.sin(rad)

                # Draw thick triangular blade
                pygame.draw.polygon(self.screen, color, [(x - 1, y), (x + 1, y), (int(end_x), int(end_y))])

                # Add some color variation within the tuft
                if angle % 60 == 0:
                    darker = tuple(max(0, c - 10) for c in color)
                    pygame.draw.line(self.screen, darker, (x, y), (int(end_x), int(end_y)), 1)

    def draw_pond_ripple(self, ripple):
        """Draw an animated water ripple"""
        if ripple["opacity"] > 0:
            # Check if ripple is within reasonable bounds of pond
            # Calculate distance from pond center
            dx = ripple["x"] - self.pond_center_x
            dy = ripple["y"] - self.pond_center_y

            # Simple ellipse bounds check (with some margin)
            ellipse_check = (dx * dx) / ((self.pond_width / 2) ** 2) + (dy * dy) / ((self.pond_height / 2) ** 2)

            if ellipse_check < 1.5:  # 1.5 allows slight overlap but prevents far escapes
                # Calculate ellipse dimensions based on pond aspect ratio
                # The pond is wider than it is tall, so maintain that ratio
                ellipse_width = int(ripple["radius"] * 2)
                ellipse_height = int(ripple["radius"] * 1.4)  # Make height smaller to match pond shape

                # Create a surface for the ripple with transparency
                ripple_surface = pygame.Surface((ellipse_width + 4, ellipse_height + 4), pygame.SRCALPHA)

                # Draw ripple ellipse with fading opacity
                color = (100, 180, 220, int(ripple["opacity"]))

                # Draw the ripple ring (not filled) as an ellipse
                if ripple["radius"] > 2:
                    rect = pygame.Rect(2, 2, ellipse_width, ellipse_height)
                    pygame.draw.ellipse(ripple_surface, color, rect, 2)

                    # Add inner highlight for water effect
                    highlight_color = (200, 220, 240, int(ripple["opacity"] * 0.5))
                    inner_rect = pygame.Rect(3, 3, ellipse_width - 2, ellipse_height - 2)
                    pygame.draw.ellipse(ripple_surface, highlight_color, inner_rect, 1)

                self.screen.blit(ripple_surface, (ripple["x"] - ellipse_width // 2 - 2, ripple["y"] - ellipse_height // 2 - 2))

    def draw_bird(self, bird, current_time):
        """Draw an animated bird"""
        x, y = int(bird["x"]), int(bird["y"])
        size = bird["size"]

        # Wing flap animation
        wing_angle = math.sin(bird["wing_phase"]) * 30

        # Body
        body_color = (80, 80, 80)
        pygame.draw.ellipse(self.screen, body_color, (x - int(8 * size), y - int(4 * size), int(16 * size), int(8 * size)))

        # Wings
        wing_length = int(15 * size)
        left_wing_end = (x - wing_length, y + int(wing_angle * 0.5))
        right_wing_end = (x + wing_length, y + int(wing_angle * 0.5))

        pygame.draw.line(self.screen, body_color, (x, y), left_wing_end, int(3 * size))
        pygame.draw.line(self.screen, body_color, (x, y), right_wing_end, int(3 * size))

        # Beak
        if bird["direction"] > 0:
            pygame.draw.polygon(
                self.screen,
                (255, 165, 0),
                [(x + int(8 * size), y), (x + int(12 * size), y), (x + int(8 * size), y + int(2 * size))],
            )
        else:
            pygame.draw.polygon(
                self.screen,
                (255, 165, 0),
                [(x - int(8 * size), y), (x - int(12 * size), y), (x - int(8 * size), y + int(2 * size))],
            )

    def draw_particle(self, particle):
        """Draw a floating particle (pollen/dandelion seed)"""
        x, y = int(particle["x"]), int(particle["y"])

        # Create semi-transparent surface
        size = int(particle["size"] * 3)
        particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # Draw dandelion seed shape
        center = (size, size)
        color = (255, 255, 255, particle["opacity"])

        # Draw radiating lines from center
        for i in range(8):
            angle = particle["rotation"] + (i * math.pi / 4)
            end_x = center[0] + math.cos(angle) * size
            end_y = center[1] + math.sin(angle) * size
            pygame.draw.line(particle_surface, color, center, (end_x, end_y), 1)

        # Center dot
        pygame.draw.circle(particle_surface, color, center, 2)

        self.screen.blit(particle_surface, (x - size, y - size))

    def draw_flower(self, flower, current_time):
        """Draw an animated swaying flower"""
        # Calculate sway
        sway = math.sin(current_time * flower["sway_speed"] + flower["sway_phase"]) * 5

        # Stem
        stem_top = (flower["x"] + int(sway), flower["y"] - flower["height"])
        pygame.draw.line(self.screen, (34, 139, 34), (flower["x"], flower["y"]), stem_top, 3)

        # Leaves on stem
        leaf_y = flower["y"] - flower["height"] // 2
        pygame.draw.ellipse(self.screen, (46, 125, 50), (flower["x"] - 8, leaf_y - 3, 16, 6))

        # Flower petals
        for i in range(flower["petal_count"]):
            angle = (i * math.pi * 2 / flower["petal_count"]) + sway * 0.1
            petal_x = stem_top[0] + math.cos(angle) * flower["size"]
            petal_y = stem_top[1] + math.sin(angle) * flower["size"]
            pygame.draw.circle(self.screen, flower["color"], (int(petal_x), int(petal_y)), flower["size"] // 2)

        # Flower center
        pygame.draw.circle(self.screen, (255, 215, 0), stem_top, flower["size"] // 3)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle mouse clicks for buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()

                # Check continue button
                if self.capybara_manager.round_complete and self.continue_button:
                    if self.continue_button.rect.collidepoint(mouse_pos):
                        self.start_next_round()
                        return None

                # Check retry and menu buttons
                if self.game_over:
                    if self.retry_button and self.retry_button.rect.collidepoint(mouse_pos):
                        self.reset_game()
                        return None
                    if self.menu_button and self.menu_button.rect.collidepoint(mouse_pos):
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
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None

    def start_next_round(self) -> None:
        """Start the next round"""
        self.capybara_manager.start_next_round()
        self.shots_remaining = 5
        if hasattr(self, "_round_completion_processed"):
            delattr(self, "_round_completion_processed")
        if hasattr(self, "_game_over_processed"):
            delattr(self, "_game_over_processed")
        self.hit_markers.clear()
        # Reset continue button for next round
        self.continue_button = None

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
        self.update_scenery(dt)

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
        if self.capybara_manager.round_complete:
            if self.continue_button and self.shoot_detected:
                if self._check_button_hit(self.continue_button):
                    self.shoot_detected = False
                    self.start_next_round()
            return None

        if self.game_over:
            if self.shoot_detected:
                if self.retry_button and self._check_button_hit(self.retry_button):
                    self.shoot_detected = False
                    self.reset_game()
                elif self.menu_button and self._check_button_hit(self.menu_button):
                    self.shoot_detected = False
                    return GAME_STATE_MENU
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

    def _check_button_hit(self, button: Button) -> bool:
        """Check if crosshair is over button and shooting"""
        if self.crosshair_pos and button and button.rect.collidepoint(self.crosshair_pos):
            # Play shoot sound
            self.sound_manager.play("shoot")
            return True
        return False

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
        self.screen.blit(self.background, (0, 0))

        # Draw animated scenery (behind capybaras)
        self.draw_scenery()

        # Draw capybaras (sorted by Y position for depth layering)
        self.capybara_manager.draw(self.screen)

        self.pond_buddy.draw(self.screen)

        if self.paused:
            self._draw_pause_screen()
            return

        if self.game_over or self.capybara_manager.game_over:
            if not self.game_over and self.capybara_manager.game_over:
                if not hasattr(self, "_game_over_processed"):
                    self._game_over_processed = True
                    self.game_over = True
                    self.pond_buddy.set_mood("disappointed", 5.0, 2)

            self._draw_game_over_screen()
            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            self._draw_camera_feed()
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

            self._draw_round_complete_screen()
            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            self._draw_camera_feed()
            return

        # Draw crosshair
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if self.shoot_pos and current_time - self.shoot_animation_time < self.shoot_animation_duration:
            self._draw_shoot_animation(self.shoot_pos)

        # Draw UI
        self._draw_ui()

        # Draw camera feed
        self._draw_camera_feed()

        # Draw debug overlay if enabled
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

    def _draw_shoot_animation(self, pos: tuple) -> None:
        """Draw shooting animation"""
        current_time = pygame.time.get_ticks()
        time_since_shoot = current_time - self.shoot_animation_time
        animation_progress = time_since_shoot / self.shoot_animation_duration

        if animation_progress < 1.0:
            # Bullet impact effect
            for i in range(3):
                radius = int((20 + i * 15) * animation_progress)
                alpha = int(255 * (1 - animation_progress) / (i + 1))

                if alpha > 0:
                    impact_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    color = YELLOW if i == 0 else WHITE
                    pygame.draw.circle(impact_surface, (*color, alpha), (radius, radius), radius, max(1, 3 - i))
                    self.screen.blit(impact_surface, (pos[0] - radius, pos[1] - radius))

    def _draw_ui(self) -> None:
        """Draw game UI elements"""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Round
        round_text = self.font.render(f"Round: {self.capybara_manager.round_number}", True, WHITE)
        self.screen.blit(round_text, (10, 50))

        # Shots remaining
        shot_text = self.font.render(
            f"Shots: {self.shots_remaining}", True, WHITE if self.shots_remaining > 0 else (255, 0, 0)
        )
        self.screen.blit(shot_text, (10, 90))

        # Hit/Pass meter
        meter_x = SCREEN_WIDTH // 2 - 150
        meter_y = SCREEN_HEIGHT - 80

        # Draw hit markers
        for i in range(self.capybara_manager.capybaras_per_round):
            x = meter_x + i * 30
            if i < len(self.hit_markers):
                color = GREEN if self.hit_markers[i] else (255, 0, 0)
            else:
                color = WHITE
            pygame.draw.rect(self.screen, color, (x, meter_y, 25, 25))
            pygame.draw.rect(self.screen, BLACK, (x, meter_y, 25, 25), 2)

        # Draw pass line
        pass_line_x = meter_x + (self.capybara_manager.required_hits - 1) * 30 + 25
        pygame.draw.line(self.screen, YELLOW, (pass_line_x, meter_y - 5), (pass_line_x, meter_y + 30), 3)

        # Required hits text
        req_text = self.small_font.render(
            f"Need {self.capybara_manager.required_hits}/{self.capybara_manager.capybaras_per_round}", True, WHITE
        )
        req_rect = req_text.get_rect(center=(SCREEN_WIDTH // 2, meter_y - 20))
        self.screen.blit(req_text, req_rect)

        # FPS counter
        fps_text = self.small_font.render(f"FPS: {self.current_fps}", True, GRAY)
        fps_rect = fps_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.screen.blit(fps_text, fps_rect)

        # Controls hint (like in Doomsday)
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Reset | Shoot BALLOONS, not capybaras!", True, GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        self.screen.blit(controls_text, controls_rect)

        # Show punishment message if capybara was shot
        current_time = pygame.time.get_ticks()
        if self.capybara_shot_message_time > 0 and current_time - self.capybara_shot_message_time < 2000:
            warning_text = self.big_font.render("NO! Save the capybaras!", True, (255, 0, 0))
            warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

            # Draw semi-transparent background for message
            msg_bg = pygame.Surface((warning_rect.width + 40, warning_rect.height + 20))
            msg_bg.set_alpha(200)
            msg_bg.fill(BLACK)
            self.screen.blit(msg_bg, (warning_rect.x - 20, warning_rect.y - 10))

            self.screen.blit(warning_text, warning_rect)

            penalty_text = self.font.render(f"-{200 * self.capybara_manager.round_number} points!", True, (255, 100, 100))
            penalty_rect = penalty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(penalty_text, penalty_rect)

    def _draw_camera_feed(self) -> None:
        """Draw camera feed in corner"""
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

    def _draw_pause_screen(self) -> None:
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.big_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(pause_text, pause_rect)

        # Draw console if active
        if self.console_active:
            # Console background
            console_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 20, 400, 40)
            pygame.draw.rect(self.screen, (40, 40, 40), console_rect)
            pygame.draw.rect(self.screen, WHITE, console_rect, 2)

            # Console text
            console_text = self.font.render(self.console_input, True, WHITE)
            self.screen.blit(console_text, (console_rect.x + 10, console_rect.y + 10))

            # Console hint
            hint_text = self.small_font.render(
                "Commands: /round #, /score #, /perfect, /miss | ESC to cancel", True, (200, 200, 200)
            )
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, console_rect.bottom + 20))
            self.screen.blit(hint_text, hint_rect)
        else:
            instructions = [
                "Press P or SPACE to resume",
                "Press / to open debug console",
                "Press ESC to return to menu",
                "Press R to reset game",
            ]

            for i, instruction in enumerate(instructions):
                text = self.font.render(instruction, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
                self.screen.blit(text, text_rect)

        # Show console message if recent
        if self.console_message and time.time() - self.console_message_time < 3:
            msg_text = self.font.render(self.console_message, True, GREEN)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
            self.screen.blit(msg_text, msg_rect)

    def _draw_game_over_screen(self):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(80)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = self.huge_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)

        # Stats
        stats = [
            f"Final Score: {self.score}",
            f"Rounds Completed: {self.capybara_manager.round_number - 1}",
            f"Capybaras Hit: {self.capybara_manager.capybaras_hit}/{self.capybara_manager.capybaras_per_round}",
        ]

        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)

        # Create shootable buttons
        button_width = 150
        button_height = 50
        button_y = SCREEN_HEIGHT // 2 + 180

        # Retry button
        if not self.retry_button:
            self.retry_button = Button(
                SCREEN_WIDTH // 2 - button_width - 20, button_y, button_width, button_height, "RETRY", self.font
            )
        self.retry_button.draw(self.screen)

        # Menu button
        if not self.menu_button:
            self.menu_button = Button(SCREEN_WIDTH // 2 + 20, button_y, button_width, button_height, "MENU", self.font)
        self.menu_button.draw(self.screen)

        # Highlight buttons if aimed at
        if self.crosshair_pos:
            if self.retry_button.rect.collidepoint(self.crosshair_pos):
                pygame.draw.rect(self.screen, UI_ACCENT, self.retry_button.rect, 3)
            if self.menu_button.rect.collidepoint(self.crosshair_pos):
                pygame.draw.rect(self.screen, UI_ACCENT, self.menu_button.rect, 3)

        # Instructions
        instruction_text = self.small_font.render("Shoot a button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, button_y + 70))
        self.screen.blit(instruction_text, instruction_rect)

    def _draw_round_complete_screen(self):
        """Draw round complete screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(50)  # Much more transparent so you can see the game
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Check for perfect round
        if self.capybara_manager.capybaras_hit == self.capybara_manager.capybaras_per_round:
            complete_text = self.big_font.render(f"PERFECT!! +{1000 * self.capybara_manager.round_number}", True, YELLOW)
        else:
            complete_text = self.big_font.render(f"ROUND {self.capybara_manager.round_number} COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(complete_text, complete_rect)

        # Stats
        stats_text = self.font.render(
            f"Hit: {self.capybara_manager.capybaras_hit}/{self.capybara_manager.capybaras_per_round} | Score: {self.score}",
            True,
            WHITE,
        )
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(stats_text, stats_rect)

        # Create shootable continue button
        button_width = 200
        button_height = 60
        button_y = SCREEN_HEIGHT // 2 + 80

        if not self.continue_button:
            self.continue_button = Button(
                SCREEN_WIDTH // 2 - button_width // 2, button_y, button_width, button_height, "CONTINUE", self.font
            )
        self.continue_button.draw(self.screen)

        # Highlight button if aimed at
        if self.crosshair_pos and self.continue_button.rect.collidepoint(self.crosshair_pos):
            pygame.draw.rect(self.screen, UI_ACCENT, self.continue_button.rect, 3)

        # Instructions
        instruction_text = self.small_font.render("Shoot the button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, button_y + 80))
        self.screen.blit(instruction_text, instruction_rect)

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
