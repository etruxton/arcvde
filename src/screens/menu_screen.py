"""
Main menu screen with camera feed and finger gun interaction
"""

# Standard library imports
import math
import os
import random
import time
from typing import Optional

# Third-party imports
import cv2
import pygame

# Local application imports
from game.enemy import Enemy
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    DEFAULT_CAMERA_ID,
    GAME_STATE_ARCADE,
    GAME_STATE_CAPYBARA_HUNT,
    GAME_STATE_INSTRUCTIONS,
    GAME_STATE_PLAYING,
    GAME_STATE_SETTINGS,
    GRAY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_BACKGROUND,
    UI_TEXT,
    VAPORWAVE_CYAN,
    VAPORWAVE_DARK,
    VAPORWAVE_LIGHT,
    VAPORWAVE_PINK,
    VAPORWAVE_PURPLE,
)
from utils.sound_manager import get_sound_manager
from utils.ui_components import Button


class MenuScreen(BaseScreen):
    """Main menu screen"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Initialize sound manager
        self.sound_manager = get_sound_manager()

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)  # Reduced default size for better fit
        self.info_font = pygame.font.Font(None, 24)

        # Pond buddy under the red triangle enemy (right side but not far edge)
        self.pond_buddy = {
            "x": SCREEN_WIDTH - 300,  # Right side but with space from edge
            "y": SCREEN_HEIGHT - 120,
            "mood": "neutral",
            "mood_timer": 0,
            "mood_duration": 2.0,
            "bob_time": 0,
            "bob_offset": 0,
            "animation_timer": 0,
            "animation_frame": 0,
            "sprite": None,
        }

        # Load pond buddy sprite
        try:
            self.pond_buddy["sprite"] = pygame.image.load("assets/pond_buddy.png").convert_alpha()
            # Scale it bigger for menu
            self.pond_buddy["sprite"] = pygame.transform.scale(self.pond_buddy["sprite"], (120, 120))
        except Exception as e:
            print(f"Could not load pond buddy sprite: {e}")
            self.pond_buddy["sprite"] = None

        # Create buttons
        button_width = 250
        button_height = 50  # Reduced height to fit more buttons
        button_spacing = 15  # Reduced spacing
        start_y = SCREEN_HEIGHT // 2 - 130  # Adjusted start position
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        self.arcade_button = Button(center_x, start_y, button_width, button_height, "DOOMSDAY", self.button_font)

        self.capybara_button = Button(
            center_x,
            start_y + 2 * (button_height + button_spacing),
            button_width,
            button_height,
            "CAPYBARA HUNT",
            self.button_font,
        )

        self.play_button = Button(
            center_x,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "TARGET PRACTICE",
            self.button_font,
        )

        self.instructions_button = Button(
            center_x,
            start_y + 3 * (button_height + button_spacing),
            button_width,
            button_height,
            "HOW TO PLAY",
            self.button_font,
        )

        self.settings_button = Button(
            center_x, start_y + 4 * (button_height + button_spacing), button_width, button_height, "SETTINGS", self.button_font
        )

        self.quit_button = Button(
            center_x, start_y + 5 * (button_height + button_spacing), button_width, button_height, "QUIT", self.button_font
        )

        self.buttons = [
            self.arcade_button,
            self.play_button,
            self.capybara_button,
            self.instructions_button,
            self.settings_button,
            self.quit_button,
        ]

        # Camera setup
        if not self.camera_manager.current_camera:
            self.camera_manager.initialize_camera(DEFAULT_CAMERA_ID)

        # Enemy showcase
        self.showcase_enemies = []
        self.init_enemy_showcase()

        # Capybara showcase
        self.init_capybara_showcase()

        self.logo = None
        self.load_logo()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        # Handle button events (mouse clicks)
        for button in self.buttons:
            if button.handle_event(event):
                return self._handle_button_action(button)

        # Handle keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return GAME_STATE_ARCADE
            elif event.key == pygame.K_2:
                return GAME_STATE_CAPYBARA_HUNT
            elif event.key == pygame.K_3:
                return GAME_STATE_PLAYING
            elif event.key == pygame.K_ESCAPE:
                return "quit"

        return None

    def _handle_button_action(self, button) -> str:
        """Handle button action - centralized logic"""
        # Play sound effect when button is clicked
        self.sound_manager.play("shoot")

        result = None
        if button == self.play_button:
            result = GAME_STATE_PLAYING
        elif button == self.arcade_button:
            result = GAME_STATE_ARCADE
        elif button == self.capybara_button:
            result = GAME_STATE_CAPYBARA_HUNT
        elif button == self.settings_button:
            result = GAME_STATE_SETTINGS
        elif button == self.instructions_button:
            result = GAME_STATE_INSTRUCTIONS
        elif button == self.quit_button:
            result = "quit"

        return result

    def init_enemy_showcase(self):
        """Initialize enemies for showcase display"""
        # Create enemies in two rows to avoid button overlap
        # Front row: zombie and giant (larger, more visible)
        # Back row: skull and demon (behind and offset)

        # Front row enemies
        zombie = Enemy(-0.65, 0.4, "zombie")  # Left front
        zombie.animation_time = 0
        self.showcase_enemies.append(zombie)

        giant = Enemy(0.65, 0.4, "giant")  # Right front
        giant.animation_time = math.pi
        self.showcase_enemies.append(giant)

        # Back row enemies (further back and offset to be visible)
        skull = Enemy(-0.45, 0.7, "skull")  # Left back, slightly inward
        skull.animation_time = math.pi / 2
        self.showcase_enemies.append(skull)

        demon = Enemy(0.45, 0.7, "demon")  # Right back, slightly inward
        demon.animation_time = math.pi * 1.5
        self.showcase_enemies.append(demon)

    def init_capybara_showcase(self):
        """Initialize capybara for showcase display"""
        # Load capybara sprites
        self.capybara_sprites = []
        try:
            sprite_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "running_capybara"
            )
            for i in range(5):  # Load frames 0-4
                sprite_path = os.path.join(sprite_dir, f"running-capybara-{i}.png")
                if os.path.exists(sprite_path):
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    # Scale to appropriate size for menu (same as in game)
                    sprite = pygame.transform.scale(sprite, (80, 80))
                    self.capybara_sprites.append(sprite)
                    print(f"Loaded capybara sprite: {sprite_path}")
                else:
                    print(f"Capybara sprite not found: {sprite_path}")
        except Exception as e:
            print(f"Error loading capybara sprites: {e}")
            self.capybara_sprites = []

        # Capybara position and animation state
        self.capybara_x = 150  # Top left area
        self.capybara_y = 150
        self.capybara_float_time = 0
        self.capybara_animation_frame = 0
        self.capybara_animation_time = 0
        self.capybara_balloon_color = (255, 100, 100)  # Red balloon

    def load_logo(self):
        """Load the game logo image"""
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "ARCVDE-3.png")
            if os.path.exists(logo_path):
                self.logo = pygame.image.load(logo_path).convert_alpha()
                logo_width = 500
                logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
                self.logo = pygame.transform.scale(self.logo, (logo_width, logo_height))
                print(f"Logo loaded successfully from {logo_path}")
            else:
                print(f"Logo file not found at {logo_path}")
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo = None

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update menu state"""
        # Process hand tracking
        self.process_finger_gun_tracking()

        # Update showcase enemies
        for enemy in self.showcase_enemies:
            # Just update their animation time for idle animations
            enemy.animation_time += dt * 2
            enemy.walk_cycle += dt * 4

        # Update capybara animation
        if self.capybara_sprites:
            self.capybara_float_time += dt
            self.capybara_animation_time += dt

            # Update animation frame
            if self.capybara_animation_time > 0.15:  # Change frame every 0.15 seconds
                self.capybara_animation_time = 0
                self.capybara_animation_frame = (self.capybara_animation_frame + 1) % len(self.capybara_sprites)

        # Update pond buddy
        self._update_pond_buddy(dt)

        # Check if hovering over any game button
        hovering_game_button = False
        hovering_capybara = False
        for button in [self.arcade_button, self.play_button, self.capybara_button]:
            if button.finger_aimed:
                hovering_game_button = True
                if button == self.capybara_button:
                    hovering_capybara = True
                break

        # Pond buddy reacts to hovering
        if hovering_game_button:
            if self.pond_buddy["mood"] == "neutral":
                if hovering_capybara:
                    self._set_pond_buddy_mood("celebration", 3.0)  # Extra excited for capybara hunt!
                else:
                    self._set_pond_buddy_mood("excited", 2.0)
        else:
            # Not hovering - return to neutral if in an excited state
            if self.pond_buddy["mood"] in ["excited", "celebration"]:
                self._set_pond_buddy_mood("neutral", 0)

        # Handle finger gun shooting as clicks
        shot_button = self.check_button_shoot(self.buttons)
        if shot_button:
            return self._handle_button_action(shot_button)

        return None

    def draw(self) -> None:
        """Draw the menu screen"""
        # Clear screen with vaporwave background
        self.screen.fill(UI_BACKGROUND)

        # Draw gradient background similar to game
        self._draw_menu_background()

        # Draw enemy showcase
        self._draw_enemy_showcase()

        # Draw capybara showcase
        self._draw_capybara_showcase()

        # Draw semi-transparent overlay for UI readability (reduced opacity)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(40)  # Reduced from 100 to 40 for more vibrant enemies
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if self.logo:
            logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(self.logo, logo_rect)
        else:
            # Draw title with vaporwave glow effect
            title_y = 100

            # Multi-layer glow effect
            glow_layers = [
                (VAPORWAVE_PINK, 6, 30),  # Outer pink glow
                (VAPORWAVE_CYAN, 4, 50),  # Mid cyan glow
                (VAPORWAVE_PURPLE, 2, 70),  # Inner purple glow
            ]

            for glow_color, radius, alpha in glow_layers:
                glow_text = self.title_font.render("ARCVDE", True, glow_color)

                for x_offset in range(-radius, radius + 1):
                    for y_offset in range(-radius, radius + 1):
                        if x_offset * x_offset + y_offset * y_offset <= radius * radius:
                            glow_rect = glow_text.get_rect(center=(SCREEN_WIDTH // 2 + x_offset, title_y + y_offset))

                            # Create alpha surface for this glow layer
                            glow_surface = pygame.Surface(glow_text.get_size(), pygame.SRCALPHA)
                            glow_surface.blit(glow_text, (0, 0))
                            glow_surface.set_alpha(alpha)
                            self.screen.blit(glow_surface, glow_rect)

            # Main title text
            title_text = self.title_font.render("ARCVDE", True, VAPORWAVE_LIGHT)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, title_y))
            self.screen.blit(title_text, title_rect)

        # Update finger aiming states and draw buttons
        self.update_button_finger_states(self.buttons)
        for button in self.buttons:
            button.draw(self.screen)

        # Draw pond buddy in bottom right
        self._draw_pond_buddy()

        # Draw crosshair if aiming
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        self.draw_shoot_animation()

        # Draw camera feed
        self.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

        # Draw debug overlay if enabled
        if self.settings_manager.get("debug_mode", False):
            self.draw_debug_overlay()

    def _draw_menu_background(self):
        """Draw vaporwave atmospheric background for menu"""
        # Create vaporwave gradient from dark purple at top to dark cyan at bottom
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT

            # Interpolate between dark purple and dark cyan
            r = int(VAPORWAVE_DARK[0] + progress * (10 - VAPORWAVE_DARK[0]))
            g = int(VAPORWAVE_DARK[1] + progress * (40 - VAPORWAVE_DARK[1]))
            b = int(VAPORWAVE_DARK[2] + progress * (60 - VAPORWAVE_DARK[2]))

            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

        # Add retro grid lines with vaporwave colors
        horizon_y = int(SCREEN_HEIGHT * 0.6)

        # Horizontal grid lines
        for i in range(10):
            y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (i / 10) ** 0.8
            alpha = max(20, 60 - i * 5)
            grid_color = (*VAPORWAVE_CYAN[:3], alpha)

            # Create surface for alpha blending
            line_surface = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
            line_surface.fill(grid_color)
            self.screen.blit(line_surface, (0, int(y)))

        # Vertical perspective lines
        for i in range(-8, 9):
            x_start = SCREEN_WIDTH // 2 + i * 120
            x_end = SCREEN_WIDTH // 2 + i * 40
            alpha = max(15, 50 - abs(i) * 3)
            grid_color = (*VAPORWAVE_PINK[:3], alpha)

            # Draw with alpha
            line_surface = pygame.Surface((2, SCREEN_HEIGHT - horizon_y), pygame.SRCALPHA)
            line_surface.fill(grid_color)

            # Calculate line positions
            if 0 <= x_start < SCREEN_WIDTH or 0 <= x_end < SCREEN_WIDTH:
                pygame.draw.line(self.screen, VAPORWAVE_PURPLE, (x_start, SCREEN_HEIGHT), (x_end, horizon_y), 1)

    def _draw_enemy_showcase(self):
        """Draw animated enemies in the background"""
        # Draw enemies
        for enemy in self.showcase_enemies:
            # Draw with full detail
            enemy.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT, debug_hitbox=False)

            # Add subtle glow effect around each enemy
            x, y = enemy.get_screen_position(SCREEN_WIDTH, SCREEN_HEIGHT)
            size = enemy.get_size()

            # Create pulsing glow
            glow_size = size + int(math.sin(enemy.animation_time) * 10)
            glow_surface = pygame.Surface((glow_size * 3, glow_size * 3), pygame.SRCALPHA)

            # Color based on enemy type
            glow_colors = {
                "zombie": (0, 100, 0, 30),
                "demon": (100, 0, 0, 30),
                "skull": (100, 100, 200, 30),
                "giant": (100, 0, 100, 30),
            }
            glow_color = glow_colors.get(enemy.enemy_type, (100, 100, 100, 30))

            pygame.draw.circle(glow_surface, glow_color, (glow_size * 3 // 2, glow_size * 3 // 2), glow_size)
            self.screen.blit(glow_surface, (x - glow_size * 3 // 2, y - glow_size * 3 // 2))

    def _draw_capybara_showcase(self):
        """Draw animated capybara with balloon in the background"""
        if not self.capybara_sprites:
            return

        # Calculate floating motion
        float_offset = math.sin(self.capybara_float_time * 2) * 10

        # Draw balloon string
        balloon_x = self.capybara_x
        balloon_y = self.capybara_y - 60 + float_offset
        capybara_center_x = self.capybara_x
        capybara_center_y = self.capybara_y + 20 + float_offset

        # Draw multiple string segments for curve effect
        prev_x = prev_y = None
        for i in range(5):
            t = i / 4
            # Bezier curve for string
            control_x = capybara_center_x + math.sin(self.capybara_float_time * 3 + i) * 5
            control_y = (balloon_y + capybara_center_y) / 2

            x1 = capybara_center_x * (1 - t) + control_x * t
            y1 = capybara_center_y * (1 - t) + control_y * t

            x2 = control_x * (1 - t) + balloon_x * t
            y2 = control_y * (1 - t) + balloon_y * t

            x = x1 * (1 - t) + x2 * t
            y = y1 * (1 - t) + y2 * t

            if i > 0 and prev_x is not None:
                pygame.draw.line(self.screen, (100, 100, 100), (prev_x, prev_y), (x, y), 2)
            prev_x, prev_y = x, y

        # Draw balloon (bigger to match capybara)
        pygame.draw.circle(self.screen, self.capybara_balloon_color, (int(balloon_x), int(balloon_y)), 35)
        # Balloon highlight
        highlight_x = balloon_x - 10
        highlight_y = balloon_y - 10
        pygame.draw.circle(self.screen, (255, 255, 255), (int(highlight_x), int(highlight_y)), 10)

        # Draw capybara sprite
        current_sprite = self.capybara_sprites[self.capybara_animation_frame]
        capybara_rect = current_sprite.get_rect(center=(int(capybara_center_x), int(capybara_center_y)))
        self.screen.blit(current_sprite, capybara_rect)

    def _update_pond_buddy(self, dt: float):
        """Update pond buddy animations and mood"""
        # Update mood timer
        if self.pond_buddy["mood_timer"] > 0:
            self.pond_buddy["mood_timer"] -= dt
            if self.pond_buddy["mood_timer"] <= 0:
                self.pond_buddy["mood"] = "neutral"

        # Random idle animations when neutral
        # Standard library imports
        import random

        if self.pond_buddy["mood"] == "neutral" and random.random() < 0.005:
            idle_moods = ["happy", "excited"]
            self._set_pond_buddy_mood(random.choice(idle_moods), random.uniform(1.0, 2.0))

        # Bobbing animation
        self.pond_buddy["bob_time"] += dt
        self.pond_buddy["bob_offset"] = math.sin(self.pond_buddy["bob_time"] * 2) * 3

        # Animation frame update
        self.pond_buddy["animation_timer"] += dt
        if self.pond_buddy["animation_timer"] > 0.2:
            self.pond_buddy["animation_timer"] = 0
            self.pond_buddy["animation_frame"] = (self.pond_buddy["animation_frame"] + 1) % 2

    def _set_pond_buddy_mood(self, mood: str, duration: float = 2.0):
        """Set the pond buddy's mood"""
        self.pond_buddy["mood"] = mood
        self.pond_buddy["mood_timer"] = duration
        self.pond_buddy["animation_frame"] = 0

    def _draw_pond_buddy(self):
        """Draw the pond companion"""
        x = self.pond_buddy["x"]
        y = self.pond_buddy["y"] + self.pond_buddy["bob_offset"]
        mood = self.pond_buddy["mood"]

        # Draw sprite if loaded
        if self.pond_buddy["sprite"]:
            sprite_rect = self.pond_buddy["sprite"].get_rect()
            sprite_rect.center = (int(x), int(y))
            self.screen.blit(self.pond_buddy["sprite"], sprite_rect)

            # Draw simple facial expressions
            # Adjusted for 120x120 sprite size, positioned higher
            face_x = x + 3
            face_y = y - 20  # Much higher on the face

            eye_color = (0, 0, 0)
            WHITE = (255, 255, 255)

            if mood == "neutral":
                # Normal eyes
                pygame.draw.circle(self.screen, eye_color, (int(face_x - 18), int(face_y)), 5)
                pygame.draw.circle(self.screen, eye_color, (int(face_x + 18), int(face_y)), 5)

            elif mood == "happy":
                # Happy eyes (curved)
                left_eye_rect = (int(face_x - 24), int(face_y - 3), 15, 15)
                right_eye_rect = (int(face_x + 9), int(face_y - 3), 15, 15)
                pygame.draw.arc(self.screen, eye_color, left_eye_rect, 0, math.pi, 3)
                pygame.draw.arc(self.screen, eye_color, right_eye_rect, 0, math.pi, 3)
                # Smile
                smile_rect = (int(face_x - 16), int(face_y + 10), 32, 18)
                pygame.draw.arc(self.screen, eye_color, smile_rect, math.pi, 2 * math.pi, 3)

            elif mood == "excited":
                # Star eyes
                if self.pond_buddy["animation_frame"] == 0:
                    # Wide eyes
                    pygame.draw.circle(self.screen, eye_color, (int(face_x - 18), int(face_y)), 7)
                    pygame.draw.circle(self.screen, eye_color, (int(face_x + 18), int(face_y)), 7)
                    pygame.draw.circle(self.screen, WHITE, (int(face_x - 15), int(face_y - 3)), 3)
                    pygame.draw.circle(self.screen, WHITE, (int(face_x + 21), int(face_y - 3)), 3)
                else:
                    # Sparkle effect
                    pygame.draw.circle(self.screen, (255, 215, 0), (int(face_x - 18), int(face_y)), 6)
                    pygame.draw.circle(self.screen, (255, 215, 0), (int(face_x + 18), int(face_y)), 6)
                # Big smile
                smile_rect = (int(face_x - 20), int(face_y + 10), 40, 20)
                pygame.draw.arc(self.screen, eye_color, smile_rect, math.pi, 2 * math.pi, 3)

            elif mood == "celebration":
                # Jumping animation
                jump_offset = abs(math.sin(self.pond_buddy["animation_timer"] * 10)) * 5
                face_y -= jump_offset

                # Star eyes
                for eye_x in [-18, 18]:
                    cx = int(face_x + eye_x)
                    cy = int(face_y)
                    # Draw star shape
                    for angle in range(0, 360, 72):
                        rad = math.radians(angle)
                        x1 = cx + math.cos(rad) * 8
                        y1 = cy + math.sin(rad) * 8
                        x2 = cx + math.cos(rad + math.radians(36)) * 4
                        y2 = cy + math.sin(rad + math.radians(36)) * 4
                        pygame.draw.line(self.screen, (255, 215, 0), (cx, cy), (int(x1), int(y1)), 2)

                # Huge smile
                smile_rect = (int(face_x - 22), int(face_y + 8), 44, 24)
                pygame.draw.arc(self.screen, eye_color, smile_rect, math.pi, 2 * math.pi, 3)

                # Party hat
                hat_color = (255, 20, 147) if self.pond_buddy["animation_frame"] == 0 else (16, 231, 245)
                pygame.draw.polygon(
                    self.screen,
                    hat_color,
                    [
                        (int(face_x), int(face_y - 50)),
                        (int(face_x - 25), int(face_y - 15)),
                        (int(face_x + 25), int(face_y - 15)),
                    ],
                )
                # Hat pompom
                pygame.draw.circle(self.screen, (255, 255, 255), (int(face_x), int(face_y - 50)), 6)
