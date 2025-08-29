"""
Capybara system for the Capybara Hunt game mode
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
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class FlyingCapybara:
    """A flying capybara target in the game"""

    # Class variables to store loaded sprites (shared by all instances)
    sprites_loaded = False
    sprite_frames = []
    laydown_sprite_frames = []  # Sprites for laying down animation
    sleeping_sprite_frames = []  # Sprites for sleeping animation (plays after laying down)
    sit_sprite_frames = []  # Sprites for sitting animation
    chilling_sprite_frames = []  # Sprites for chilling animation (plays after sitting down)
    frontkick_sprite_frames = []  # Sprites for front kick animation
    standing_sprite_frames = []  # Sprites for standing animation
    sprite_size = (80, 80)  # Keep sprites square since originals are square

    def __init__(self, start_x: float, start_y: float, direction: str, speed_multiplier: float = 1.0):
        """
        Initialize a flying capybara

        Args:
            start_x: Starting X position
            start_y: Starting Y position
            direction: Flight direction ('left', 'right', 'diagonal_left', 'diagonal_right')
            speed_multiplier: Speed multiplier for difficulty
        """
        self.x = start_x
        self.y = start_y
        self.direction = direction
        self.speed_multiplier = speed_multiplier

        # Visual properties
        self.size = 80
        self.color = (139, 90, 43)  # Brown color for capybara
        self.alive = True  # Balloon is intact
        self.hit_time = None
        self.fall_speed = 0
        self.walking = False  # Whether capybara is walking on ground
        self.standing = False  # Whether capybara is standing still
        self.grounded = False  # Whether capybara has landed on ground
        self.ground_y = 0  # Y position when grounded
        self.walk_direction = 1  # 1 for right, -1 for left
        self.walk_speed = 50  # Slower speed for walking
        self.shot_capybara = False  # True if player shot capybara instead of balloon

        # Laying down state
        self.laying_down = False
        self.laying_animation_frame = 0
        self.laying_animation_timer = 0
        self.laying_animation_speed = 0.1  # Seconds per frame
        self.laying_animation_playing = False  # True when transitioning to/from laying
        self.laying_animation_reverse = False  # True when getting up

        # Sleeping state (plays after laying down)
        self.sleeping = False
        self.sleeping_frame = 0
        self.sleeping_timer = 0
        self.sleeping_speed = 0.15  # Slightly slower for breathing effect
        self.sleeping_forward = True  # Direction of animation (0->4 or 4->0)

        # Sitting state
        self.sitting = False
        self.sit_animation_frame = 0
        self.sit_animation_timer = 0
        self.sit_animation_speed = 0.1  # Seconds per frame
        self.sit_animation_playing = False  # True when transitioning to/from sitting
        self.sit_animation_reverse = False  # True when standing up

        # Chilling state (plays after sitting down)
        self.chilling = False
        self.chilling_frame = 0
        self.chilling_timer = 0
        self.chilling_speed = 0.15  # Slightly slower for relaxed effect

        # Front kick state
        self.kicking = False
        self.kick_animation_frame = 0
        self.kick_animation_timer = 0
        self.kick_animation_speed = 0.08  # Slightly faster animation
        self.kick_loops_completed = 0
        self.kick_loops_target = 1  # Will be randomized when kicking starts

        # Standing state
        self.standing_animation_frame = 0
        self.standing_animation_timer = 0
        self.standing_animation_speed = 0.15  # Slower for idle animation

        self.time_until_action = random.uniform(2.0, 5.0)  # Time before next action

        # Balloon properties
        self.balloon_color = random.choice(
            [
                (255, 100, 100),  # Red
                (100, 255, 100),  # Green
                (100, 100, 255),  # Blue
                (255, 255, 100),  # Yellow
                (255, 100, 255),  # Magenta
                (100, 255, 255),  # Cyan
                (255, 180, 100),  # Orange
                (200, 100, 255),  # Purple
            ]
        )
        self.balloon_radius = 35
        self.string_wave = 0  # For string animation
        self.balloon_popped = False

        # Flight properties
        self.base_speed = 150  # pixels per second (reduced for better gameplay)
        self.vertical_speed = 0
        self.flight_time = 0
        self.escape_time = random.uniform(4.0, 6.0)  # More time before escaping

        # Set initial velocities based on direction
        if direction == "left":
            self.vx = -self.base_speed * speed_multiplier
            self.vy = random.uniform(-80, -120) * speed_multiplier  # Upward movement
        elif direction == "right":
            self.vx = self.base_speed * speed_multiplier
            self.vy = random.uniform(-80, -120) * speed_multiplier  # Upward movement
        elif direction == "diagonal_left":
            self.vx = -self.base_speed * 0.6 * speed_multiplier  # Slower horizontal
            self.vy = -self.base_speed * 0.8 * speed_multiplier  # More vertical
        else:  # diagonal_right
            self.vx = self.base_speed * 0.6 * speed_multiplier  # Slower horizontal
            self.vy = -self.base_speed * 0.8 * speed_multiplier  # More vertical

        # Animation
        self.float_timer = 0
        self.float_amplitude = 5  # How much the balloon bobs
        self.sprite_frame_index = 0
        self.sprite_animation_timer = 0
        self.sprite_animation_speed = 0.1  # Seconds per frame

        # Load sprites if not already loaded
        self.load_sprites()

        # Determine if sprite should be flipped based on direction
        self.flip_sprite = direction in ["right", "diagonal_right"]

    @classmethod
    def load_sprites(cls):
        """Load capybara sprite images (only once for all instances)"""
        if not cls.sprites_loaded:
            try:
                # Load running sprite frames
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/running_capybara/running-capybara-{i}.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Sprite not found: {sprite_path}")

                # Load laydown sprite frames
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/laydown_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.laydown_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Laydown sprite not found: {sprite_path}")

                # Load sleeping sprite frames (plays after laying down)
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/sleeping_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.sleeping_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Sleeping sprite not found: {sprite_path}")

                # Load sit sprite frames
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/sit_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.sit_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Sit sprite not found: {sprite_path}")

                # Load chilling sprite frames (plays after sitting down)
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/chilling_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.chilling_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Chilling sprite not found: {sprite_path}")

                # Load front kick sprite frames
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/frontkick_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.frontkick_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Front kick sprite not found: {sprite_path}")

                # Load standing sprite frames
                for i in range(5):  # 0 to 4
                    sprite_path = f"assets/standing_capybara/frame_{i}_delay-0.1s.png"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path)
                        # Scale sprite to consistent size
                        sprite = pygame.transform.scale(sprite, cls.sprite_size)
                        cls.standing_sprite_frames.append(sprite)
                    else:
                        print(f"Warning: Standing sprite not found: {sprite_path}")

                if cls.sprite_frames:
                    cls.sprites_loaded = True
                    print(
                        f"Loaded {len(cls.sprite_frames)} running, {len(cls.laydown_sprite_frames)} laydown, {len(cls.sit_sprite_frames)} sit, {len(cls.frontkick_sprite_frames)} kick, {len(cls.standing_sprite_frames)} standing sprites"
                    )
                else:
                    print("Warning: No capybara sprites loaded")
            except Exception as e:
                print(f"Error loading sprites: {e}")
                cls.sprites_loaded = False

    def update(self, dt: float) -> bool:
        """
        Update capybara position and state

        Returns:
            True if capybara should be removed (escaped or fell off screen)
        """
        self.flight_time += dt

        # Update sprite animation based on state
        if self.alive and self.sprite_frames:
            # Flying capybara - always use running animation
            self.sprite_animation_timer += dt
            if self.sprite_animation_timer > self.sprite_animation_speed:
                self.sprite_animation_timer = 0
                self.sprite_frame_index = (self.sprite_frame_index + 1) % len(self.sprite_frames)
        elif self.standing and self.__class__.standing_sprite_frames:
            # Standing animation for grounded capybaras
            self.standing_animation_timer += dt
            if self.standing_animation_timer > self.standing_animation_speed:
                self.standing_animation_timer = 0
                self.standing_animation_frame = (self.standing_animation_frame + 1) % len(
                    self.__class__.standing_sprite_frames
                )
        elif self.walking and self.sprite_frames:
            # Walking animation for grounded capybaras
            self.sprite_animation_timer += dt
            if self.sprite_animation_timer > self.sprite_animation_speed:
                self.sprite_animation_timer = 0
                self.sprite_frame_index = (self.sprite_frame_index + 1) % len(self.sprite_frames)

        # Update balloon float animation
        self.float_timer += dt
        self.string_wave = math.sin(self.float_timer * 3) * 2  # Gentle string waving

        if self.alive:
            # Balloon is intact - float with balloon
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Add bobbing motion from balloon
            self.y += math.sin(self.float_timer * 2) * self.float_amplitude * dt

            # Check if escaped off screen
            if self.flight_time > self.escape_time:
                # Start flying upward to escape
                self.vy = max(self.vy - 150 * dt, -300)

            # Check boundaries
            if self.x < -100 or self.x > SCREEN_WIDTH + 100:
                return True  # Escaped horizontally
            if self.y < -100:
                return True  # Escaped vertically

            # Keep above ground level
            if self.y > SCREEN_HEIGHT - 150:
                self.y = SCREEN_HEIGHT - 150
                self.vy = min(self.vy, 0)

        elif self.grounded:
            # Capybara is on ground - maintain Y position
            self.y = self.ground_y  # Always keep at ground level
            self.time_until_action -= dt

            # Handle laying down animation transitions
            if self.laying_animation_playing:
                self.laying_animation_timer += dt
                if self.laying_animation_timer > self.laying_animation_speed:
                    self.laying_animation_timer = 0

                    if self.laying_animation_reverse:
                        # Getting up animation (play frames in reverse)
                        if self.laying_animation_frame > 0:
                            self.laying_animation_frame -= 1
                        else:
                            # Finished getting up - choose to stand or walk
                            self.laying_animation_playing = False
                            self.laying_down = False
                            self.sleeping = False  # Stop sleeping when getting up
                            if random.random() < 0.25:  # 25% chance to stand after getting up
                                self.standing = True
                                self.walking = False
                            else:
                                self.standing = False
                                self.walking = True
                            self.time_until_action = random.uniform(2.0, 5.0)
                    else:
                        # Laying down animation
                        if self.laying_animation_frame < len(self.laydown_sprite_frames) - 1:
                            self.laying_animation_frame += 1
                        else:
                            # Finished laying down - start sleeping
                            self.laying_animation_playing = False
                            self.laying_down = True
                            self.sleeping = True
                            self.sleeping_frame = 0
                            self.sleeping_forward = True
                            self.sleeping_timer = 0
                            self.time_until_action = random.uniform(3.0, 6.0)  # Stay down longer

            # Handle sleeping animation (breathing loop)
            if self.sleeping and self.laying_down:
                self.sleeping_timer += dt
                if self.sleeping_timer > self.sleeping_speed:
                    self.sleeping_timer = 0

                    # Animation goes 0->1->2->3->4->3->2->1->0 and loops
                    if self.sleeping_forward:
                        self.sleeping_frame += 1
                        if self.sleeping_frame >= len(self.sleeping_sprite_frames) - 1:
                            self.sleeping_frame = len(self.sleeping_sprite_frames) - 1
                            self.sleeping_forward = False
                    else:
                        self.sleeping_frame -= 1
                        if self.sleeping_frame <= 0:
                            self.sleeping_frame = 0
                            self.sleeping_forward = True

            # Handle chilling animation (simple loop)
            if self.chilling and self.sitting:
                self.chilling_timer += dt
                if self.chilling_timer > self.chilling_speed:
                    self.chilling_timer = 0
                    # Simple loop: 0->1->2->3->4->0
                    self.chilling_frame = (self.chilling_frame + 1) % len(self.chilling_sprite_frames)

            # Handle kicking animation
            elif self.kicking:
                self.kick_animation_timer += dt
                if self.kick_animation_timer > self.kick_animation_speed:
                    self.kick_animation_timer = 0
                    self.kick_animation_frame += 1

                    # Check if we completed a loop
                    if self.kick_animation_frame >= len(self.frontkick_sprite_frames):
                        self.kick_animation_frame = 0
                        self.kick_loops_completed += 1

                        # Check if we've done enough loops
                        if self.kick_loops_completed >= self.kick_loops_target:
                            # Finished kicking - choose to stand or walk
                            self.kicking = False
                            self.kick_loops_completed = 0
                            if random.random() < 0.25:  # 25% chance to stand after kicking
                                self.standing = True
                                self.walking = False
                            else:
                                self.standing = False
                                self.walking = True
                            self.time_until_action = random.uniform(2.0, 5.0)

            # Handle sitting animation transitions
            elif self.sit_animation_playing:
                self.sit_animation_timer += dt
                if self.sit_animation_timer > self.sit_animation_speed:
                    self.sit_animation_timer = 0

                    if self.sit_animation_reverse:
                        # Standing up animation (play frames in reverse)
                        if self.sit_animation_frame > 0:
                            self.sit_animation_frame -= 1
                        else:
                            # Finished standing up - choose to stand or walk
                            self.sit_animation_playing = False
                            self.sitting = False
                            self.chilling = False  # Make sure chilling is stopped
                            if random.random() < 0.25:  # 25% chance to stand after sitting
                                self.standing = True
                                self.walking = False
                            else:
                                self.standing = False
                                self.walking = True
                            self.time_until_action = random.uniform(2.0, 5.0)
                    else:
                        # Sitting down animation
                        if self.sit_animation_frame < len(self.sit_sprite_frames) - 1:
                            self.sit_animation_frame += 1
                        else:
                            # Finished sitting down - start chilling
                            self.sit_animation_playing = False
                            self.sitting = True
                            self.chilling = True
                            self.chilling_frame = 0
                            self.chilling_timer = 0
                            self.time_until_action = random.uniform(2.0, 4.0)  # Sit for a moderate time

            # Decide on next action (only if not already animating)
            if (
                self.time_until_action <= 0
                and not self.laying_animation_playing
                and not self.sit_animation_playing
                and not self.kicking
            ):
                if self.laying_down:
                    # Start getting up from laying
                    self.sleeping = False  # Stop sleeping when starting to get up
                    self.laying_animation_playing = True
                    self.laying_animation_reverse = True
                    self.laying_animation_frame = len(self.laydown_sprite_frames) - 1
                elif self.sitting:
                    # Start standing up from sitting
                    self.chilling = False  # Stop chilling when starting to get up
                    self.sit_animation_playing = True
                    self.sit_animation_reverse = True
                    self.sit_animation_frame = len(self.sit_sprite_frames) - 1
                else:
                    # Decide what to do next based on current state
                    action_roll = random.random()

                    if self.standing:
                        # Standing capybara can: start walking, kick, lay down, or sit
                        if action_roll < 0.25:  # 25% chance to start walking
                            self.standing = False
                            self.walking = True
                            self.time_until_action = random.uniform(2.0, 5.0)
                        elif action_roll < 0.40:  # 15% chance to kick
                            self.standing = False  # Clear standing state
                            self.walking = False
                            self.kicking = True
                            self.kick_animation_frame = 0
                            self.kick_loops_completed = 0
                            self.kick_loops_target = 3
                        elif action_roll < 0.55:  # 15% chance to lay down
                            self.standing = False  # Clear standing state
                            self.walking = False
                            self.laying_animation_playing = True
                            self.laying_animation_reverse = False
                            self.laying_animation_frame = 0
                        elif action_roll < 0.70:  # 15% chance to sit
                            self.standing = False  # Clear standing state
                            self.walking = False
                            self.sit_animation_playing = True
                            self.sit_animation_reverse = False
                            self.sit_animation_frame = 0
                        else:
                            # Keep standing, reset timer
                            self.time_until_action = random.uniform(2.0, 5.0)

                    elif self.walking:
                        # Walking capybara can: stand, kick, lay down, or sit
                        if action_roll < 0.20:  # 20% chance to stand
                            self.walking = False
                            self.standing = True
                            self.time_until_action = random.uniform(2.0, 5.0)
                        elif action_roll < 0.35:  # 15% chance to kick
                            self.walking = False  # Clear walking state
                            self.standing = False
                            self.kicking = True
                            self.kick_animation_frame = 0
                            self.kick_loops_completed = 0
                            self.kick_loops_target = 3
                        elif action_roll < 0.50:  # 15% chance to lay down
                            self.walking = False  # Clear walking state
                            self.standing = False
                            self.laying_animation_playing = True
                            self.laying_animation_reverse = False
                            self.laying_animation_frame = 0
                        elif action_roll < 0.65:  # 15% chance to sit
                            self.walking = False  # Clear walking state
                            self.standing = False
                            self.sit_animation_playing = True
                            self.sit_animation_reverse = False
                            self.sit_animation_frame = 0
                        else:
                            # Keep walking, reset timer
                            self.time_until_action = random.uniform(2.0, 5.0)

            # Only move if walking and not doing any special action
            if (
                self.walking
                and not self.laying_down
                and not self.laying_animation_playing
                and not self.sitting
                and not self.sit_animation_playing
                and not self.kicking
            ):
                # Calculate new position
                new_x = self.x + self.walk_speed * self.walk_direction * dt

                # Check pond boundaries (pond is at bottom left)
                # Pond parameters from init_scenery
                pond_center_x = 100
                pond_center_y = SCREEN_HEIGHT - 40
                pond_width = 280
                pond_height = 140
                pond_left = pond_center_x - pond_width // 2 - 20  # Add buffer
                pond_right = pond_center_x + pond_width // 2 + 20  # Add buffer
                pond_top = pond_center_y - pond_height // 2 - 10  # Add buffer

                # Check if capybara would walk into pond area
                in_pond_x = pond_left < new_x < pond_right
                in_pond_y = self.y > pond_top  # Capybara is low enough to be near pond

                if in_pond_x and in_pond_y:
                    # Turn around instead of walking into pond
                    self.walk_direction *= -1
                    self.flip_sprite = self.walk_direction > 0
                else:
                    # Safe to move
                    self.x = new_x

                # Turn around at screen edges
                if self.x <= 50:
                    self.walk_direction = 1
                    self.flip_sprite = True
                elif self.x >= SCREEN_WIDTH - 50:
                    self.walk_direction = -1
                    self.flip_sprite = False

            # Keep current Y position (already set when landing)

        else:
            # Falling after balloon popped or shot
            if self.shot_capybara:
                # Shot capybara falls faster and off screen
                self.fall_speed += 800 * dt  # Faster gravity for shot capybaras
                self.y += self.fall_speed * dt

                # Slight horizontal drift while falling
                self.x += random.uniform(-20, 20) * dt

                # Remove when fallen off screen
                if self.y > SCREEN_HEIGHT + self.size:
                    return True  # Remove from game
            else:
                # Balloon was popped - gentler fall
                self.fall_speed += 300 * dt  # Gentler gravity
                self.y += self.fall_speed * dt

                # Check if hit ground (use pre-determined ground level)
                if self.y >= self.ground_y:
                    self.y = self.ground_y
                    self.grounded = True

                    # Check if capybara landed in pond area
                    pond_center_x = 100
                    pond_center_y = SCREEN_HEIGHT - 60
                    pond_width = 150
                    pond_height = 100
                    pond_left = pond_center_x - pond_width // 2
                    pond_right = pond_center_x + pond_width // 2
                    pond_top = pond_center_y - pond_height // 2 - 10

                    # If landed in pond, teleport to right edge + 10px
                    if pond_left < self.x < pond_right and self.y > pond_top:
                        self.x = pond_right + 10  # Move to right of pond + 10px
                        print(f"Capybara rescued from pond! Moved to x={self.x}")

                    # Randomly choose to stand or walk when landing
                    if random.random() < 0.2:  # 20% chance to stand
                        self.standing = True
                        self.walking = False
                    else:
                        self.walking = True
                        self.standing = False
                    self.walk_direction = random.choice([-1, 1])
                    self.flip_sprite = self.walk_direction > 0

        return False

    def check_hit(self, x: int, y: int) -> tuple[bool, str]:
        """Check if shot hit the balloon or capybara

        Returns:
            (hit, target) where target is 'balloon', 'capybara', or 'none'
        """
        if not self.alive or self.balloon_popped:
            return False, "none"

        # Check balloon hit first (above capybara)
        balloon_y = self.y - self.size // 2 - 40  # Balloon is above capybara
        balloon_distance = math.sqrt((x - self.x) ** 2 + (y - balloon_y) ** 2)
        if balloon_distance < self.balloon_radius:
            return True, "balloon"

        # Check capybara hit
        capybara_distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        if capybara_distance < self.size // 2:
            return True, "capybara"

        return False, "none"

    def shoot(self, target: str):
        """Handle shooting the balloon or capybara"""
        if target == "balloon":
            self.alive = False
            self.balloon_popped = True
            self.hit_time = time.time()
            self.fall_speed = 0
            # Set random landing position when balloon is popped
            self.ground_y = random.randint(575, 700)
        elif target == "capybara":
            self.alive = False
            self.balloon_popped = True
            self.shot_capybara = True
            self.hit_time = time.time()
            self.fall_speed = 0
            # Shot capybaras also get a random landing position
            self.ground_y = random.randint(575, 700)

    def draw(self, screen: pygame.Surface):
        """Draw the capybara with balloon"""
        # Check if capybara is on ground
        if self.grounded:
            # Draw grounded capybara (walking, standing, or doing actions)
            self._draw_walking_capybara(screen)
        elif not self.alive:
            # Draw falling/dead capybara
            self._draw_dead_capybara(screen)
        else:
            # Draw flying capybara with balloon
            self._draw_flying_capybara(screen)

    def _draw_flying_capybara(self, screen: pygame.Surface):
        """Draw a flying capybara with balloon"""
        x, y = int(self.x), int(self.y)

        # Draw balloon string first (behind balloon)
        balloon_x = x
        balloon_y = y - self.size // 2 - 40  # Balloon is above capybara

        # Draw wavy string from capybara to balloon
        string_points = []
        num_segments = 8
        for i in range(num_segments + 1):
            t = i / num_segments
            string_x = x + self.string_wave * math.sin(t * math.pi) * (1 - t)  # Less wave at top
            string_y = y - t * (self.size // 2 + 40)
            string_points.append((string_x, string_y))

        # Draw string
        for i in range(len(string_points) - 1):
            pygame.draw.line(screen, (100, 100, 100), string_points[i], string_points[i + 1], 2)

        # Draw balloon shadow
        shadow_offset = 3
        pygame.draw.circle(
            screen, (50, 50, 50, 100), (balloon_x + shadow_offset, balloon_y + shadow_offset), self.balloon_radius
        )

        # Draw balloon
        pygame.draw.circle(screen, self.balloon_color, (balloon_x, balloon_y), self.balloon_radius)

        # Draw balloon highlight
        highlight_x = balloon_x - self.balloon_radius // 3
        highlight_y = balloon_y - self.balloon_radius // 3
        pygame.draw.circle(screen, (255, 255, 255, 150), (highlight_x, highlight_y), self.balloon_radius // 4)

        # Draw capybara sprite
        if self.sprites_loaded and self.sprite_frames:
            # Get current sprite frame
            sprite = self.sprite_frames[self.sprite_frame_index]

            # Flip sprite if moving right
            if self.flip_sprite:
                sprite = pygame.transform.flip(sprite, True, False)

            # Draw sprite centered at position
            sprite_rect = sprite.get_rect(center=(x, y))
            screen.blit(sprite, sprite_rect)
        else:
            # Fallback to simple drawn capybara if sprites not loaded
            body_rect = pygame.Rect(x - self.size // 2, y - self.size // 3, self.size, self.size * 2 // 3)
            pygame.draw.ellipse(screen, self.color, body_rect)
            pygame.draw.ellipse(screen, (100, 60, 30), body_rect, 2)

            # Head (circle)
            head_size = self.size // 2
            head_x = x - self.size // 2 - head_size // 2 if self.vx < 0 else x + self.size // 2 - head_size // 2
            pygame.draw.circle(screen, self.color, (head_x, y - self.size // 4), head_size // 2)
            pygame.draw.circle(screen, (100, 60, 30), (head_x, y - self.size // 4), head_size // 2, 2)

    def _draw_walking_capybara(self, screen: pygame.Surface):
        """Draw a walking capybara on the ground"""
        x, y = int(self.x), int(self.y)

        # Draw sprite if available
        if self.sprites_loaded:
            sprite = None

            # Choose sprite based on state (priority: kicking > laying > sitting > standing > walking)
            if self.kicking:
                # Use front kick sprite
                if self.__class__.frontkick_sprite_frames:
                    sprite = self.__class__.frontkick_sprite_frames[self.kick_animation_frame]
                    # Front kick sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
            elif self.laying_down or self.laying_animation_playing:
                # Use sleeping sprite if sleeping, otherwise laydown sprite
                if self.sleeping and self.__class__.sleeping_sprite_frames:
                    sprite = self.__class__.sleeping_sprite_frames[self.sleeping_frame]
                    # Sleeping sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
                elif self.__class__.laydown_sprite_frames:
                    sprite = self.__class__.laydown_sprite_frames[self.laying_animation_frame]
                    # Laydown sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
            elif self.sitting or self.sit_animation_playing:
                # Use chilling sprite if chilling, otherwise sit sprite
                if self.chilling and self.__class__.chilling_sprite_frames:
                    sprite = self.__class__.chilling_sprite_frames[self.chilling_frame]
                    # Chilling sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
                elif self.__class__.sit_sprite_frames:
                    sprite = self.__class__.sit_sprite_frames[self.sit_animation_frame]
                    # Sit sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
            elif self.standing:
                # Use standing sprite
                if self.__class__.standing_sprite_frames:
                    sprite = self.__class__.standing_sprite_frames[self.standing_animation_frame]
                    # Standing sprites face west by default, flip if facing east
                    if self.flip_sprite:
                        sprite = pygame.transform.flip(sprite, True, False)
            elif self.walking and self.sprite_frames:
                # Use walking sprite
                sprite = self.sprite_frames[self.sprite_frame_index]
                # Flip sprite if moving right
                if self.flip_sprite:
                    sprite = pygame.transform.flip(sprite, True, False)

            if sprite:
                # Draw sprite centered at position
                sprite_rect = sprite.get_rect(center=(x, y))
                screen.blit(sprite, sprite_rect)
                return

        # Fallback to simple drawn capybara if sprites not loaded
        body_rect = pygame.Rect(x - self.size // 2, y - self.size // 3, self.size, self.size * 2 // 3)
        pygame.draw.ellipse(screen, self.color, body_rect)
        pygame.draw.ellipse(screen, (100, 60, 30), body_rect, 2)

    def _draw_dead_capybara(self, screen: pygame.Surface):
        """Draw a falling/dead capybara (shot capybara or safely landed)"""
        x, y = int(self.x), int(self.y)

        # Draw sprite if available
        if self.sprites_loaded and self.sprite_frames:
            # Keep animating sprite while falling
            self.sprite_animation_timer += 0.016  # Approximate dt
            if self.sprite_animation_timer > self.sprite_animation_speed:
                self.sprite_animation_timer = 0
                self.sprite_frame_index = (self.sprite_frame_index + 1) % len(self.sprite_frames)

            # Get current sprite frame
            sprite = self.sprite_frames[self.sprite_frame_index]

            # Flip sprite if needed
            if self.flip_sprite:
                sprite = pygame.transform.flip(sprite, True, False)

            # Only rotate if capybara was shot (not for safe landing)
            if self.shot_capybara:
                angle = (time.time() - self.hit_time) * 180  # Rotate while falling
                sprite = pygame.transform.rotate(sprite, angle)

            # Draw sprite centered at position
            sprite_rect = sprite.get_rect(center=(x, y))
            screen.blit(sprite, sprite_rect)
        else:
            # Fallback to simple drawn capybara
            body_rect = pygame.Rect(x - self.size // 2, y - self.size // 3, self.size, self.size * 2 // 3)
            pygame.draw.ellipse(screen, self.color, body_rect)
            pygame.draw.ellipse(screen, (100, 60, 30), body_rect, 2)

        # Draw X eyes only if capybara was shot (not if balloon was popped)
        if self.shot_capybara:
            eye_size = 12  # Bigger X for emphasis
            eye_offset = 15

            # X eyes (dead) - positioned relative to center
            pygame.draw.line(
                screen, (255, 0, 0), (x - eye_size, y - eye_offset - eye_size), (x + eye_size, y - eye_offset + eye_size), 4
            )
            pygame.draw.line(
                screen, (255, 0, 0), (x - eye_size, y - eye_offset + eye_size), (x + eye_size, y - eye_offset - eye_size), 4
            )


class CapybaraManager:
    """Manages capybara spawning, updating, and game state"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Capybara management
        self.capybaras: List[FlyingCapybara] = []
        self.spawn_timer = 0
        self.spawn_delay = 2.0  # Seconds between spawns
        self.current_wave_capybaras = 0  # Capybaras in current wave (1 or 2)
        self.wave_active = False

        # Game state tracking
        self.round_number = 1
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6

        # Round completion tracking
        self.round_complete = False
        self.round_ready_to_complete = False
        self.round_ready_time = 0
        self.game_over = False

    def update(self, dt: float, current_time: float) -> tuple[bool, bool, int]:
        """
        Update all capybaras and game state
        
        Returns:
            tuple of (capybaras_removed, new_wave_spawned, escaped_count)
        """
        # Track return values
        capybaras_removed = False
        new_wave_spawned = False
        escaped_count = 0
        
        # Update existing capybaras
        capybaras_to_remove = []
        for capybara in self.capybaras[:]:
            should_remove = capybara.update(dt)
            if should_remove:
                capybaras_to_remove.append(capybara)
        
        # Remove escaped capybaras and track escapes
        for capybara in capybaras_to_remove:
            # Check if this capybara escaped (balloon still intact) vs was shot
            if capybara.alive:  # Balloon intact = escaped
                escaped_count += 1
            self.capybaras.remove(capybara)
            capybaras_removed = True

        # Spawn capybaras (only during active gameplay)
        if not self.wave_active and self.capybaras_spawned < self.capybaras_per_round:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_wave()
                self.spawn_timer = 0
                new_wave_spawned = True

        # Check if wave is complete (all capybaras either escaped or balloon popped)
        if self.wave_active:
            flying_capybaras = [c for c in self.capybaras if c.alive]
            if len(flying_capybaras) == 0:
                self.wave_active = False

        # Check round completion
        if self.capybaras_spawned >= self.capybaras_per_round:
            flying_capybaras = [c for c in self.capybaras if c.alive]
            falling_capybaras = [c for c in self.capybaras if not c.alive and not c.grounded and not c.shot_capybara]
            
            # Round is ready when all capybaras are either landed or gone
            if len(flying_capybaras) == 0 and len(falling_capybaras) == 0 and not self.wave_active:
                if not self.round_ready_to_complete:
                    self.round_ready_to_complete = True
                    self.round_ready_time = current_time
                
                # Check if round passes or fails after 2 second delay
                elif self.round_ready_to_complete and current_time - self.round_ready_time >= 2.0:
                    if self.capybaras_hit >= self.required_hits:
                        self.round_complete = True
                    else:
                        # Game over - failed to hit enough capybaras
                        self.game_over = True
        
        return (capybaras_removed, new_wave_spawned, escaped_count)

    def spawn_wave(self):
        """Spawn a wave of capybaras"""
        if self.capybaras_spawned >= self.capybaras_per_round:
            return
        
        self.wave_active = True
        
        # Determine number of capybaras to spawn
        if self.round_number <= 2:
            num_capybaras = 1  # Always single spawn for first 2 rounds
        else:
            # Calculate chance for multiple spawn (increases with rounds)
            multi_spawn_chance = min(0.3 + (self.round_number - 3) * 0.1, 0.8)  # Cap at 80%
            if random.random() < multi_spawn_chance and self.capybaras_spawned < self.capybaras_per_round - 1:
                num_capybaras = 2
            else:
                num_capybaras = 1
                
        self.current_wave_capybaras = min(num_capybaras, self.capybaras_per_round - self.capybaras_spawned)
        
        # Spawn capybaras from grass area
        grass_line = self.screen_height * 2 // 3
        
        for i in range(self.current_wave_capybaras):
            # Spawn in middle 60% of screen width
            start_x = random.randint(int(self.screen_width * 0.2), int(self.screen_width * 0.8))
            start_y = random.randint(grass_line, grass_line + 20)
            
            # Random direction
            direction = random.choice(["left", "right", "diagonal_left", "diagonal_right"])
            
            # Speed increases with round
            speed_multiplier = 1.0 + (self.round_number - 1) * 0.08
            
            capybara = FlyingCapybara(start_x, start_y, direction, speed_multiplier)
            self.capybaras.append(capybara)
            self.capybaras_spawned += 1

    def check_hit(self, x: int, y: int) -> tuple[bool, str, int]:
        """
        Check if shot hit any capybara
        
        Returns:
            (hit, target_type, score) where target_type is 'balloon', 'capybara', or 'none'
        """
        for capybara in self.capybaras:
            hit, target = capybara.check_hit(x, y)
            if hit:
                capybara.shoot(target)
                
                if target == "balloon":
                    self.capybaras_hit += 1
                    # Score based on round number
                    score = 100 * self.round_number
                    return True, "balloon", score
                elif target == "capybara":
                    # Penalty for shooting capybara
                    return True, "capybara", -50
                    
        return False, "none", 0

    def draw(self, screen: pygame.Surface):
        """Draw all capybaras with depth layering (back to front)"""
        # Sort capybaras by Y position for proper depth layering
        # Capybaras higher up (smaller Y) should be drawn first (behind)
        # Capybaras lower down (larger Y) should be drawn last (in front)
        sorted_capybaras = sorted(self.capybaras, key=lambda c: c.y)
        
        for capybara in sorted_capybaras:
            capybara.draw(screen)

    def start_next_round(self):
        """Start the next round"""
        self.round_number += 1
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.round_complete = False
        self.round_ready_to_complete = False
        self.round_ready_time = 0
        self.game_over = False
        self.capybaras.clear()
        self.spawn_timer = 0
        self.wave_active = False
        
        # Increase difficulty
        if self.round_number <= 3:
            self.required_hits = 6
        elif self.round_number <= 6:
            self.required_hits = 7
        else:
            self.required_hits = 8

    def reset_game(self):
        """Reset game to initial state"""
        self.round_number = 1
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6
        self.round_complete = False
        self.round_ready_to_complete = False
        self.round_ready_time = 0
        self.game_over = False
        self.capybaras.clear()
        self.spawn_timer = 0
        self.wave_active = False

    def get_flying_capybaras_count(self) -> int:
        """Get count of capybaras that are still flying"""
        return len([c for c in self.capybaras if c.alive])
        
    def get_grounded_capybaras_count(self) -> int:
        """Get count of capybaras that are grounded and active"""
        return len([c for c in self.capybaras if c.grounded])