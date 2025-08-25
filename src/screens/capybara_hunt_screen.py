"""
Capybara Hunt - Duck Hunt inspired game mode with flying capybaras
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
            if self.time_until_action <= 0 and not self.laying_animation_playing and not self.sit_animation_playing and not self.kicking:
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


class CapybaraHuntScreen(BaseScreen):
    """Capybara Hunt gameplay screen - Duck Hunt inspired"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        # Initialize base class (handles camera, hand tracker, sound manager, settings)
        super().__init__(screen, camera_manager)

        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        self.huge_font = pygame.font.Font(None, 120)

        # Game state
        self.round_number = 1
        self.score = 0
        self.shots_remaining = 5  # Increased from 3 to 5 for buffer
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6  # Start with 6/10 required
        self.game_over = False
        self.round_complete = False
        self.round_complete_time = 0
        self.round_ready_to_complete = False  # Track when round is ready to complete
        self.round_ready_time = 0  # Time when round became ready
        self.paused = False

        # UI Buttons for shooting
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None
        
        # Pond companion (like Duck Hunt dog)
        self.pond_buddy = {
            'x': 100,  # Center of pond
            'y': SCREEN_HEIGHT - 70,  # In the pond - raised up a bit
            'mood': 'neutral',  # neutral, happy, sad, excited, laughing, surprised, celebration, relieved, proud, disappointed, worried
            'mood_timer': 0,
            'mood_duration': 2.0,  # How long each mood lasts
            'bob_offset': 0,  # For bobbing animation
            'bob_time': 0,
            'last_hit_streak': 0,  # Track consecutive hits
            'last_miss_streak': 0,  # Track consecutive misses
            'animation_frame': 0,
            'animation_timer': 0,
            'sprite': None  # Will load the pond buddy sprite
        }
        
        # Load pond buddy sprite
        try:
            self.pond_buddy['sprite'] = pygame.image.load('assets/pond_buddy.png').convert_alpha()
            # Scale it to be bigger
            self.pond_buddy['sprite'] = pygame.transform.scale(self.pond_buddy['sprite'], (100, 100))
        except Exception as e:
            print(f"Could not load pond buddy sprite: {e}")
            self.pond_buddy['sprite'] = None

        # Capybara management
        self.capybaras: List[FlyingCapybara] = []
        self.spawn_timer = 0
        self.spawn_delay = 2.0  # Seconds between spawns
        self.current_wave_capybaras = 0  # Capybaras in current wave (1 or 2)
        self.wave_active = False

        # Shooting state
        self.shoot_pos = None
        self.shoot_animation_time = 0
        self.shoot_animation_duration = 200
        self.capybara_shot_message_time = 0  # For showing punishment message

        # Hit tracking for round
        self.hit_markers = []  # List of booleans for hit/miss display

        # Performance tracking
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0

        # Background
        self.create_background()

        # Animated scenery elements
        self.init_scenery()

        # Debug console (for pause menu commands)
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
                int(135 + (206 - 135) * progress),  # Sky blue to lighter
                int(206 + (235 - 206) * progress),
                int(235 + (250 - 235) * progress),
            )
            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))

        # Draw distant mountains (back layer)
        self.draw_mountain_layer(
            self.background,
            color=(170, 180, 200),  # Light blue-gray for distance
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

        # Draw rolling hills (front layer)
        self.draw_hills_layer(
            self.background,
            color=(120, 130, 100),  # Muted sage/olive color for distant hills
            base_y=SCREEN_HEIGHT * 2 // 3,
            hill_count=5,
            max_height=80,
        )

        # Ground
        ground_color = (34, 139, 34)  # Forest green
        pygame.draw.rect(self.background, ground_color, (0, SCREEN_HEIGHT * 2 // 3, SCREEN_WIDTH, SCREEN_HEIGHT // 3))

        # Add some grass texture
        for _ in range(200):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(SCREEN_HEIGHT * 2 // 3, SCREEN_HEIGHT)
            height = random.randint(5, 15)
            pygame.draw.line(self.background, (46, 125, 50), (x, y), (x, y - height), 1)

        # Draw pond in bottom left corner (cut off by edge)
        pond_center_x = 100  # Mostly visible, slightly cut off on left
        pond_center_y = SCREEN_HEIGHT - 40  # Lower, so bottom is cut off
        pond_width = 280  # Bigger pond
        pond_height = 140  # Bigger pond

        # Draw pond water
        pond_rect = pygame.Rect(pond_center_x - pond_width // 2, pond_center_y - pond_height // 2, pond_width, pond_height)

        # Draw pond with gradient effect
        for i in range(pond_height // 2):
            color_factor = i / (pond_height // 2)
            water_color = (
                int(64 + 20 * color_factor),  # Blue gets lighter toward edge
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

        # Add pond edge with darker color
        pygame.draw.ellipse(self.background, (40, 90, 120), pond_rect, 3)

    def draw_mountain_layer(self, surface, color, peak_heights, base_y, peak_variance):
        """Draw a layer of mountains with jagged peaks"""
        points = [(0, base_y)]

        # Create mountain peaks
        num_peaks = len(peak_heights)
        for i, height in enumerate(peak_heights):
            x = (i + 1) * (SCREEN_WIDTH // (num_peaks + 1))

            # Add some smaller peaks between main peaks for more natural look
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

        # Draw filled mountains
        pygame.draw.polygon(surface, color, points)

        # Add subtle shading with darker edges
        darker_color = tuple(max(0, c - 20) for c in color)
        pygame.draw.lines(surface, darker_color, False, points[: len(peak_heights) * 2 + 2], 2)

    def draw_hills_layer(self, surface, color, base_y, hill_count, max_height):
        """Draw rolling hills using smooth curves"""
        points = [(0, base_y)]

        # Create smooth rolling hills using sine waves
        for x in range(0, SCREEN_WIDTH + 10, 10):
            # Combine multiple sine waves for natural rolling effect
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

        # Draw filled hills
        pygame.draw.polygon(surface, color, points)

        # Add gentle highlight on tops
        lighter_color = tuple(min(255, c + 10) for c in color)
        for i in range(1, len(points) - 2):
            if points[i][1] < points[i - 1][1] and points[i][1] < points[i + 1][1]:  # Peak point
                pygame.draw.circle(surface, lighter_color, (int(points[i][0]), int(points[i][1])), 3)

    def init_scenery(self):
        """Initialize animated scenery elements"""
        # Define pond parameters first (needed for flower and grass placement)
        self.pond_center_x = 100
        self.pond_center_y = SCREEN_HEIGHT - 40
        self.pond_width = 280
        self.pond_height = 140

        # Clouds
        self.clouds = []
        for i in range(5):
            cloud = {
                "x": random.randint(-200, SCREEN_WIDTH),
                "y": random.randint(30, 150),  # Raised higher - was 50-200
                "speed": random.uniform(10, 30),  # pixels per second
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

        for i in range(12):  # Reduced from 20 to 12
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

            # Only add flower if we found a valid position
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

        # Animated grass tufts (pixel art style)
        self.grass_tufts = []
        ground_line = SCREEN_HEIGHT * 2 // 3
        pond_left = self.pond_center_x - self.pond_width // 2
        pond_right = self.pond_center_x + self.pond_width // 2
        pond_top = self.pond_center_y - self.pond_height // 2

        # Create fewer but more visible grass tufts
        for _ in range(80):  # Reduced from 200 to 80 for cleaner look
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
                "y": self.pond_center_y + random.randint(-40, 20),  # Adjusted for lower pond
                "radius": random.uniform(0, 20),
                "max_radius": random.uniform(25, 40),  # Smaller max radius to stay in bounds
                "speed": random.uniform(15, 25),
                "opacity": 255,
            }
            self.pond_ripples.append(ripple)

    def update_scenery(self, dt: float):
        """Update animated scenery elements"""
        current_time = pygame.time.get_ticks() / 1000.0

        # Update clouds
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"] * dt
            if cloud["x"] > SCREEN_WIDTH + 200:
                cloud["x"] = -200
                cloud["y"] = random.randint(30, 150)  # Match initial spawn height

        # Update birds
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

        # Update floating particles
        for particle in self.particles:
            # Gentle floating movement
            particle["x"] += particle["vx"] * dt + math.sin(current_time * 2 + particle["rotation"]) * 10 * dt
            particle["y"] += particle["vy"] * dt
            particle["rotation"] += particle["rotation_speed"] * dt

            # Respawn at top when reaching bottom
            if particle["y"] > SCREEN_HEIGHT + 10:
                particle["y"] = -10
                particle["x"] = random.randint(0, SCREEN_WIDTH)

        # Update sun rays
        self.sun_ray_angle += dt * 0.1

        # Update pond ripples
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

        # Update existing ripples
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

        # Draw sun and rays
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

            # Only draw if ripple center is within or near the pond ellipse
            if ellipse_check < 1.5:  # 1.5 allows slight overlap but prevents far escapes
                # Calculate ellipse dimensions based on pond aspect ratio
                # The pond is wider than it is tall, so maintain that ratio
                ellipse_width = int(ripple["radius"] * 2)
                ellipse_height = int(ripple["radius"] * 1.4)  # Make height smaller to match pond shape
                
                # Create a surface for the ripple with transparency
                ripple_surface = pygame.Surface(
                    (ellipse_width + 4, ellipse_height + 4), pygame.SRCALPHA
                )

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

                # Blit the ripple to the screen (center it on the ripple position)
                self.screen.blit(ripple_surface, 
                    (ripple["x"] - ellipse_width // 2 - 2, 
                     ripple["y"] - ellipse_height // 2 - 2))

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
                if self.round_complete and self.continue_button:
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
                if not self.game_over and not self.round_complete:
                    self.paused = not self.paused
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_RETURN and (self.game_over or self.round_complete):
                if self.game_over:
                    self.reset_game()
                elif self.round_complete:
                    self.start_next_round()
            elif event.key == pygame.K_SLASH and self.paused:  # Open console with /
                self.console_active = True
                self.console_input = "/"

        return None

    def reset_game(self) -> None:
        """Reset the entire game"""
        self.round_number = 1
        self.score = 0
        self.shots_remaining = 5  # Reset to 5 shots
        self.capybaras_per_round = 10
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.required_hits = 6
        self.game_over = False
        self.round_complete = False
        self.round_ready_to_complete = False
        self.round_ready_time = 0
        self.capybaras.clear()
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False
        self.hand_tracker.reset_tracking_state()
        self.shoot_pos = None
        self.crosshair_pos = None
        # Reset buttons
        self.continue_button = None
        self.retry_button = None
        self.menu_button = None

    def start_next_round(self) -> None:
        """Start the next round"""
        self.round_number += 1
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.shots_remaining = 5  # Reset to 5 shots for new round
        self.round_complete = False
        self.round_ready_to_complete = False
        self.round_ready_time = 0
        self.capybaras.clear()  # Clear capybaras when starting new round
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False
        # Reset continue button for next round
        self.continue_button = None

        # Increase difficulty (slower progression)
        self.required_hits = min(9, 6 + (self.round_number - 1) // 5)  # More gradual increase
        self.spawn_delay = max(1.0, 2.0 - self.round_number * 0.1)  # Faster spawns
        
        # Pond buddy gets excited for new round
        if self.round_number > 1:
            if self.round_number % 5 == 0:
                # Milestone round!
                self._set_pond_buddy_mood('celebration', 2.0)
            else:
                self._set_pond_buddy_mood('excited', 1.5)

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update game state"""
        # Process hand tracking always (for button shooting)
        self._process_hand_tracking()

        # Always update animations (even during round complete/game over)
        self._update_pond_buddy(dt)
        self.update_scenery(dt)

        # Always update capybara animations (even during round complete/game over)
        capybaras_to_remove = []
        for capybara in self.capybaras:
            if capybara.update(dt):
                capybaras_to_remove.append(capybara)
                # Only count misses during active gameplay
                if not self.round_complete and not self.game_over:
                    if capybara.alive and not hasattr(capybara, "already_counted"):
                        # Missed (escaped) - only count if not already counted
                        self.hit_markers.append(False)
                        capybara.already_counted = True
                        # Pond buddy reacts to the escape
                        self._on_capybara_escape()

        for capybara in capybaras_to_remove:
            self.capybaras.remove(capybara)

        # Handle button shooting in round complete or game over states
        if self.round_complete:
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

        # Spawn capybaras (only during active gameplay)
        if not self.wave_active and self.capybaras_spawned < self.capybaras_per_round:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_wave()
                self.spawn_timer = 0

        # Check if wave is complete (all capybaras either escaped or balloon popped)
        if self.wave_active:
            flying_capybaras = [c for c in self.capybaras if c.alive]
            if len(flying_capybaras) == 0:
                self.wave_active = False
                self.shots_remaining = 5  # Reset shots for next wave

        # Check round completion (when all capybaras spawned and no flying/falling ones left)
        if self.capybaras_spawned >= self.capybaras_per_round:
            flying_capybaras = [c for c in self.capybaras if c.alive]
            # Falling capybaras are those that are not alive, not grounded, and not shot
            falling_capybaras = [c for c in self.capybaras if not c.alive and not c.grounded and not c.shot_capybara]

            # First check if round is ready (all capybaras are either landed or gone)
            if len(flying_capybaras) == 0 and len(falling_capybaras) == 0 and not self.wave_active:
                if not self.round_ready_to_complete:
                    self.round_ready_to_complete = True
                    self.round_ready_time = time.time()

                # Wait 0.5 seconds before showing continue screen
                if time.time() - self.round_ready_time >= 0.5:
                    # Don't clear capybaras here - let them stay visible
                    # They'll be cleared when continue is clicked

                    if self.capybaras_hit >= self.required_hits:
                        self.round_complete = True
                        self.round_complete_time = time.time()
                        # Perfect round bonus
                        if self.capybaras_hit == self.capybaras_per_round:
                            self.score += 1000 * self.round_number
                            # Pond buddy celebrates perfect round
                            self._set_pond_buddy_mood('celebration', 4.0)
                        elif self.capybaras_hit == self.required_hits:
                            # Just barely made it
                            self._set_pond_buddy_mood('relieved', 3.0)
                        else:
                            # Good job
                            self._set_pond_buddy_mood('proud', 3.0)
                    else:
                        self.game_over = True
                        # Pond buddy reacts to game over
                        self._set_pond_buddy_mood('disappointed', 5.0)

        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0

        return None

    def spawn_wave(self):
        """Spawn a wave of 1 or 2 capybaras"""
        self.wave_active = True

        # Determine number of capybaras based on round with increasing chance
        if self.round_number <= 2:
            num_capybaras = 1
        else:
            # Calculate chance for multiple spawn (increases with rounds)
            # Round 3: 30% chance, Round 4: 40%, Round 5: 50%, etc.
            multi_spawn_chance = min(0.3 + (self.round_number - 3) * 0.1, 0.8)  # Cap at 80%

            # Check if we should spawn 2 (and if we have at least 2 capybaras left to spawn)
            if random.random() < multi_spawn_chance and self.capybaras_spawned < self.capybaras_per_round - 1:
                num_capybaras = 2
            else:
                num_capybaras = 1

        self.current_wave_capybaras = min(num_capybaras, self.capybaras_per_round - self.capybaras_spawned)

        # Spawn capybaras from grass area (2/3 down the screen)
        grass_line = SCREEN_HEIGHT * 2 // 3

        for i in range(self.current_wave_capybaras):
            # Spawn in the middle 60% of the screen to give better shooting opportunity
            # Avoid edges: spawn between 20% and 80% of screen width
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
            speed_multiplier = 1.0 + (self.round_number - 1) * 0.08  # 8% increase per round instead of 15%

            capybara = FlyingCapybara(start_x, start_y, direction, speed_multiplier)
            self.capybaras.append(capybara)
            self.capybaras_spawned += 1

    def _process_hand_tracking(self) -> None:
        """Process hand tracking and shooting detection"""
        # Use base class method for tracking
        self.process_finger_gun_tracking()

        # Only handle shooting in active game
        if not self.game_over and not self.round_complete and not self.paused:
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
        if self.shots_remaining <= 0 or not self.wave_active:
            return

        self.shoot_pos = shoot_position
        self.shoot_animation_time = pygame.time.get_ticks()
        self.shots_remaining -= 1

        # Play shoot sound
        self.sound_manager.play("shoot")

        # Check for hits
        hit_any = False
        for capybara in self.capybaras:
            hit, target = capybara.check_hit(shoot_position[0], shoot_position[1])
            if hit:
                if target == "balloon":
                    # Good shot! Saved the capybara
                    capybara.shoot("balloon")
                    capybara.already_counted = True  # Mark as counted
                    self.score += 100 * self.round_number
                    self.capybaras_hit += 1
                    self.hit_markers.append(True)
                    self._on_capybara_hit()  # Pond buddy reacts
                    self.sound_manager.play("hit")
                    hit_any = True
                elif target == "capybara":
                    # Bad shot! Shot the capybara instead of balloon
                    capybara.shoot("capybara")
                    capybara.already_counted = True  # Mark as counted
                    self.score -= 200 * self.round_number  # Penalty for shooting capybara
                    self.hit_markers.append(False)  # Mark as miss
                    self._on_capybara_miss()  # Pond buddy reacts
                    self.sound_manager.play("error")  # Play error sound
                    # Flash the screen red for visual feedback
                    self.shoot_animation_time = pygame.time.get_ticks() - 100  # Make animation last longer
                    self.capybara_shot_message_time = pygame.time.get_ticks()  # Show warning message
                    hit_any = True
                break

        # Check if wave should end (out of ammo)
        if self.shots_remaining == 0:
            # Mark ALL remaining flying capybaras in this wave as missed
            flying_in_wave = [c for c in self.capybaras if c.alive and not hasattr(c, "already_counted")]
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

        # Always draw capybaras and pond buddy (even during round complete/game over)
        # Draw capybaras (sorted by Y position for depth layering)
        # Capybaras with lower Y values (higher up) are drawn first (behind)
        # Capybaras with higher Y values (lower down) are drawn last (in front)
        sorted_capybaras = sorted(self.capybaras, key=lambda c: c.y)
        for capybara in sorted_capybaras:
            capybara.draw(self.screen)
        
        # Draw pond buddy (after capybaras so it appears in front)
        self._draw_pond_buddy()

        if self.paused:
            self._draw_pause_screen()
            return

        if self.game_over:
            self._draw_game_over_screen()
            # Draw crosshair for button shooting
            if self.crosshair_pos:
                self.draw_crosshair(self.crosshair_pos, self.crosshair_color)
            self._draw_camera_feed()
            return

        if self.round_complete:
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
        round_text = self.font.render(f"Round: {self.round_number}", True, WHITE)
        self.screen.blit(round_text, (10, 50))

        # Shots remaining
        shot_text = self.font.render(
            f"Shots: {self.shots_remaining}", True, WHITE if self.shots_remaining > 0 else (255, 0, 0)
        )
        self.screen.blit(shot_text, (10, 90))

        # Hit/Pass meter (like Duck Hunt)
        meter_x = SCREEN_WIDTH // 2 - 150
        meter_y = SCREEN_HEIGHT - 80

        # Draw hit markers
        for i in range(self.capybaras_per_round):
            x = meter_x + i * 30
            if i < len(self.hit_markers):
                color = GREEN if self.hit_markers[i] else (255, 0, 0)
            else:
                color = WHITE
            pygame.draw.rect(self.screen, color, (x, meter_y, 25, 25))
            pygame.draw.rect(self.screen, BLACK, (x, meter_y, 25, 25), 2)

        # Draw pass line
        pass_line_x = meter_x + (self.required_hits - 1) * 30 + 25
        pygame.draw.line(self.screen, YELLOW, (pass_line_x, meter_y - 5), (pass_line_x, meter_y + 30), 3)

        # Required hits text
        req_text = self.small_font.render(f"Need {self.required_hits}/{self.capybaras_per_round}", True, WHITE)
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

            penalty_text = self.font.render(f"-{200 * self.round_number} points!", True, (255, 100, 100))
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
        overlay.set_alpha(80)  # More transparent so you can see the pond buddy's reaction
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = self.huge_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)

        # Stats
        stats = [
            f"Final Score: {self.score}",
            f"Rounds Completed: {self.round_number - 1}",
            f"Capybaras Hit: {self.capybaras_hit}/{self.capybaras_per_round}",
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
        if self.capybaras_hit == self.capybaras_per_round:
            complete_text = self.big_font.render(f"PERFECT!! +{1000 * self.round_number}", True, YELLOW)
        else:
            complete_text = self.big_font.render(f"ROUND {self.round_number} COMPLETE!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(complete_text, complete_rect)

        # Stats
        stats_text = self.font.render(
            f"Hit: {self.capybaras_hit}/{self.capybaras_per_round} | Score: {self.score}", True, WHITE
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
            # Set current round to perfect score
            self.capybaras_hit = self.capybaras_per_round
            self.hit_markers = [True] * self.capybaras_per_round
            self.console_message = "Perfect round activated"

        elif command == "/miss":
            # Force a miss for testing game over
            self.capybaras_hit = 0
            self.hit_markers = [False] * self.capybaras_per_round
            self.console_message = "Forced miss - prepare for game over"

        elif command == "/skip":
            # Skip to round complete
            if not self.round_complete and not self.game_over:
                self.capybaras_spawned = self.capybaras_per_round
                self.capybaras.clear()
                self.wave_active = False
                self.console_message = "Skipped to round end"
            else:
                self.console_message = "Cannot skip - round already complete"

        else:
            self.console_message = "Unknown command. Try: /round #, /score #, /perfect, /miss, /skip"

        self.console_message_time = time.time()

    def _jump_to_round(self, round_num: int):
        """Jump directly to a specific round"""
        # Reset game state
        self.round_number = round_num
        self.capybaras_spawned = 0
        self.capybaras_hit = 0
        self.shots_remaining = 3
        self.round_complete = False
        self.game_over = False
        self.capybaras.clear()
        self.hit_markers.clear()
        self.spawn_timer = 0
        self.wave_active = False

        # Adjust difficulty for the round
        self.required_hits = min(9, 6 + (round_num - 1) // 5)
        self.spawn_delay = max(1.0, 2.0 - round_num * 0.1)
    
    def _update_pond_buddy(self, dt: float):
        """Update pond buddy animations and mood"""
        # Update mood timer
        if self.pond_buddy['mood_timer'] > 0:
            self.pond_buddy['mood_timer'] -= dt
            if self.pond_buddy['mood_timer'] <= 0:
                self.pond_buddy['mood'] = 'neutral'
                self.pond_buddy['last_hit_streak'] = 0
                self.pond_buddy['last_miss_streak'] = 0
        
        # Random idle reactions when neutral
        if self.pond_buddy['mood'] == 'neutral' and random.random() < 0.01:  # Small chance each frame
            idle_moods = ['surprised', 'happy', 'laughing']
            self._set_pond_buddy_mood(random.choice(idle_moods), random.uniform(0.5, 1.5))
        
        # Bobbing animation
        self.pond_buddy['bob_time'] += dt
        self.pond_buddy['bob_offset'] = math.sin(self.pond_buddy['bob_time'] * 2) * 3
        
        # Animation frame update for expressions
        self.pond_buddy['animation_timer'] += dt
        if self.pond_buddy['animation_timer'] > 0.2:
            self.pond_buddy['animation_timer'] = 0
            self.pond_buddy['animation_frame'] = (self.pond_buddy['animation_frame'] + 1) % 2
    
    def _set_pond_buddy_mood(self, mood: str, duration: float = 2.0):
        """Set the pond buddy's mood"""
        self.pond_buddy['mood'] = mood
        self.pond_buddy['mood_timer'] = duration
        self.pond_buddy['animation_frame'] = 0
    
    def _on_capybara_hit(self):
        """Called when player successfully hits a capybara"""
        self.pond_buddy['last_hit_streak'] += 1
        self.pond_buddy['last_miss_streak'] = 0
        
        if self.pond_buddy['last_hit_streak'] >= 5:
            # Amazing streak!
            self._set_pond_buddy_mood('celebration', 3.5)
        elif self.pond_buddy['last_hit_streak'] >= 3:
            self._set_pond_buddy_mood('excited', 3.0)
        elif self.pond_buddy['last_hit_streak'] == 1:
            self._set_pond_buddy_mood('happy', 1.5)
    
    def _on_capybara_miss(self):
        """Called when player shoots capybara instead of balloon"""
        self.pond_buddy['last_miss_streak'] += 1
        self.pond_buddy['last_hit_streak'] = 0
        
        if self.pond_buddy['last_miss_streak'] >= 3:
            self._set_pond_buddy_mood('laughing', 2.5)
        else:
            self._set_pond_buddy_mood('sad', 1.5)
    
    def _on_capybara_escape(self):
        """Called when a capybara escapes (flies away)"""
        # Show worried expression when capybara escapes
        self._set_pond_buddy_mood('worried', 1.5)
    
    def _draw_pond_buddy(self):
        """Draw the pond companion"""
        x = self.pond_buddy['x']
        y = self.pond_buddy['y'] + self.pond_buddy['bob_offset']
        mood = self.pond_buddy['mood']
        
        # Draw the pond buddy sprite if loaded
        if self.pond_buddy['sprite']:
            # Calculate sprite position (centered on x, y)
            sprite_rect = self.pond_buddy['sprite'].get_rect()
            sprite_rect.center = (int(x), int(y))
            self.screen.blit(self.pond_buddy['sprite'], sprite_rect)
            
            # Now draw facial expressions on top of the sprite
            # The face area appears to be in the center-upper part of the sprite
            # Adjusting positions based on the sprite's face area (scaled for 100x100)
            face_x = x + 2  
            face_y = y - 20  
            
            # Draw face based on mood
            eye_color = (0, 0, 0)
            
            if mood == 'neutral':
                # Normal eyes - farther apart (scaled for larger sprite)
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 5)
            
            elif mood == 'happy':
                # Happy eyes (curved) - draw multiple passes to fill gaps
                left_eye_rect = (int(face_x - 20), int(face_y - 3), 12, 12)
                right_eye_rect = (int(face_x + 8), int(face_y - 3), 12, 12)
                pygame.draw.arc(self.screen, eye_color, left_eye_rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (left_eye_rect[0], left_eye_rect[1]+1, left_eye_rect[2], left_eye_rect[3]), 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, right_eye_rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (right_eye_rect[0], right_eye_rect[1]+1, right_eye_rect[2], right_eye_rect[3]), 0, math.pi, 3)
                # Smile (upward curve) - draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 7), 28, 16)
                pygame.draw.arc(self.screen, eye_color, rect, math.pi, 2 * math.pi, 2)
                # Draw again with slight offset to fill gaps
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)
            
            elif mood == 'sad':
                # Sad eyes (small) - scaled up
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 3)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 3)
                # Frown (downward curve) - draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 18), 28, 14)
                pygame.draw.arc(self.screen, eye_color, rect, 0, math.pi, 3)
                # Draw again with slight offset to fill gaps
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]+1, rect[2], rect[3]), 0, math.pi, 3)
            
            elif mood == 'excited':
                # Star eyes
                frame = self.pond_buddy['animation_frame']
                if frame == 0:
                    # Wide eyes - scaled up
                    pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 6)
                    pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 6)
                    pygame.draw.circle(self.screen, WHITE, (int(face_x - 13), int(face_y - 2)), 3)
                    pygame.draw.circle(self.screen, WHITE, (int(face_x + 17), int(face_y - 2)), 3)
                else:
                    # Sparkle effect - scaled up
                    pygame.draw.circle(self.screen, (255, 215, 0), (int(face_x - 15), int(face_y)), 5)
                    pygame.draw.circle(self.screen, (255, 215, 0), (int(face_x + 15), int(face_y)), 5)
                # Big smile - draw multiple passes to fill gaps
                rect = (int(face_x - 18), int(face_y + 7), 36, 20)
                pygame.draw.arc(self.screen, eye_color, rect, math.pi, 2 * math.pi, 2)
                # Draw again with slight offset to fill gaps
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)
            
            elif mood == 'laughing':
                # Closed eyes (laughing) - draw multiple passes to fill gaps
                left_eye_rect = (int(face_x - 20), int(face_y), 12, 6)
                right_eye_rect = (int(face_x + 8), int(face_y), 12, 6)
                pygame.draw.arc(self.screen, eye_color, left_eye_rect, math.pi, 2 * math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, (left_eye_rect[0], left_eye_rect[1]-1, left_eye_rect[2], left_eye_rect[3]), math.pi, 2 * math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, right_eye_rect, math.pi, 2 * math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, (right_eye_rect[0], right_eye_rect[1]-1, right_eye_rect[2], right_eye_rect[3]), math.pi, 2 * math.pi, 2)
                # Wide open mouth - lowered (laughing mouth isn't a smile)
                if self.pond_buddy['animation_frame'] == 0:
                    pygame.draw.ellipse(self.screen, eye_color, (int(face_x - 10), int(face_y + 14), 20, 14))
                    pygame.draw.ellipse(self.screen, (255, 192, 203), (int(face_x - 7), int(face_y + 16), 14, 9))
                else:
                    # Draw multiple passes to fill gaps
                    rect = (int(face_x - 14), int(face_y + 7), 28, 16)
                    pygame.draw.arc(self.screen, eye_color, rect, math.pi, 2 * math.pi, 2)
                    pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)
        
            elif mood == 'surprised':
                # Wide eyes - scaled up
                pygame.draw.circle(self.screen, WHITE, (int(face_x - 15), int(face_y)), 8)
                pygame.draw.circle(self.screen, WHITE, (int(face_x + 15), int(face_y)), 8)
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 5)
                # O mouth - filled black circle - lowered
                pygame.draw.circle(self.screen, eye_color, (int(face_x), int(face_y + 16)), 7)
            
            elif mood == 'celebration':
                # Jumping animation
                jump_offset = abs(math.sin(self.pond_buddy['animation_timer'] * 10)) * 5
                face_y -= jump_offset
                # Star eyes - scaled up
                for eye_x in [-15, 15]:
                    cx = int(face_x + eye_x)
                    cy = int(face_y)
                    # Draw star shape - scaled up
                    pygame.draw.line(self.screen, (255, 215, 0), (cx - 5, cy), (cx + 5, cy), 3)
                    pygame.draw.line(self.screen, (255, 215, 0), (cx, cy - 5), (cx, cy + 5), 3)
                    pygame.draw.line(self.screen, (255, 215, 0), (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
                    pygame.draw.line(self.screen, (255, 215, 0), (cx - 4, cy + 4), (cx + 4, cy - 4), 2)
                # Huge smile - draw multiple passes to fill gaps
                rect = (int(face_x - 20), int(face_y + 5), 40, 24)
                pygame.draw.arc(self.screen, eye_color, rect, math.pi, 2 * math.pi, 3)
                # Draw again with slight offset to fill gaps
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi, 2 * math.pi, 3)
                # Party hat (triangle on top of head) - scaled up
                hat_color = (255, 20, 147) if self.pond_buddy['animation_frame'] == 0 else (16, 231, 245)
                pygame.draw.polygon(self.screen, hat_color, [
                    (int(face_x), int(face_y - 40)),
                    (int(face_x - 14), int(face_y - 20)),
                    (int(face_x + 14), int(face_y - 20))
                ])
            
            elif mood == 'relieved':
                # Half-closed eyes (relief) - draw multiple passes to fill gaps
                left_eye_rect = (int(face_x - 18), int(face_y - 2), 10, 8)
                right_eye_rect = (int(face_x + 8), int(face_y - 2), 10, 8)
                pygame.draw.arc(self.screen, eye_color, left_eye_rect, math.pi, 2 * math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (left_eye_rect[0], left_eye_rect[1]-1, left_eye_rect[2], left_eye_rect[3]), math.pi, 2 * math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, right_eye_rect, math.pi, 2 * math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (right_eye_rect[0], right_eye_rect[1]-1, right_eye_rect[2], right_eye_rect[3]), math.pi, 2 * math.pi, 3)
                # Slight smile - draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 7), 28, 16)
                pygame.draw.arc(self.screen, eye_color, rect, math.pi, 2 * math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi, 2 * math.pi, 2)
                # Sweat drop - teardrop shape (rounded cone)
                sweat_color = (100, 180, 255)  # Bright blue
                drop_x = int(face_x + 28)
                drop_y = int(face_y - 14)
                
                # Draw teardrop shape - combination of circle bottom and triangle top
                # Bottom circle (the rounded part)
                pygame.draw.circle(self.screen, sweat_color, (drop_x, drop_y), 6)
                
                # Top triangle/cone that connects smoothly to circle
                # Draw multiple triangles to create smooth transition
                for i in range(6):
                    width = 6 - i  # Gradually narrow from circle width to point
                    y_offset = i * 2
                    pygame.draw.polygon(self.screen, sweat_color, [
                        (drop_x, drop_y - 6 - y_offset - 2),  # Top point (gets higher)
                        (drop_x - width, drop_y - y_offset),  # Left base
                        (drop_x + width, drop_y - y_offset)   # Right base
                    ])
                
                # Add white highlight for glossy effect
                pygame.draw.circle(self.screen, WHITE, (drop_x - 2, drop_y - 2), 2)
                pygame.draw.circle(self.screen, (200, 230, 255), (drop_x - 1, drop_y - 4), 1)
            
            elif mood == 'proud':
                # Confident eyes - scaled up
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, WHITE, (int(face_x - 13), int(face_y - 2)), 2)
                pygame.draw.circle(self.screen, WHITE, (int(face_x + 17), int(face_y - 2)), 2)
                # Smug smile - draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 7), 28, 14)
                pygame.draw.arc(self.screen, eye_color, rect, math.pi * 1.2, math.pi * 1.8, 3)
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]-1, rect[2], rect[3]), math.pi * 1.2, math.pi * 1.8, 3)
                # Raised eyebrow effect - draw multiple passes to fill gaps
                left_brow_rect = (int(face_x - 20), int(face_y - 7), 14, 7)
                right_brow_rect = (int(face_x + 6), int(face_y - 7), 14, 7)
                pygame.draw.arc(self.screen, eye_color, left_brow_rect, 0, math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, (left_brow_rect[0], left_brow_rect[1]+1, left_brow_rect[2], left_brow_rect[3]), 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, right_brow_rect, 0, math.pi, 2)
                pygame.draw.arc(self.screen, eye_color, (right_brow_rect[0], right_brow_rect[1]+1, right_brow_rect[2], right_brow_rect[3]), 0, math.pi, 3)
            
            elif mood == 'disappointed':
                # Sad droopy eyes - draw multiple passes to fill gaps
                left_eye_rect = (int(face_x - 18), int(face_y + 2), 10, 7)
                right_eye_rect = (int(face_x + 8), int(face_y + 2), 10, 7)
                pygame.draw.arc(self.screen, eye_color, left_eye_rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (left_eye_rect[0], left_eye_rect[1]+1, left_eye_rect[2], left_eye_rect[3]), 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, right_eye_rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (right_eye_rect[0], right_eye_rect[1]+1, right_eye_rect[2], right_eye_rect[3]), 0, math.pi, 3)
                # Frown - draw multiple passes to fill gaps
                rect = (int(face_x - 14), int(face_y + 18), 28, 14)
                pygame.draw.arc(self.screen, eye_color, rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, (rect[0], rect[1]+1, rect[2], rect[3]), 0, math.pi, 3)
                # Tear drop animation - scaled up
                if self.pond_buddy['animation_frame'] == 0:
                    pygame.draw.circle(self.screen, (135, 206, 250), (int(face_x - 20), int(face_y + 5)), 3)
                else:
                    pygame.draw.circle(self.screen, (135, 206, 250), (int(face_x - 20), int(face_y + 10)), 3)
            
            elif mood == 'worried':
                # Worried expression - raised eyebrows and wavy mouth
                # Wide concerned eyes
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 15), int(face_y)), 5)
                pygame.draw.circle(self.screen, WHITE, (int(face_x - 13), int(face_y - 1)), 2)
                pygame.draw.circle(self.screen, WHITE, (int(face_x + 17), int(face_y - 1)), 2)
                
                # Raised worried eyebrows (tilted)
                left_brow_rect = (int(face_x - 18), int(face_y - 8), 12, 6)
                right_brow_rect = (int(face_x + 6), int(face_y - 8), 12, 6)
                pygame.draw.arc(self.screen, eye_color, left_brow_rect, math.pi * 0.2, math.pi * 0.8, 3)
                pygame.draw.arc(self.screen, eye_color, right_brow_rect, math.pi * 0.2, math.pi * 0.8, 3)
                
                # Wavy worried mouth - lowered
                pygame.draw.line(self.screen, eye_color, (int(face_x - 10), int(face_y + 18)), (int(face_x - 5), int(face_y + 16)), 3)
                pygame.draw.line(self.screen, eye_color, (int(face_x - 5), int(face_y + 16)), (int(face_x), int(face_y + 18)), 3)
                pygame.draw.line(self.screen, eye_color, (int(face_x), int(face_y + 18)), (int(face_x + 5), int(face_y + 16)), 3)
                pygame.draw.line(self.screen, eye_color, (int(face_x + 5), int(face_y + 16)), (int(face_x + 10), int(face_y + 18)), 3)
        else:
            # Fallback if no sprite is loaded - draw simple circle buddy
            body_color = (101, 67, 33)  # Brown
            pygame.draw.circle(self.screen, body_color, (int(x), int(y)), 25)
            pygame.draw.circle(self.screen, (139, 90, 43), (int(x), int(y)), 25, 3)  # Border
            # Simple neutral face
            pygame.draw.circle(self.screen, (0, 0, 0), (int(x - 8), int(y - 5)), 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(x + 8), int(y - 5)), 3)
