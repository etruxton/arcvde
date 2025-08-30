"""
Comprehensive rendering system for Doomsday mode
"""

# Standard library imports
import math
import random
import time
from typing import Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from game.doomsday.ui_manager import DoomsdayUI
from utils.constants import (
    BLACK,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    CAMERA_X,
    CAMERA_Y,
    DARK_GRAY,
    GRAY,
    GREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)


class DoomsdayRenderer:
    """Handles all rendering for Doomsday game mode"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # Initialize fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        self.huge_font = pygame.font.Font(None, 96)

        # Initialize UI manager
        self.ui_manager = DoomsdayUI(screen)

    def draw_main_game(
        self,
        stage_manager,
        enemy_manager,
        base_screen,
        crosshair_pos: Optional[Tuple[int, int]],
        crosshair_color: Tuple[int, int, int],
        shoot_pos: Optional[Tuple[int, int]],
        shoot_animation_time: int,
        shoot_animation_duration: int,
        muzzle_flash_time: float,
        damage_flash_time: float,
        screen_shake_time: float,
        screen_shake_intensity: int,
        player_health: int,
        max_health: int,
        score: int,
        current_fps: int,
        debug_mode: bool,
    ) -> None:
        """Draw the main game screen with all elements"""

        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if screen_shake_time > 0:
            shake_offset_x = int((pygame.time.get_ticks() % 100 - 50) / 50 * screen_shake_intensity)
            shake_offset_y = int((pygame.time.get_ticks() % 117 - 58) / 58 * screen_shake_intensity)

        draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Draw background (stage manager handles this)
        draw_surface.blit(stage_manager.get_background(), (0, 0))

        # Draw stage transition effects if active (stage manager handles this)
        stage_manager.draw_stage_transition(draw_surface)

        # Draw stage transition text if active (stage manager handles this)
        stage_manager.draw_stage_transition_text(draw_surface, self.big_font)

        # Draw stage-specific background elements (detailed backgrounds)
        self._draw_stage_background(draw_surface, stage_manager, enemy_manager)

        # Stage background elements are now drawn directly in _draw_stage_background with exact original code
        # stage_manager.draw_stage_background_elements(draw_surface)  # Disabled - causes wiggling triangles

        # Draw meteors for Stage 4
        if stage_manager.current_stage_theme == 4:
            self.draw_meteors(draw_surface)

        # Draw stage effects (stage manager handles this - eliminates duplication)
        stage_manager.draw_stage_effects(draw_surface)

        # Draw enemies with blood physics
        enemy_manager.draw(draw_surface, debug_mode, dt=1.0 / 60.0)

        # Draw crosshair
        if crosshair_pos:
            self._draw_crosshair(draw_surface, crosshair_pos, crosshair_color, base_screen)

        # Draw shooting animation
        current_time = pygame.time.get_ticks()
        if shoot_pos and current_time - shoot_animation_time < shoot_animation_duration:
            self._draw_shoot_animation(draw_surface, shoot_pos, shoot_animation_time, shoot_animation_duration)

        # Draw muzzle flash
        if muzzle_flash_time > 0:
            self._draw_muzzle_flash(draw_surface, muzzle_flash_time)

        # Apply damage flash
        if damage_flash_time > 0:
            alpha = int(100 * (damage_flash_time / 0.3))
            self.ui_manager.draw_damage_flash(draw_surface, alpha)

        # Draw UI
        self._draw_ui(draw_surface, stage_manager, enemy_manager, player_health, max_health, score, current_fps, debug_mode)

        # Blit everything with shake
        self.screen.blit(draw_surface, (shake_offset_x, shake_offset_y))

    def draw_camera_feed(self, base_screen) -> None:
        """Draw camera feed in corner"""
        base_screen.draw_camera_with_tracking(CAMERA_X, CAMERA_Y, CAMERA_WIDTH, CAMERA_HEIGHT)

    def draw_meteors(self, surface: pygame.Surface) -> None:
        """Draw apocalyptic effects for Stage 4 - ORIGINAL IMPLEMENTATION"""
        draw_target = surface

        # 1. Falling meteors/debris
        for i in range(8):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, int(SCREEN_HEIGHT * 0.6))
            meteor_size = random.randint(3, 8)
            # Meteor core
            pygame.draw.circle(draw_target, (255, 100, 0), (x, y), meteor_size)
            # Fiery trail
            for j in range(5):
                trail_x = x - j * 3
                trail_y = y - j * 5
                trail_size = meteor_size - j
                if trail_size > 0:
                    color = (255 - j * 30, 50 + j * 20, 0)
                    pygame.draw.circle(draw_target, color, (trail_x, trail_y), trail_size)

        # 2. Ash particles falling
        for i in range(15):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(draw_target, (150, 150, 150), (x, y), 1)

        # 3. Intense lightning with screen flash
        if random.random() < 0.04:  # 4% chance
            # Draw actual lightning bolt
            lightning_x = random.randint(100, SCREEN_WIDTH - 100)
            current_x = lightning_x
            current_y = 0
            for i in range(10):
                next_x = current_x + random.randint(-30, 30)
                next_y = current_y + SCREEN_HEIGHT // 10
                pygame.draw.line(draw_target, (255, 255, 255), (current_x, current_y), (next_x, next_y), 3)
                pygame.draw.line(draw_target, (200, 200, 255), (current_x, current_y), (next_x, next_y), 1)
                current_x, current_y = next_x, next_y

            # Screen flash
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.set_alpha(60)
            flash_surface.fill((255, 200, 150))
            draw_target.blit(flash_surface, (0, 0))

        # 4. Dark smoke clouds at top
        smoke_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(4):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, int(SCREEN_HEIGHT * 0.3))
            radius = random.randint(40, 100)
            smoke_surface.fill((50, 30, 20, 30), (x - radius, y - radius, radius * 2, radius * 2))
        draw_target.blit(smoke_surface, (0, 0))

    def draw_pause_screen(
        self,
        console_active: bool,
        console_input: str,
        console_message: str,
        console_message_time: float,
    ) -> None:
        """Draw pause overlay - delegate to UI manager"""
        self.ui_manager.draw_pause_screen(self.screen, console_active, console_input, console_message, console_message_time)

    def draw_game_over_screen(self, surface: pygame.Surface, score: int, enemy_manager) -> None:
        """Draw game over screen - delegate to UI manager"""
        # Calculate time survived (placeholder - would need actual game time)
        time_survived = enemy_manager.wave_number * 30.0  # Rough estimate

        self.ui_manager.draw_game_over_screen(
            surface, score, enemy_manager.wave_number - 1, enemy_manager.total_kills, time_survived
        )

    def _draw_ui(
        self,
        surface: pygame.Surface,
        stage_manager,
        enemy_manager,
        player_health: int,
        max_health: int,
        score: int,
        current_fps: int,
        debug_mode: bool,
    ) -> None:
        """Draw game UI elements - delegate main HUD to UI manager"""
        # Draw main HUD through UI manager
        self.ui_manager.draw_hud(
            surface,
            stage_manager,
            enemy_manager,
            player_health,
            max_health,
            score,
            enemy_manager.wave_number,
            current_fps,
            debug_mode,
        )

        # Draw combo indicator (game-specific logic)
        if enemy_manager.current_combo > 1:
            self.ui_manager.draw_combo_indicator(surface, enemy_manager.current_combo, enemy_manager.combo_timer)

        # Draw wave completion status
        if enemy_manager.wave_complete:
            wave_complete_text = self.big_font.render(f"WAVE {enemy_manager.wave_number} COMPLETE!", True, (0, 255, 0))
            wave_rect = wave_complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(wave_complete_text, wave_rect)

            # Draw stage transition text if active
            if stage_manager.should_show_stage_transition_text():
                stage_manager.draw_stage_transition_text(surface, self.big_font)
            else:
                next_wave_text = self.font.render("Next wave starting...", True, WHITE)
                next_rect = next_wave_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                surface.blit(next_wave_text, next_rect)

        # Controls hint
        controls_text = self.small_font.render("ESC: Menu | P: Pause | R: Reset | D: Debug", True, GRAY)
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = SCREEN_WIDTH // 2
        controls_rect.y = SCREEN_HEIGHT - 30
        surface.blit(controls_text, controls_rect)

        # Debug info
        if debug_mode:
            debug_text = self.small_font.render("DEBUG MODE - Hitboxes Visible", True, (255, 0, 255))
            surface.blit(debug_text, (10, 120))

        # Danger indicator if enemies are close
        closest_distance = enemy_manager.get_closest_enemy_distance()
        if closest_distance < 0.3:
            danger_alpha = int(255 * (1 - closest_distance / 0.3))
            danger_surface = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
            danger_surface.fill((255, 0, 0, danger_alpha // 4))
            surface.blit(danger_surface, (0, 0))
            surface.blit(danger_surface, (0, SCREEN_HEIGHT - 60))

    def _draw_crosshair(self, surface: pygame.Surface, pos: Tuple[int, int], color: Tuple[int, int, int], base_screen) -> None:
        """Draw crosshair on surface - delegate to UI manager"""
        self.ui_manager.draw_crosshair(surface, pos, color)

    def _draw_shoot_animation(
        self, surface: pygame.Surface, pos: Tuple[int, int], shoot_animation_time: int, shoot_animation_duration: int
    ) -> None:
        """Draw shooting animation - simple target practice style"""
        current_time = pygame.time.get_ticks()
        time_since_shoot = current_time - shoot_animation_time
        animation_progress = time_since_shoot / shoot_animation_duration

        if animation_progress < 1.0:
            # Simple expanding circle animation - matches target practice
            radius = int(40 * animation_progress)
            alpha = int(255 * (1 - animation_progress))

            # Create surface for alpha blending
            if alpha > 0:
                shoot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shoot_surface, (*YELLOW, alpha), (radius, radius), radius, 3)
                pygame.draw.circle(shoot_surface, (*WHITE, alpha // 2), (radius, radius), radius // 2, 2)
                surface.blit(shoot_surface, (pos[0] - radius, pos[1] - radius))

    def _draw_muzzle_flash(self, surface: pygame.Surface, muzzle_flash_time: float) -> None:
        """Draw muzzle flash effect at bottom of screen"""
        flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 3), pygame.SRCALPHA)

        # Create radial gradient for muzzle flash
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 3

        for radius in range(0, SCREEN_HEIGHT // 3, 5):
            alpha = int(255 * (1 - radius / (SCREEN_HEIGHT // 3)) * (muzzle_flash_time / 0.1))
            if alpha > 0:
                pygame.draw.circle(flash_surface, (255, 200, 100, alpha), (center_x, center_y), radius)

        surface.blit(flash_surface, (0, SCREEN_HEIGHT - SCREEN_HEIGHT // 3))

    def _draw_stage_background(self, surface: pygame.Surface, stage_manager, enemy_manager) -> None:
        """Draw stage-specific background elements - EXACT original from doomsday_screen.py"""
        horizon_y = int(SCREEN_HEIGHT * 0.4)

        # Handle object visibility during transitions
        if stage_manager.stage_transition_active:
            progress = stage_manager.stage_transition_time / stage_manager.stage_transition_duration
            if progress < 0.6:  # Hide objects during first 60% of transition
                return  # Don't draw any objects
            # After 60%, we want to draw NEW stage objects
            # So we need to determine what the target theme should be
            target_theme = min(4, (enemy_manager.wave_number - 1) // 2 + 1)
        else:
            # Not in transition, use current theme
            target_theme = stage_manager.current_stage_theme

        draw_target = surface

        if target_theme == 1:
            # Stage 1: The Beginning

            for i in range(18):
                building_x = i * 70
                building_height = 60 + (i % 4) * 10
                building_width = 35 + (i % 3) * 5
                building_y = horizon_y - building_height + 10

                # Far building silhouette
                color = (35, 30, 30)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                max_floors = (building_height - 20) // 20
                max_windows_per_floor = (building_width - 10) // 12
                for floor in range(max_floors):
                    for window in range(max_windows_per_floor):
                        win_x = building_x + 5 + window * 12
                        win_y = building_y + 10 + floor * 20
                        if win_x + 6 <= building_x + building_width - 5:
                            # Use deterministic pattern for dark/lit windows
                            if (i + floor + window) % 3 == 0:
                                if int(pygame.time.get_ticks() / 500) % 2 == 0 or (i + floor) % 4 != 0:
                                    pygame.draw.rect(draw_target, (15, 15, 15), (win_x, win_y, 6, 8))
                                else:
                                    pygame.draw.rect(draw_target, (60, 50, 30), (win_x, win_y, 6, 8))  # Lit window
                            else:
                                pygame.draw.rect(draw_target, (15, 15, 15), (win_x, win_y, 6, 8))

            for i in range(10):
                tower_x = 30 + i * 120
                tower_height = 100 + (i % 3) * 15
                tower_width = 55 + (i % 2) * 10
                tower_y = horizon_y - tower_height

                # Tower silhouette with more detail
                color = (28, 23, 23)
                pygame.draw.rect(draw_target, color, (tower_x, tower_y, tower_width, tower_height))

                # Side shadow for depth
                shadow_width = 8
                pygame.draw.rect(
                    draw_target, (20, 18, 18), (tower_x + tower_width - shadow_width, tower_y, shadow_width, tower_height)
                )

                if i % 2 == 0:
                    points = [
                        (tower_x, tower_y),
                        (tower_x + tower_width // 3, tower_y - 15),
                        (tower_x + tower_width * 2 // 3, tower_y + 10),
                        (tower_x + tower_width, tower_y - 5),
                        (tower_x + tower_width, tower_y + 20),
                        (tower_x, tower_y + 20),
                    ]
                    pygame.draw.polygon(draw_target, color, points)

                # Windows with proper bounds checking
                max_floors = (tower_height - 30) // 25
                max_windows = (tower_width - 20) // 15
                for floor in range(min(4, max_floors)):
                    for window in range(min(3, max_windows)):
                        win_x = tower_x + 8 + window * 15
                        win_y = tower_y + 25 + floor * 25
                        if win_x + 10 <= tower_x + tower_width - 8 and win_y + 12 <= tower_y + tower_height - 10:
                            if (i + floor * 3 + window) % 4 == 0:
                                # Flashing emergency lights
                                if int(pygame.time.get_ticks() / 300 + i) % 3 == 0:
                                    pygame.draw.rect(draw_target, (80, 20, 20), (win_x, win_y, 10, 12))  # Red emergency light
                                else:
                                    pygame.draw.rect(draw_target, (10, 10, 10), (win_x, win_y, 10, 12))
                            else:
                                pygame.draw.rect(draw_target, (10, 10, 10), (win_x, win_y, 10, 12))

            for i in range(7):
                building_x = i * 175
                building_height = 140 + (i % 3) * 25
                building_width = 80 + (i % 2) * 15
                building_y = horizon_y - building_height + 5

                color = (22, 18, 18)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                # Strong side shadow for depth
                shadow_width = 12
                pygame.draw.rect(
                    draw_target,
                    (15, 12, 12),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                if i == 1 or i == 3:
                    hole_y = building_y + building_height // 3
                    hole_size = 25
                    pygame.draw.ellipse(
                        draw_target,
                        (30, 20, 20),
                        (building_x + building_width // 2 - hole_size // 2, hole_y, hole_size, hole_size * 2),
                    )

                # Detailed windows with bounds checking
                max_floors = (building_height - 30) // 26
                max_windows = (building_width - 25) // 18
                for floor in range(min(5, max_floors)):
                    for window in range(min(4, max_windows)):
                        win_x = building_x + 10 + window * 18
                        win_y = building_y + 20 + floor * 26
                        if win_x + 12 <= building_x + building_width - 10 and win_y + 15 <= building_y + building_height - 15:
                            if (i * 7 + floor * 5 + window) % 5 == 0:
                                # Flickering lights
                                flicker = int(pygame.time.get_ticks() / 200 + i + floor) % 4
                                if flicker == 0:
                                    pygame.draw.rect(draw_target, (60, 50, 30), (win_x, win_y, 12, 15))  # Lit
                                else:
                                    pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))
                            elif (i + floor + window) % 3 != 0:
                                pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))
                                if (floor * window) % 7 == 0:
                                    pygame.draw.line(draw_target, (15, 15, 15), (win_x, win_y), (win_x + 12, win_y + 15), 1)
                            else:
                                pygame.draw.rect(draw_target, (8, 8, 8), (win_x, win_y, 12, 15))

            fence_y = horizon_y + 50
            # Fence posts
            for x in range(0, SCREEN_WIDTH, 80):
                pygame.draw.line(draw_target, (40, 35, 35), (x, fence_y - 30), (x, fence_y + 30), 3)
            # Wire
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y - 20), (SCREEN_WIDTH, fence_y - 20), 2)
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y), (SCREEN_WIDTH, fence_y), 2)
            pygame.draw.line(draw_target, (50, 45, 45), (0, fence_y + 20), (SCREEN_WIDTH, fence_y + 20), 2)

            # Scattered debris and rubble
            for _ in range(8):
                debris_x = random.randint(50, SCREEN_WIDTH - 50)
                debris_y = random.randint(horizon_y + 80, SCREEN_HEIGHT - 100)
                debris_size = random.randint(10, 30)
                pygame.draw.polygon(
                    draw_target,
                    (35, 30, 25),
                    [
                        (debris_x, debris_y),
                        (debris_x - debris_size // 2, debris_y + debris_size // 3),
                        (debris_x + debris_size // 3, debris_y + debris_size // 2),
                        (debris_x + debris_size, debris_y + debris_size // 4),
                    ],
                )

        elif target_theme == 2:
            # Stage 2: Hell's Gates

            for i in range(4):
                volcano_x = 150 + i * 250
                volcano_base_width = 120
                volcano_height = 80
                volcano_y = horizon_y + 10

                # Distant volcano
                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 20, volcano_y - volcano_height),
                    (volcano_x + 20, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (70, 35, 30), points)

            for i in range(3):
                volcano_x = 100 + i * 350
                volcano_base_width = 160
                volcano_height = 110
                volcano_y = horizon_y + 5

                # Medium volcano
                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 25, volcano_y - volcano_height),
                    (volcano_x + 25, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (65, 30, 25), points)

                glow_radius = 15
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 100, 0, 60), (glow_radius, glow_radius), glow_radius)
                draw_target.blit(glow_surface, (volcano_x - glow_radius, volcano_y - volcano_height - glow_radius))

            for i in range(2):
                volcano_x = 200 + i * 500
                volcano_base_width = 200
                volcano_height = 150
                volcano_y = horizon_y

                points = [
                    (volcano_x - volcano_base_width // 2, volcano_y),
                    (volcano_x - 30, volcano_y - volcano_height),
                    (volcano_x + 30, volcano_y - volcano_height),
                    (volcano_x + volcano_base_width // 2, volcano_y),
                ]
                pygame.draw.polygon(draw_target, (60, 25, 20), points)

                # Lava glow at top
                for j in range(3):
                    glow_radius = 20 - j * 5
                    glow_alpha = 100 - j * 30
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (255, 100, 0, glow_alpha), (glow_radius, glow_radius), glow_radius)
                    draw_target.blit(glow_surface, (volcano_x - glow_radius, volcano_y - volcano_height - glow_radius))

                # Smoke plume
                for smoke in range(5):
                    smoke_y = volcano_y - volcano_height - 20 - smoke * 15
                    smoke_x = volcano_x + math.sin(smoke * 0.5 + pygame.time.get_ticks() * 0.001) * 10
                    smoke_size = 15 + smoke * 3
                    smoke_alpha = max(20, 80 - smoke * 15)
                    smoke_surface = pygame.Surface((smoke_size * 2, smoke_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surface, (80, 80, 80, smoke_alpha), (smoke_size, smoke_size), smoke_size)
                    draw_target.blit(smoke_surface, (smoke_x - smoke_size, smoke_y - smoke_size))

            # Flowing lava river
            river_start_x = -50
            river_y = horizon_y + 60

            river_points = []
            for i in range(30):
                x = river_start_x + i * 45
                # Create a winding river path
                y_offset = math.sin(i * 0.3) * 25
                flow_offset = math.sin(pygame.time.get_ticks() * 0.0005 + i * 0.5) * 3
                river_points.append((x, river_y + y_offset + flow_offset))

            # Draw river with multiple passes for depth
            # Dark outer edge
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (100, 20, 0), river_points[i], river_points[i + 1], 25)
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (200, 50, 0), river_points[i], river_points[i + 1], 20)
            # Bright inner flow
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (255, 100, 0), river_points[i], river_points[i + 1], 15)
            # Hot center line
            for i in range(len(river_points) - 1):
                pygame.draw.line(draw_target, (255, 200, 50), river_points[i], river_points[i + 1], 5)

            # Add flowing lava streaks
            for i in range(8):
                streak_pos = (pygame.time.get_ticks() * 0.05 + i * 100) % (SCREEN_WIDTH + 100)
                river_index = int((streak_pos - river_start_x) / 45)
                if 0 <= river_index < len(river_points) - 1:
                    t = ((streak_pos - river_start_x) % 45) / 45.0
                    y1 = river_points[river_index][1]
                    y2 = river_points[river_index + 1][1] if river_index + 1 < len(river_points) else y1
                    y_at_pos = y1 + (y2 - y1) * t
                    pygame.draw.ellipse(draw_target, (255, 255, 100), (int(streak_pos), int(y_at_pos) - 2, 20, 4))

            # Static lava pools
            lava_pool_positions = [
                (150, horizon_y + 140, 90, 35),
                (450, horizon_y + 120, 110, 40),
                (700, horizon_y + 150, 80, 30),
                (950, horizon_y + 130, 100, 35),
                (1050, horizon_y + 145, 70, 25),
            ]

            for pool_x, pool_y, pool_width, pool_height in lava_pool_positions:
                # Lava pool with glow
                lava_rect = pygame.Rect(pool_x, pool_y, pool_width, pool_height)
                pygame.draw.ellipse(draw_target, (200, 50, 0), lava_rect)
                pygame.draw.ellipse(draw_target, (255, 100, 0), (pool_x + 2, pool_y + 2, pool_width - 4, pool_height - 4))

                bubble_positions = [
                    (pool_x + pool_width // 3, pool_y + pool_height // 2),
                    (pool_x + pool_width * 2 // 3, pool_y + pool_height // 3),
                ]
                for bx, by in bubble_positions:
                    bubble_size = 3 + math.sin(pygame.time.get_ticks() * 0.003) * 1
                    pygame.draw.circle(draw_target, (255, 200, 0), (int(bx), int(by)), int(bubble_size))

            # Static charred trees
            tree_positions = [
                (120, horizon_y + 40),
                (320, horizon_y + 60),
                (520, horizon_y + 30),
                (720, horizon_y + 70),
                (880, horizon_y + 50),
            ]

            for stake_x, stake_y in tree_positions:
                # Burnt tree trunk
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y), (stake_x, stake_y - 40), 4)
                # Broken branches
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y - 30), (stake_x - 15, stake_y - 35), 2)
                pygame.draw.line(draw_target, (20, 10, 5), (stake_x, stake_y - 20), (stake_x + 10, stake_y - 28), 2)

        elif target_theme == 3:
            # Stage 3: Demon Realm - EXACT ORIGINAL IMPLEMENTATION FROM SOURCE CODE

            for crystal in range(15):
                crystal_x = crystal * 80
                crystal_y = horizon_y - 30 + math.sin(pygame.time.get_ticks() * 0.001 + crystal * 0.7) * 10

                # Smaller crystal
                size_mult = 0.5
                points = [
                    (crystal_x, crystal_y - 30 * size_mult),
                    (crystal_x - 10 * size_mult, crystal_y),
                    (crystal_x - 7 * size_mult, crystal_y + 20 * size_mult),
                    (crystal_x, crystal_y + 25 * size_mult),
                    (crystal_x + 7 * size_mult, crystal_y + 20 * size_mult),
                    (crystal_x + 10 * size_mult, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (60, 30, 90), points)

            # Main floating crystal formations
            for crystal in range(10):
                crystal_x = crystal * 120
                crystal_y = horizon_y - 50 + math.sin(pygame.time.get_ticks() * 0.001 + crystal) * 20

                # Main crystal body
                points = [
                    (crystal_x, crystal_y - 60),
                    (crystal_x - 20, crystal_y),
                    (crystal_x - 15, crystal_y + 40),
                    (crystal_x, crystal_y + 50),
                    (crystal_x + 15, crystal_y + 40),
                    (crystal_x + 20, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (80, 40, 120), points)
                pygame.draw.polygon(draw_target, (120, 60, 180), points, 2)

                # Inner glow
                inner_points = [
                    (crystal_x, crystal_y - 50),
                    (crystal_x - 10, crystal_y),
                    (crystal_x, crystal_y + 40),
                    (crystal_x + 10, crystal_y),
                ]
                pygame.draw.polygon(draw_target, (150, 100, 200), inner_points)

                # Energy particles around crystal
                for particle in range(4):
                    angle = pygame.time.get_ticks() * 0.003 + particle * 1.5
                    particle_x = crystal_x + math.cos(angle) * 30
                    particle_y = crystal_y + math.sin(angle) * 30
                    pygame.draw.circle(draw_target, (200, 150, 255), (int(particle_x), int(particle_y)), 2)

            # Twisted portal/vortex in background with rotation
            portal_x = SCREEN_WIDTH // 2
            portal_y = horizon_y - 200
            for ring in range(5):
                ring_size = 90 - ring * 15
                ring_alpha = 40 + ring * 15

                # Create rotation effect - each ring rotates at different speeds
                rotation_speed = 0.001 + ring * 0.0005  # Outer rings rotate slower
                rotation_angle = pygame.time.get_ticks() * rotation_speed

                # Create larger surface for rotation
                ring_surface = pygame.Surface((ring_size * 6, ring_size * 4), pygame.SRCALPHA)

                # Draw multiple overlapping ellipses to create swirl effect
                for swirl in range(3):
                    swirl_angle = rotation_angle + swirl * (math.pi * 2 / 3)
                    offset_x = math.cos(swirl_angle) * 10
                    offset_y = math.sin(swirl_angle) * 5

                    color = (100 + ring * 20, 50 + ring * 10, 150 + ring * 15, ring_alpha // 3)
                    ellipse_rect = (
                        ring_size * 3 - ring_size * 2 + offset_x,
                        ring_size * 2 - ring_size + offset_y,
                        ring_size * 4,
                        ring_size * 2,
                    )
                    pygame.draw.ellipse(ring_surface, color, ellipse_rect)

                draw_target.blit(ring_surface, (portal_x - ring_size * 3, portal_y - ring_size * 2))

            tentacle_positions = [
                (120, horizon_y + 140),
                (280, horizon_y + 170),
                (450, horizon_y + 145),
                (320, horizon_y + 190),
                (680, horizon_y + 135),
                (530, horizon_y + 175),
                (850, horizon_y + 160),
                (750, horizon_y + 185),
                (980, horizon_y + 150),
                (1100, horizon_y + 140),
                (200, horizon_y + 180),
                (600, horizon_y + 200),
            ]

            for tentacle_x, tentacle_base_y in tentacle_positions:
                # Draw segmented tentacle
                for segment in range(5):
                    segment_y = tentacle_base_y - segment * 15
                    wave_offset = math.sin(segment * 0.5 + pygame.time.get_ticks() * 0.002) * 10
                    segment_x = tentacle_x + wave_offset
                    segment_width = 15 - segment * 2
                    if segment_width > 0:
                        pygame.draw.circle(draw_target, (60, 30, 80), (int(segment_x), segment_y), segment_width)
                        # Sucker detail
                        if segment % 2 == 0:
                            pygame.draw.circle(draw_target, (40, 20, 60), (int(segment_x), segment_y), segment_width - 2)

            # Many more floating geometric shapes in background
            for shape in range(16):
                shape_x = shape * 75
                shape_y = horizon_y + 20 + math.sin(shape * 0.8) * 15
                rotation = pygame.time.get_ticks() * 0.0008 + shape * 0.5

                # Smaller background triangles
                size = 15
                points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * size
                    py = shape_y + math.sin(angle) * size
                    points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (80, 40, 120), points, 1)

            for shape in range(9):
                shape_x = shape * 135
                shape_y = horizon_y - 10 + math.sin(shape) * 20
                rotation = pygame.time.get_ticks() * 0.001 + shape

                # Rotating triangular prism outline
                size = 25
                points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * size
                    py = shape_y + math.sin(angle) * size
                    points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (100, 50, 150), points, 2)

                # Inner triangle
                inner_points = []
                for i in range(3):
                    angle = rotation + i * 2 * math.pi / 3
                    px = shape_x + math.cos(angle) * (size - 5)
                    py = shape_y + math.sin(angle) * (size - 5)
                    inner_points.append((int(px), int(py)))
                pygame.draw.polygon(draw_target, (150, 80, 200), inner_points, 1)

        elif target_theme == 4:
            # Stage 4: Final Apocalypse - EXACT ORIGINAL IMPLEMENTATION FROM SOURCE CODE

            for building in range(20):
                building_x = building * 60
                building_width = 40 + (building % 3) * 10
                building_height = 50 + (building % 4) * 15
                building_y = horizon_y - building_height + 15

                # Distant buildings
                color = (40, 35, 35)
                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                if building % 3 == 0:
                    points = [
                        (building_x, building_y),
                        (building_x + building_width // 3, building_y - 10),
                        (building_x + building_width * 2 // 3, building_y + 5),
                        (building_x + building_width, building_y),
                        (building_x + building_width, building_y + 10),
                        (building_x, building_y + 10),
                    ]
                    pygame.draw.polygon(draw_target, color, points)

            for building in range(13):
                building_x = building * 92
                building_width = 60 + (building % 3) * 15
                building_height = 80 + (building % 4) * 20
                building_y = horizon_y - building_height + 10

                color = (32, 27, 27)

                pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                # Side shadow for depth
                shadow_width = 6
                pygame.draw.rect(
                    draw_target,
                    (25, 20, 20),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                # Structural damage
                if building % 2 == 1:
                    # Hole blown through
                    hole_y = building_y + building_height // 2
                    hole_size = 20
                    pygame.draw.ellipse(
                        draw_target,
                        (50, 35, 35),
                        (building_x + building_width // 2 - hole_size // 2, hole_y, hole_size, hole_size),
                    )

                # Windows (many broken)
                for floor in range(building_height // 20):
                    for window in range(building_width // 18):
                        win_x = building_x + 8 + window * 18
                        win_y = building_y + 8 + floor * 20
                        if win_y < building_y + building_height - 15:
                            if (building + floor + window) % 3 != 0:
                                pygame.draw.rect(draw_target, (8, 5, 5), (win_x, win_y, 7, 10))

            for building in range(8):
                building_x = building * 150
                building_width = 100 + (building % 2) * 30
                building_height = 120 + (building % 3) * 40
                building_y = horizon_y - building_height + 5

                color = (25, 20, 20)

                # Draw building with heavy damage
                if building % 2 == 0:
                    # Broken/collapsed top
                    points = [
                        (building_x, building_y + 40),
                        (building_x + building_width // 4, building_y + 10),
                        (building_x + building_width // 2, building_y + 25),
                        (building_x + building_width * 3 // 4, building_y),
                        (building_x + building_width, building_y + 30),
                        (building_x + building_width, building_y + building_height),
                        (building_x, building_y + building_height),
                    ]
                    pygame.draw.polygon(draw_target, color, points)
                else:
                    pygame.draw.rect(draw_target, color, (building_x, building_y, building_width, building_height))

                    # Multiple holes
                    for hole_num in range(2):
                        hole_y = building_y + (hole_num + 1) * building_height // 3
                        hole_x = building_x + building_width // 2 + (hole_num - 0.5) * 20
                        hole_size = 25 + hole_num * 5
                        pygame.draw.ellipse(
                            draw_target, (45, 30, 30), (int(hole_x - hole_size // 2), hole_y, hole_size, int(hole_size * 1.5))
                        )

                # Strong shadow for depth
                shadow_width = 10
                pygame.draw.rect(
                    draw_target,
                    (15, 12, 12),
                    (building_x + building_width - shadow_width, building_y, shadow_width, building_height),
                )

                # Detailed broken windows
                for floor in range(building_height // 22):
                    for window in range(building_width // 16):
                        win_x = building_x + 10 + window * 16
                        win_y = building_y + 10 + floor * 22
                        if win_y < building_y + building_height - 20:
                            if (building * floor + window) % 4 != 0:
                                pygame.draw.rect(draw_target, (5, 3, 3), (win_x, win_y, 10, 13))
                                # Cracks in some windows
                                if (floor + window) % 5 == 0:
                                    pygame.draw.line(draw_target, (10, 8, 8), (win_x, win_y), (win_x + 10, win_y + 13), 1)

                # Fire in some buildings
                if building in [1, 3]:
                    fire_floors = [building_height // 3, building_height * 2 // 3]
                    for fire_y_offset in fire_floors:
                        fire_y = building_y + fire_y_offset
                        for flame in range(3):
                            flame_offset = (flame - 1) * 15
                            flame_x = building_x + building_width // 2 + flame_offset
                            # Flame animation using time
                            flame_height = 20 + math.sin(pygame.time.get_ticks() * 0.003 + flame) * 5
                            flame_width = 15 + math.cos(pygame.time.get_ticks() * 0.004 + flame) * 3
                            pygame.draw.ellipse(
                                draw_target,
                                (255, 150 + flame * 20, 0),
                                (
                                    int(flame_x - flame_width // 2),
                                    int(fire_y - flame_height),
                                    int(flame_width),
                                    int(flame_height),
                                ),
                            )

            # Foreground ground
            main_crack_positions = [
                [
                    (50, SCREEN_HEIGHT),
                    (80, SCREEN_HEIGHT - 60),
                    (70, SCREEN_HEIGHT - 120),
                    (100, SCREEN_HEIGHT - 180),
                    (90, SCREEN_HEIGHT - 220),
                ],
                [
                    (350, SCREEN_HEIGHT),
                    (370, SCREEN_HEIGHT - 70),
                    (360, SCREEN_HEIGHT - 130),
                    (380, SCREEN_HEIGHT - 190),
                    (375, SCREEN_HEIGHT - 230),
                ],
                [
                    (700, SCREEN_HEIGHT),
                    (720, SCREEN_HEIGHT - 50),
                    (710, SCREEN_HEIGHT - 110),
                    (730, SCREEN_HEIGHT - 160),
                    (725, SCREEN_HEIGHT - 200),
                ],
                [(900, SCREEN_HEIGHT), (920, SCREEN_HEIGHT - 80), (910, SCREEN_HEIGHT - 140), (925, SCREEN_HEIGHT - 180)],
                # Two new cracks on the right side
                [
                    (1050, SCREEN_HEIGHT),
                    (1070, SCREEN_HEIGHT - 90),
                    (1060, SCREEN_HEIGHT - 150),
                    (1080, SCREEN_HEIGHT - 200),
                ],
                [
                    (1180, SCREEN_HEIGHT),
                    (1200, SCREEN_HEIGHT - 70),
                    (1190, SCREEN_HEIGHT - 130),
                    (1210, SCREEN_HEIGHT - 180),
                    (1205, SCREEN_HEIGHT - 220),
                ],
            ]

            # Animated pulsing glow for cracks
            pulse_intensity = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)

            for crack_segments in main_crack_positions:
                if len(crack_segments) > 1:
                    # Main crack
                    pygame.draw.lines(draw_target, (10, 5, 0), False, crack_segments, 4)

                    # Animated pulsing glow from within
                    glow_color = (255, int(50 * pulse_intensity), 0)
                    pygame.draw.lines(draw_target, glow_color, False, crack_segments, 2)

                    # Bright inner line with separate animation
                    inner_color = (255, int(150 + 50 * math.sin(pygame.time.get_ticks() * 0.008)), 50)
                    pygame.draw.lines(draw_target, inner_color, False, crack_segments, 1)
