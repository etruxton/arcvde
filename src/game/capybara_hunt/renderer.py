# Standard library imports
import math
import random
import time
from typing import List, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from utils.constants import (
    BLACK,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    GRAY,
    GREEN,
    LIGHT_GRAY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    WHITE,
    YELLOW,
)


class CapybaraHuntRenderer:
    """Handles all rendering and drawing for Capybara Hunt game mode"""

    def __init__(self):
        # Background surface
        self.background: Optional[pygame.Surface] = None

        # Animated scenery elements
        self.clouds = []
        self.birds = []
        self.particles = []
        self.flowers = []
        self.grass_tufts = []
        self.pond_ripples = []

        # Scenery state
        self.pond_center_x = 100
        self.pond_center_y = SCREEN_HEIGHT - 40
        self.pond_width = 280
        self.pond_height = 140
        self.sun_ray_angle = 0
        self.sun_x = SCREEN_WIDTH - 150
        self.sun_y = 100
        self.ripple_spawn_timer = 0

        # Initialize everything
        self.create_background()
        self.init_scenery()

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

        # Add darker border like the mountains
        darker_color = tuple(max(0, c - 20) for c in color)
        pygame.draw.lines(surface, darker_color, False, points[:-2], 2)  # Exclude bottom corners

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

            # Create flower if we found a valid position
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

    def draw_scenery(self, screen: pygame.Surface):
        """Draw animated scenery elements"""
        current_time = pygame.time.get_ticks() / 1000.0

        self.draw_sun_rays(screen)

        # Draw clouds (behind everything)
        for cloud in self.clouds:
            self.draw_cloud(screen, cloud)

        # Draw birds
        for bird in self.birds:
            self.draw_bird(screen, bird, current_time)

        # Draw floating particles
        for particle in self.particles:
            self.draw_particle(screen, particle)

        # Draw animated grass tufts
        for grass in self.grass_tufts:
            self.draw_grass_tuft(screen, grass, current_time)

        # Draw pond ripples
        for ripple in self.pond_ripples:
            self.draw_pond_ripple(screen, ripple)

        # Draw flowers (foreground)
        for flower in self.flowers:
            self.draw_flower(screen, flower, current_time)

    def draw_sun_rays(self, screen: pygame.Surface):
        """Draw animated sun rays"""
        # Draw sun
        pygame.draw.circle(screen, (255, 253, 184), (self.sun_x, self.sun_y), 40)
        pygame.draw.circle(screen, (255, 255, 224), (self.sun_x, self.sun_y), 35)

        # Draw rotating rays
        ray_count = 12
        for i in range(ray_count):
            angle = self.sun_ray_angle + (i * math.pi * 2 / ray_count)
            length = 60 + math.sin(angle * 3) * 20
            end_x = self.sun_x + math.cos(angle) * length
            end_y = self.sun_y + math.sin(angle) * length

            # Create gradient effect for rays
            for j in range(3):
                width = 3 - j
                color = (255, 253, 184)
                start_radius = 40 + j * 5
                start_x = self.sun_x + math.cos(angle) * start_radius
                start_y = self.sun_y + math.sin(angle) * start_radius

                pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), width)

    def draw_cloud(self, screen: pygame.Surface, cloud):
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

        screen.blit(cloud_surface, (x, y))

    def draw_grass_tuft(self, screen: pygame.Surface, grass, current_time):
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
                    screen,
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
                        screen, lighter, (x + offset_x - 1, y), (x + offset_x + int(blade_sway) - 1, y - height), 1
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
                pygame.draw.polygon(screen, color, points)

        else:  # bushy
            # Bushy grass - circular cluster of short blades
            for angle in range(0, 180, 30):
                rad = math.radians(angle)
                end_x = x + math.cos(rad) * 8 * size
                end_y = y - abs(math.sin(rad)) * 10 * size

                # Add sway to endpoints
                end_x += sway * math.sin(rad)

                # Draw thick triangular blade
                pygame.draw.polygon(screen, color, [(x - 1, y), (x + 1, y), (int(end_x), int(end_y))])

                # Add some color variation within the tuft
                if angle % 60 == 0:
                    darker = tuple(max(0, c - 10) for c in color)
                    pygame.draw.line(screen, darker, (x, y), (int(end_x), int(end_y)), 1)

    def draw_pond_ripple(self, screen: pygame.Surface, ripple):
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

                screen.blit(ripple_surface, (ripple["x"] - ellipse_width // 2 - 2, ripple["y"] - ellipse_height // 2 - 2))

    def draw_bird(self, screen: pygame.Surface, bird, current_time):
        """Draw an animated bird"""
        x, y = int(bird["x"]), int(bird["y"])
        size = bird["size"]

        # Wing flap animation
        wing_angle = math.sin(bird["wing_phase"]) * 30

        # Body
        body_color = (80, 80, 80)
        pygame.draw.ellipse(screen, body_color, (x - int(8 * size), y - int(4 * size), int(16 * size), int(8 * size)))

        # Wings
        wing_length = int(15 * size)
        left_wing_end = (x - wing_length, y + int(wing_angle * 0.5))
        right_wing_end = (x + wing_length, y + int(wing_angle * 0.5))

        pygame.draw.line(screen, body_color, (x, y), left_wing_end, int(3 * size))
        pygame.draw.line(screen, body_color, (x, y), right_wing_end, int(3 * size))

        # Beak
        if bird["direction"] > 0:
            pygame.draw.polygon(
                screen,
                (255, 165, 0),
                [(x + int(8 * size), y), (x + int(12 * size), y), (x + int(8 * size), y + int(2 * size))],
            )
        else:
            pygame.draw.polygon(
                screen,
                (255, 165, 0),
                [(x - int(8 * size), y), (x - int(12 * size), y), (x - int(8 * size), y + int(2 * size))],
            )

    def draw_particle(self, screen: pygame.Surface, particle):
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

        screen.blit(particle_surface, (x - size, y - size))

    def draw_flower(self, screen: pygame.Surface, flower, current_time):
        """Draw an animated swaying flower"""
        # Calculate sway
        sway = math.sin(current_time * flower["sway_speed"] + flower["sway_phase"]) * 5

        # Stem
        stem_top = (flower["x"] + int(sway), flower["y"] - flower["height"])
        pygame.draw.line(screen, (34, 139, 34), (flower["x"], flower["y"]), stem_top, 3)

        # Leaves on stem
        leaf_y = flower["y"] - flower["height"] // 2
        pygame.draw.ellipse(screen, (46, 125, 50), (flower["x"] - 8, leaf_y - 3, 16, 6))

        # Flower petals
        for i in range(flower["petal_count"]):
            angle = (i * math.pi * 2 / flower["petal_count"]) + sway * 0.1
            petal_x = stem_top[0] + math.cos(angle) * flower["size"]
            petal_y = stem_top[1] + math.sin(angle) * flower["size"]
            pygame.draw.circle(screen, flower["color"], (int(petal_x), int(petal_y)), flower["size"] // 2)

        # Flower center
        pygame.draw.circle(screen, (255, 215, 0), stem_top, flower["size"] // 3)

    def draw_crosshair(self, screen: pygame.Surface, pos: Tuple[int, int], color: Tuple[int, int, int]):
        """Draw crosshair at given position - matches base class implementation"""
        x, y = pos
        size = 15
        thickness = 2

        pygame.draw.circle(screen, color, pos, size, thickness)

        pygame.draw.line(screen, color, (x - size - 8, y), (x + size + 8, y), thickness)
        pygame.draw.line(screen, color, (x, y - size - 8), (x, y + size + 8), thickness)

    def draw_shoot_animation(self, screen: pygame.Surface, pos: Tuple[int, int], animation_time: int, animation_duration: int):
        """Draw shooting animation"""
        current_time = pygame.time.get_ticks()
        time_since_shoot = current_time - animation_time
        animation_progress = time_since_shoot / animation_duration

        if animation_progress < 1.0:
            # Bullet impact effect
            for i in range(3):
                radius = int((20 + i * 15) * animation_progress)
                alpha = int(255 * (1 - animation_progress) / (i + 1))

                if alpha > 0:
                    impact_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    color = YELLOW if i == 0 else WHITE
                    pygame.draw.circle(impact_surface, (*color, alpha), (radius, radius), radius, max(1, 3 - i))
                    screen.blit(impact_surface, (pos[0] - radius, pos[1] - radius))

    def draw_hud(
        self,
        screen: pygame.Surface,
        score: int,
        shots_remaining: int,
        round_number: int,
        hit_markers: List[bool],
        capybaras_per_round: int,
        required_hits: int,
        current_fps: int,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        """Draw game HUD elements"""
        # Score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Round
        round_text = font.render(f"Round: {round_number}", True, WHITE)
        screen.blit(round_text, (10, 50))

        # Shots remaining
        shot_text = font.render(f"Shots: {shots_remaining}", True, WHITE if shots_remaining > 0 else (255, 0, 0))
        screen.blit(shot_text, (10, 90))

        # Hit/Pass meter
        meter_x = SCREEN_WIDTH // 2 - 150
        meter_y = SCREEN_HEIGHT - 80

        # Draw hit markers
        for i in range(capybaras_per_round):
            x = meter_x + i * 30
            if i < len(hit_markers):
                color = GREEN if hit_markers[i] else (255, 0, 0)
            else:
                color = WHITE
            pygame.draw.rect(screen, color, (x, meter_y, 25, 25))
            pygame.draw.rect(screen, BLACK, (x, meter_y, 25, 25), 2)

        # Draw pass line
        pass_line_x = meter_x + (required_hits - 1) * 30 + 25
        pygame.draw.line(screen, YELLOW, (pass_line_x, meter_y - 5), (pass_line_x, meter_y + 30), 3)

        # Required hits text
        req_text = small_font.render(f"Need {required_hits}/{capybaras_per_round}", True, WHITE)
        req_rect = req_text.get_rect(center=(SCREEN_WIDTH // 2, meter_y - 20))
        screen.blit(req_text, req_rect)

        # FPS counter
        fps_text = small_font.render(f"FPS: {current_fps}", True, GRAY)
        fps_rect = fps_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        screen.blit(fps_text, fps_rect)

        # Controls hint
        controls_text = small_font.render("ESC: Menu | P: Pause | R: Reset | D: Debug", True, LIGHT_GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        screen.blit(controls_text, controls_rect)

    def draw_punishment_message(
        self, screen: pygame.Surface, message_time: int, round_number: int, big_font: pygame.font.Font, font: pygame.font.Font
    ):
        """Draw punishment message when capybara is shot"""
        current_time = pygame.time.get_ticks()
        if message_time > 0 and current_time - message_time < 2000:
            warning_text = big_font.render("NO! Save the capybaras!", True, (255, 0, 0))
            warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

            # Draw semi-transparent background for message
            msg_bg = pygame.Surface((warning_rect.width + 40, warning_rect.height + 20))
            msg_bg.set_alpha(200)
            msg_bg.fill(BLACK)
            screen.blit(msg_bg, (warning_rect.x - 20, warning_rect.y - 10))

            screen.blit(warning_text, warning_rect)

            penalty_text = font.render(f"-{200 * round_number} points!", True, (255, 100, 100))
            penalty_rect = penalty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            screen.blit(penalty_text, penalty_rect)

    def draw_camera_feed(self, screen: pygame.Surface, camera_manager, hand_tracker):
        """Draw camera feed in corner"""
        # This uses the base screen method for drawing camera with tracking
        # We'll need to pass this through from the main screen
        pass  # Implementation will be handled by main screen

    def draw_pause_screen(
        self,
        screen: pygame.Surface,
        console_active: bool,
        console_input: str,
        console_message: str,
        console_message_time: float,
        big_font: pygame.font.Font,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        """Draw pause overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        pause_text = big_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(pause_text, pause_rect)

        # Draw console if active
        if console_active:
            # Console background
            console_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 20, 400, 40)
            pygame.draw.rect(screen, (40, 40, 40), console_rect)
            pygame.draw.rect(screen, WHITE, console_rect, 2)

            # Console text
            console_text = font.render(console_input, True, WHITE)
            screen.blit(console_text, (console_rect.x + 10, console_rect.y + 10))

            # Console hint
            hint_text = small_font.render("Commands: /round # | ESC to cancel", True, (200, 200, 200))
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, console_rect.bottom + 20))
            screen.blit(hint_text, hint_rect)
        else:
            instructions = [
                "Press P or SPACE to resume",
                "Press / to open debug console",
                "Press ESC to return to menu",
                "Press R to reset game",
            ]

            for i, instruction in enumerate(instructions):
                text = font.render(instruction, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
                screen.blit(text, text_rect)

        # Show console message if recent
        if console_message and time.time() - console_message_time < 3:
            msg_text = font.render(console_message, True, GREEN)
            msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
            screen.blit(msg_text, msg_rect)

    def draw_game_over_screen(
        self,
        screen: pygame.Surface,
        score: int,
        round_number: int,
        capybaras_hit: int,
        capybaras_per_round: int,
        huge_font: pygame.font.Font,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        """Draw game over screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(80)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = huge_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(game_over_text, game_over_rect)

        # Stats
        stats = [
            f"Final Score: {score}",
            f"Rounds Completed: {round_number - 1}",
            f"Capybaras Hit: {capybaras_hit}/{capybaras_per_round}",
        ]

        for i, stat in enumerate(stats):
            text = font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            screen.blit(text, text_rect)

        # Instructions
        instruction_text = small_font.render("Shoot a button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 250))
        screen.blit(instruction_text, instruction_rect)

    def draw_round_complete_screen(
        self,
        screen: pygame.Surface,
        score: int,
        round_number: int,
        capybaras_hit: int,
        capybaras_per_round: int,
        big_font: pygame.font.Font,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        """Draw round complete screen"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(50)  # Much more transparent so you can see the game
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Check for perfect round
        if capybaras_hit == capybaras_per_round:
            complete_text = big_font.render(f"PERFECT!! +{1000 * round_number}", True, YELLOW)
        else:
            complete_text = big_font.render(f"ROUND {round_number} COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(complete_text, complete_rect)

        # Stats
        stats_text = font.render(
            f"Hit: {capybaras_hit}/{capybaras_per_round} | Score: {score}",
            True,
            WHITE,
        )
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(stats_text, stats_rect)

        # Instructions
        instruction_text = small_font.render("Shoot the button to continue", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 160))
        screen.blit(instruction_text, instruction_rect)

    def draw_pause_screen(
        self,
        surface: pygame.Surface,
        console_active: bool,
        console_input: str,
        console_message: str,
        console_message_time: float,
        big_font: pygame.font.Font,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Draw pause screen overlay - same style as Doomsday"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Pause text
        pause_text = big_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        surface.blit(pause_text, pause_rect)

        # Controls
        controls = [
            "P/SPACE - Resume",
            "R - Restart",
            "ESC - Menu",
            "/ - Console (when paused)",
            "D - Debug Mode",
        ]

        y_start = SCREEN_HEIGHT // 2 - 50
        for i, control in enumerate(controls):
            control_text = font.render(control, True, UI_ACCENT)
            control_rect = control_text.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 40))
            surface.blit(control_text, control_rect)

        # Debug console
        if console_active:
            self._draw_debug_console(surface, console_input, console_message, console_message_time, font, small_font)

    def _draw_debug_console(
        self,
        surface: pygame.Surface,
        console_input: str,
        console_message: str,
        console_message_time: float,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Draw debug console interface"""
        # Standard library imports
        import time

        # Console background
        console_y = SCREEN_HEIGHT - 200
        console_bg = pygame.Surface((SCREEN_WIDTH - 40, 150))
        console_bg.set_alpha(200)
        console_bg.fill((20, 20, 20))
        surface.blit(console_bg, (20, console_y))

        # Console border
        pygame.draw.rect(surface, UI_ACCENT, (20, console_y, SCREEN_WIDTH - 40, 150), 2)

        # Console title
        title_text = font.render("DEBUG CONSOLE", True, UI_ACCENT)
        surface.blit(title_text, (30, console_y + 10))

        # Input line
        input_text = font.render(f"> {console_input}", True, WHITE)
        surface.blit(input_text, (30, console_y + 50))

        # Blinking cursor
        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
            cursor_x = 30 + font.size(f"> {console_input}")[0]
            pygame.draw.line(surface, WHITE, (cursor_x, console_y + 50), (cursor_x, console_y + 70), 2)

        # Console message with fade
        if console_message and time.time() - console_message_time < 3.0:
            fade_alpha = max(0, 255 - int((time.time() - console_message_time) * 85))
            message_surface = small_font.render(console_message, True, (0, 255, 0))
            message_surface.set_alpha(fade_alpha)
            surface.blit(message_surface, (30, console_y + 90))

        # Help text
        help_text = small_font.render("Available commands: /round #, /score #", True, (128, 128, 128))
        surface.blit(help_text, (30, console_y + 120))
