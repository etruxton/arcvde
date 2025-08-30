# Standard library imports
import math
import random
from typing import Dict, Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from utils.constants import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE


class StageManager:
    """Manages stage themes, transitions, backgrounds, and effects for Doomsday mode"""

    def __init__(self, sound_manager, screen_shake_callback=None):
        self.sound_manager = sound_manager
        self.screen_shake_callback = screen_shake_callback

        # Current stage state
        self.current_stage_theme = 1
        self.current_stage_ambient = None
        self.current_music_track = None
        self.stage4_alternating_mode = False
        self.music_started = False

        # Stage transition system
        self.stage_transition_active = False
        self.stage_transition_time = 0
        self.stage_transition_duration = 1.5  # 1.5 seconds
        self.stage_transition_type = "fade"  # fade, slide, flash
        self.old_background = None
        self.new_background = None

        # Stage color themes
        self.stage_themes = {
            1: {  # Stage 1-2: Classic Doom brown/gray
                "sky_base": (30, 20, 20),
                "sky_end": (50, 35, 35),
                "ground_base": (40, 30, 25),
                "ground_end": (70, 50, 40),
                "horizon": (60, 40, 40),
                "grid": (40, 30, 30),
            },
            2: {  # Stage 3-4: Hellish red
                "sky_base": (40, 10, 10),
                "sky_end": (80, 20, 20),
                "ground_base": (60, 20, 15),
                "ground_end": (100, 40, 30),
                "horizon": (120, 30, 30),
                "grid": (60, 20, 20),
            },
            3: {  # Stage 5-6: Demonic purple/dark
                "sky_base": (20, 10, 30),
                "sky_end": (40, 20, 60),
                "ground_base": (30, 15, 40),
                "ground_end": (60, 30, 80),
                "horizon": (80, 40, 100),
                "grid": (40, 20, 50),
            },
            4: {  # Stage 7+: Apocalyptic orange/black
                "sky_base": (30, 15, 5),
                "sky_end": (60, 30, 10),
                "ground_base": (40, 20, 5),
                "ground_end": (80, 40, 15),
                "horizon": (100, 50, 20),
                "grid": (50, 25, 10),
            },
        }

        # Background surfaces
        self.background = None
        self.create_background()

        # Start initial stage music (temporarily disabled for debugging)
        # if hasattr(self.sound_manager, 'play_stage_music'):
        #     self._start_stage_music(1)

        # Stage names and metadata
        self.stage_names = {1: "The Beginning", 2: "Hell's Gates", 3: "Demon Realm", 4: "Final Apocalypse"}

        self.stage_transition_names = {
            1: "RETURNING TO THE BEGINNING",
            2: "ENTERING HELL'S GATES",
            3: "DESCENDING TO DEMON REALM",
            4: "THE FINAL APOCALYPSE BEGINS",
        }

    def create_background(self):
        """Create a doom-like background with gradient based on current stage"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        theme = self.stage_themes.get(self.current_stage_theme, self.stage_themes[1])

        for y in range(SCREEN_HEIGHT):
            if y < SCREEN_HEIGHT * 0.4:  # Sky
                sky_progress = y / (SCREEN_HEIGHT * 0.4)
                color = (
                    int(theme["sky_base"][0] + (theme["sky_end"][0] - theme["sky_base"][0]) * sky_progress),
                    int(theme["sky_base"][1] + (theme["sky_end"][1] - theme["sky_base"][1]) * sky_progress),
                    int(theme["sky_base"][2] + (theme["sky_end"][2] - theme["sky_base"][2]) * sky_progress),
                )
            else:  # Ground
                ground_progress = (y - SCREEN_HEIGHT * 0.4) / (SCREEN_HEIGHT * 0.6)
                color = (
                    int(theme["ground_base"][0] + (theme["ground_end"][0] - theme["ground_base"][0]) * ground_progress),
                    int(theme["ground_base"][1] + (theme["ground_end"][1] - theme["ground_base"][1]) * ground_progress),
                    int(theme["ground_base"][2] + (theme["ground_end"][2] - theme["ground_base"][2]) * ground_progress),
                )

            pygame.draw.line(self.background, color, (0, y), (SCREEN_WIDTH, y))

        # Draw horizon line
        horizon_y = int(SCREEN_HEIGHT * 0.4)
        pygame.draw.line(self.background, theme["horizon"], (0, horizon_y), (SCREEN_WIDTH, horizon_y), 2)

        # Draw floor grid
        self._draw_floor_grid(theme)

    def _draw_floor_grid(self, theme):
        """Draw 3D floor grid for perspective"""
        grid_color = theme["grid"]
        horizon_y = int(SCREEN_HEIGHT * 0.4)

        # Vertical lines (perspective) - converge toward center
        for i in range(-10, 11):
            x_start = SCREEN_WIDTH // 2 + i * 100  # Wide at bottom
            x_end = SCREEN_WIDTH // 2 + i * 20  # Narrow at horizon
            pygame.draw.line(self.background, grid_color, (x_start, SCREEN_HEIGHT), (x_end, horizon_y), 1)

        # Horizontal lines (depth) - use power function for perspective
        for i in range(10):
            y = horizon_y + (SCREEN_HEIGHT - horizon_y) * (i / 10) ** 0.7
            pygame.draw.line(self.background, grid_color, (0, int(y)), (SCREEN_WIDTH, int(y)), 1)

    def update_stage_progression(self, wave_number: int) -> None:
        """Update stage theme based on wave progression"""
        new_theme = min(4, (wave_number - 1) // 2 + 1)

        if new_theme != self.current_stage_theme and not self.stage_transition_active:
            self._start_stage_transition(new_theme)

        if self.current_stage_theme >= 4 and self.stage4_alternating_mode:
            self._handle_stage4_music_alternation()

    def update(self, dt: float) -> None:
        """Update stage system each frame"""
        if self.stage_transition_active:
            self.stage_transition_time += dt
            if self.stage_transition_time >= self.stage_transition_duration:
                self._complete_stage_transition()

    def _start_stage_transition(self, new_theme: int) -> None:
        """Start a smooth transition to a new stage"""
        if self.stage_transition_active:
            return

        print(f"Starting stage transition from {self.current_stage_theme} to {new_theme}")

        # Store old background
        self.old_background = self.background.copy()
        old_theme = self.current_stage_theme
        self.current_stage_theme = new_theme

        # Create new background
        self.create_background()
        self.new_background = self.background.copy()

        # Restore old theme temporarily for transition
        self.current_stage_theme = old_theme

        # Choose transition type based on stage
        if new_theme == 2:
            self.stage_transition_type = "flash"  # Hell's gates - dramatic flash
        elif new_theme == 3:
            self.stage_transition_type = "fade"
        elif new_theme == 4:
            self.stage_transition_type = "slide"  # Final apocalypse - sliding destruction
        else:
            self.stage_transition_type = "fade"

        self.stage_transition_active = True
        self.stage_transition_time = 0

        # Trigger dramatic screen shake
        if self.screen_shake_callback:
            self.screen_shake_callback(1.0, 15)  # 1 second duration, intensity 15

        # Play transition sound effect
        if hasattr(self.sound_manager, "play_stage_transition"):
            self.sound_manager.play_stage_transition(new_theme)

        print(f"Starting stage transition from {old_theme} to {new_theme} with {self.stage_transition_type} effect")

    def draw_stage_transition(self, surface: pygame.Surface) -> None:
        """Draw the stage transition effect"""
        if not self.stage_transition_active or not self.old_background or not self.new_background:
            return

        progress = self.stage_transition_time / self.stage_transition_duration
        progress = min(1.0, progress)

        if self.stage_transition_type == "fade":
            # Cross-fade between backgrounds
            surface.blit(self.old_background, (0, 0))

            # Create alpha surface for new background
            alpha = int(255 * progress)
            temp_surface = self.new_background.copy()
            temp_surface.set_alpha(alpha)
            surface.blit(temp_surface, (0, 0))

            # Add some flash effects during fade
            if 0.3 < progress < 0.7:
                flash_alpha = int(100 * (0.5 - abs(progress - 0.5)) * 2)
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill((255, 255, 255))
                flash_surface.set_alpha(flash_alpha)
                surface.blit(flash_surface, (0, 0))

        elif self.stage_transition_type == "flash":
            # Dramatic flash effect for Hell's Gates
            if progress < 0.3:
                # Build up phase - show old background
                surface.blit(self.old_background, (0, 0))
            elif progress < 0.5:
                # Flash phase - intense white/red flash
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                if (progress * 10) % 1 < 0.5:  # Flicker effect
                    flash_surface.fill((255, 255, 255))  # Bright white
                else:
                    flash_surface.fill((255, 150, 150))  # Reddish flash
                surface.blit(flash_surface, (0, 0))
            elif progress < 0.8:
                # Reveal phase - show new background with effects
                surface.blit(self.new_background, (0, 0))
                # Add some lingering flash
                flash_alpha = int(150 * (0.8 - progress) / 0.3)
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill((255, 100, 100))
                flash_surface.set_alpha(flash_alpha)
                surface.blit(flash_surface, (0, 0))
            else:
                # Fade to normal
                surface.blit(self.new_background, (0, 0))

        elif self.stage_transition_type == "slide":
            # Sliding destruction effect with dramatic elements
            slide_offset = int(SCREEN_WIDTH * progress)

            # Old background slides out to left
            surface.blit(self.old_background, (-slide_offset, 0))
            # New background slides in from right
            surface.blit(self.new_background, (SCREEN_WIDTH - slide_offset, 0))

            # Add destruction particles during slide
            if 0.2 < progress < 0.8:
                # Standard library imports
                import random

                for _ in range(8):
                    x = random.randint(int(SCREEN_WIDTH * 0.3), int(SCREEN_WIDTH * 0.7))
                    y = random.randint(0, SCREEN_HEIGHT)
                    size = random.randint(3, 12)
                    color = random.choice([(255, 100, 0), (200, 50, 0), (150, 75, 25)])
                    pygame.draw.circle(surface, color, (x, y), size)

    def draw_stage_transition_text(self, surface: pygame.Surface, big_font: pygame.font.Font) -> None:
        """Draw dramatic text during stage transitions"""
        if not self.stage_transition_active:
            return

        # For direct jumps, use the target stage; for sequential progression, use current + 1
        if hasattr(self, "_direct_jump_target"):
            new_theme = self._direct_jump_target
        else:
            new_theme = min(4, (self.current_stage_theme + 1))

        stage_text = self.stage_transition_names.get(new_theme, "STAGE CHANGE")

        progress = self.stage_transition_time / self.stage_transition_duration

        if self.stage_transition_type == "flash":
            # Show text during flash phase
            if 0.4 < progress < 0.9:
                text_alpha = int(255 * min(1.0, (progress - 0.4) * 5))
                text_surface = big_font.render(stage_text, True, (255, 100, 0))
                text_surface.set_alpha(text_alpha)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                surface.blit(text_surface, text_rect)

        elif self.stage_transition_type == "fade":
            # Show text with fade effect
            if 0.2 < progress < 0.8:
                fade_progress = (progress - 0.2) / 0.6
                text_alpha = int(255 * (1 - abs(fade_progress - 0.5) * 2))
                text_surface = big_font.render(stage_text, True, (255, 100, 0))
                text_surface.set_alpha(text_alpha)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                surface.blit(text_surface, text_rect)

        elif self.stage_transition_type == "slide":
            # Text slides in with new background
            if progress > 0.3:
                text_x = int(SCREEN_WIDTH * (1 - progress) + SCREEN_WIDTH // 2)
                text_surface = big_font.render(stage_text, True, (255, 100, 0))
                glow_surface = big_font.render(stage_text, True, (255, 200, 100))

                # Add glow effect for sliding text
                glow_rect = glow_surface.get_rect(center=(text_x + 2, SCREEN_HEIGHT // 2 + 2))
                surface.blit(glow_surface, glow_rect)

                text_rect = text_surface.get_rect(center=(text_x, SCREEN_HEIGHT // 2))
                surface.blit(text_surface, text_rect)

    def get_stage_object_alpha(self) -> int:
        """Calculate alpha for stage objects during transitions"""
        if not self.stage_transition_active:
            return 255

        progress = self.stage_transition_time / self.stage_transition_duration

        # Fade out during first half, fade in during second half
        if progress < 0.5:
            return int(255 * (1 - progress * 2))
        else:
            return int(255 * ((progress - 0.5) * 2))

    def draw_stage_background_elements(self, surface: pygame.Surface) -> None:
        """Draw stage-specific background elements (mountains, structures, etc.)"""
        object_alpha = self.get_stage_object_alpha()

        if object_alpha <= 0:
            return

        # Create a temporary surface for stage elements
        stage_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        if self.current_stage_theme == 1:
            self._draw_stage1_elements(stage_surface)
        elif self.current_stage_theme == 2:
            self._draw_stage2_elements(stage_surface)
        elif self.current_stage_theme == 3:
            self._draw_stage3_elements(stage_surface)
        elif self.current_stage_theme == 4:
            self._draw_stage4_elements(stage_surface)

        # Apply alpha to the entire stage surface
        stage_surface.set_alpha(object_alpha)
        surface.blit(stage_surface, (0, 0))

    def _draw_stage1_elements(self, surface: pygame.Surface) -> None:
        """Draw Stage 1 background elements"""
        # Simple rocky formations and basic structures
        ground_y = int(SCREEN_HEIGHT * 0.4)

        # Draw some simple mountains/rocks
        for i in range(3):
            x = 100 + i * 200
            height = 80 + random.randint(-20, 20)
            points = [(x, ground_y), (x + 50, ground_y - height), (x + 100, ground_y)]
            pygame.draw.polygon(surface, (60, 50, 45), points)

    def _draw_stage2_elements(self, surface: pygame.Surface) -> None:
        """Draw Stage 2 (Hell's Gates) background elements"""
        ground_y = int(SCREEN_HEIGHT * 0.4)

        # Draw hellish structures and fire effects
        # Gate-like structures
        pygame.draw.rect(surface, (80, 40, 40), (50, ground_y - 120, 20, 120))
        pygame.draw.rect(surface, (80, 40, 40), (150, ground_y - 120, 20, 120))
        pygame.draw.rect(surface, (60, 30, 30), (70, ground_y - 140, 80, 20))

        # More structures across the background
        for i in range(4):
            x = 200 + i * 150
            pygame.draw.rect(surface, (70, 35, 35), (x, ground_y - 80, 15, 80))

    def _draw_stage3_elements(self, surface: pygame.Surface) -> None:
        """Draw Stage 3 (Demon Realm) background elements"""
        ground_y = int(SCREEN_HEIGHT * 0.4)

        # Draw demonic spires and twisted structures
        for i in range(5):
            x = 80 + i * 120
            height = 90 + random.randint(-30, 30)
            # Twisted spires
            points = [
                (x, ground_y),
                (x - 10, ground_y - height // 2),
                (x + 10, ground_y - height * 0.8),
                (x - 5, ground_y - height),
            ]
            pygame.draw.polygon(surface, (50, 30, 70), points)

    def _draw_stage4_elements(self, surface: pygame.Surface) -> None:
        """Draw Stage 4 (Final Apocalypse) background elements"""
        ground_y = int(SCREEN_HEIGHT * 0.4)

        # Draw apocalyptic ruins and destruction
        for i in range(6):
            x = 60 + i * 100
            height = 60 + random.randint(-20, 40)
            width = 30 + random.randint(-10, 10)

            # Broken structures
            pygame.draw.rect(surface, (70, 40, 20), (x, ground_y - height, width, height))
            # Add some "broken" tops
            if random.random() < 0.5:
                pygame.draw.polygon(
                    surface,
                    (50, 30, 15),
                    [(x, ground_y - height), (x + width // 3, ground_y - height - 15), (x + width, ground_y - height)],
                )

    def draw_stage_effects(self, surface: pygame.Surface) -> None:
        """Draw atmospheric effects based on current stage"""
        if self.stage_transition_active:
            return  # Skip effects during transitions

        object_alpha = self.get_stage_object_alpha()

        if self.current_stage_theme == 1:
            # Urban decay dust and debris particles
            self._draw_dust_effects(surface, object_alpha)
        elif self.current_stage_theme == 2:
            # Hell fire effects
            self._draw_fire_effects(surface, object_alpha)
        elif self.current_stage_theme == 3:
            # Demon realm mist/static
            self._draw_mist_effects(surface, object_alpha)
        elif self.current_stage_theme == 4:
            # Apocalyptic lightning/destruction
            self._draw_lightning_effects(surface, object_alpha)

    def _draw_dust_effects(self, surface: pygame.Surface, alpha: int) -> None:
        """Draw dust and debris effects for Urban Decay stage"""
        # Floating dust particles
        for i in range(3):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(int(SCREEN_HEIGHT * 0.4), SCREEN_HEIGHT)
            size = random.randint(1, 3)
            color = random.choice([(80, 70, 60), (90, 80, 70), (70, 65, 55)])
            pygame.draw.circle(surface, color, (x, y), size)

        # Occasional falling debris
        if random.random() < 0.005:  # 0.5% chance per frame
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(int(SCREEN_HEIGHT * 0.4), int(SCREEN_HEIGHT * 0.6))
            debris_size = random.randint(2, 5)
            debris_color = (60, 55, 45)
            pygame.draw.circle(surface, debris_color, (x, y), debris_size)

    def _draw_fire_effects(self, surface: pygame.Surface, alpha: int) -> None:
        """Draw fire effects for Hell's Gates stage - matches original implementation"""
        # Fire particles at bottom of screen
        for i in range(5):
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT - random.randint(0, 100)
            size = random.randint(2, 6)
            color = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0)])
            pygame.draw.circle(surface, color, (x, y), size)

            # Occasional fire crackling sound
            if size >= 5 and random.random() < 0.001:
                if hasattr(self.sound_manager, "play_one_shot_effect"):
                    self.sound_manager.play_one_shot_effect("stage2_fire_crackle", volume=0.05)

    def _draw_mist_effects(self, surface: pygame.Surface, alpha: int) -> None:
        """Draw mist effects for Demon Realm stage - matches original purple pixel particles"""
        # Create purple mist particles like original
        mist_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(3):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(int(SCREEN_HEIGHT * 0.4), SCREEN_HEIGHT)
            radius = random.randint(50, 150)
            # Draw filled circle with purple color and transparency
            mist_color = (100, 50, 150, 20)
            temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            temp_surface.fill(mist_color)
            mist_surface.blit(temp_surface, (x - radius, y - radius))
        surface.blit(mist_surface, (0, 0))

    def _draw_lightning_effects(self, surface: pygame.Surface, alpha: int) -> None:
        """Draw lightning effects for Final Apocalypse stage - matches original implementation"""
        # Occasional lightning
        if random.random() < 0.04:  # 4% chance per frame
            # Play lightning sound effect
            if hasattr(self.sound_manager, "play_one_shot_effect"):
                if random.random() < 0.7:
                    self.sound_manager.play_one_shot_effect("stage4_lightning", volume=0.4)
                else:
                    self.sound_manager.play_one_shot_effect("stage4_thunder", volume=0.3)

            # Draw actual lightning bolt
            lightning_x = random.randint(100, SCREEN_WIDTH - 100)
            current_x = lightning_x
            current_y = 0
            for i in range(10):
                next_x = current_x + random.randint(-30, 30)
                next_y = current_y + SCREEN_HEIGHT // 10
                # White outer lightning bolt
                pygame.draw.line(surface, (255, 255, 255), (current_x, current_y), (next_x, next_y), 3)
                # Blue-white inner glow
                pygame.draw.line(surface, (200, 200, 255), (current_x, current_y), (next_x, next_y), 1)
                current_x, current_y = next_x, next_y

    def _start_stage_music(self, stage: int) -> None:
        """Start the appropriate music for a given stage"""
        if stage >= 4:
            self.stage4_alternating_mode = True
            # Play tracks once to enable alternation
            self.current_music_track = self.sound_manager.get_stage_music(stage)
            self.sound_manager.play_stage_music(stage, loops=0)
        else:
            self.stage4_alternating_mode = False
            self.current_music_track = self.sound_manager.play_stage_music(stage, loops=-1)

        # Start stage-specific ambient effects
        if stage == 2:
            self.current_stage_ambient = "stage2_fire_ambient"
            self.sound_manager.play_stage_effect("stage2_fire_ambient", loops=-1, volume=0.08)
            print("Starting Stage 2 fire ambient")
        elif stage == 3:
            # Play static/mist ambient for Stage 3
            self.current_stage_ambient = "stage3_static_mist"
            self.sound_manager.play_stage_effect("stage3_static_mist", loops=-1, volume=0.2)
            print("Starting Stage 3 static ambient")
        elif stage >= 4:
            # No continuous ambient for Stage 4, just one-shot lightning
            self.current_stage_ambient = None
            self.sound_manager.stop_stage_effect()
        else:
            # Stop any stage effects for Stage 1
            self.current_stage_ambient = None
            self.sound_manager.stop_stage_effect()

    def _handle_stage4_music_alternation(self) -> None:
        """Handle the alternating music logic for Stage 4+"""
        # Check if current track finished, then switch to next
        if self.sound_manager.is_ambient_finished():
            # Get the next track in the alternating sequence
            next_track = self.sound_manager.get_next_stage4_track(self.current_music_track)
            print(f"Stage 4 music alternation: {self.current_music_track} -> {next_track}")

            self.current_music_track = next_track

            # Metal track loops indefinitely for enhanced intensity
            if next_track == "stage4_music3":
                self.sound_manager.play_ambient(next_track, loops=-1, fade_ms=1000)
            else:
                self.sound_manager.play_ambient(next_track, loops=0, fade_ms=1000)

            print(f"Now playing: {next_track}")

    def jump_to_stage(self, stage_number: int) -> Tuple[bool, str]:
        """Jump directly to a specific stage (for console commands)"""
        if stage_number < 1:
            return False, "Invalid stage number"

        # Calculate wave number from stage (2 waves per stage)
        wave_number = (stage_number - 1) * 2 + 1
        new_theme = min(4, stage_number)

        if new_theme != self.current_stage_theme:
            self._start_direct_stage_jump(new_theme)
        else:
            # If same stage, just update background without transition
            self.create_background()
            self._start_stage_music(new_theme)

        return True, f"Jumped to Stage {stage_number} (Wave {wave_number})"

    def _start_direct_stage_jump(self, target_theme: int) -> None:
        """Start a direct transition to any stage (for console commands)"""
        if self.stage_transition_active:
            return

        print(f"Direct stage jump from {self.current_stage_theme} to {target_theme}")

        # Store old background
        self.old_background = self.background.copy()

        # Create new background for target theme
        old_theme = self.current_stage_theme
        self.current_stage_theme = target_theme
        self.create_background()
        self.new_background = self.background.copy()

        # Temporarily restore old theme for transition display
        self.current_stage_theme = old_theme

        # Choose appropriate transition type based on target theme
        if target_theme == 2:
            self.stage_transition_type = "flash"
        elif target_theme == 3:
            self.stage_transition_type = "fade"
        elif target_theme == 4:
            self.stage_transition_type = "slide"
        else:
            self.stage_transition_type = "fade"

        self.stage_transition_active = True
        self.stage_transition_time = 0

        # Mark this as a direct jump so completion knows where to go
        self._direct_jump_target = target_theme

        # Trigger screen shake
        if self.screen_shake_callback:
            self.screen_shake_callback(1.0, 15)

        print(f"Starting direct jump transition to stage {target_theme} with {self.stage_transition_type} effect")

    def _complete_stage_transition(self) -> None:
        """Complete the stage transition"""
        # For direct jumps, set to the target theme directly
        # For sequential progression, increment by 1
        if hasattr(self, "_direct_jump_target"):
            self.current_stage_theme = self._direct_jump_target
            delattr(self, "_direct_jump_target")
        else:
            # Sequential progression
            self.current_stage_theme = min(4, (self.current_stage_theme + 1))

        self._start_stage_music(self.current_stage_theme)

        self.stage_transition_active = False
        self.stage_transition_time = 0

        # Clean up transition backgrounds
        self.old_background = None
        self.new_background = None

        print(f"Stage transition completed to theme {self.current_stage_theme}")

    def reset(self) -> None:
        """Reset stage system to initial state"""
        self.current_stage_theme = 1
        self.stage4_alternating_mode = False
        self.music_started = False
        self.current_stage_ambient = None
        self.sound_manager.stop_stage_effect()

        # Reset transition state
        self.stage_transition_active = False
        self.stage_transition_time = 0
        self.old_background = None
        self.new_background = None

        # Recreate background
        self.create_background()

    def get_stage_name(self) -> str:
        """Get the name of the current stage"""
        return self.stage_names.get(self.current_stage_theme, "Unknown")

    def get_wave_text(self, wave_number: int) -> str:
        """Get formatted wave text with stage name"""
        stage_name = self.get_stage_name()
        return f"Wave {wave_number}: {stage_name}"

    def should_show_stage_transition_text(self) -> bool:
        """Check if stage transition text should be displayed"""
        return self.stage_transition_active

    def get_background(self) -> pygame.Surface:
        """Get the current background surface"""
        return self.background
