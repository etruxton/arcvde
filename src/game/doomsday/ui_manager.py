"""
UI Manager for Doomsday mode - handles all UI rendering and elements
"""

# Standard library imports
import time
from typing import Optional, Tuple

# Third-party imports
import pygame

# Local application imports
from utils.constants import DARK_GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, UI_ACCENT, WHITE, YELLOW


class DoomsdayUI:
    """UI manager for doomsday mode screens and overlays"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def draw_hud(
        self,
        surface: pygame.Surface,
        stage_manager,
        enemy_manager,
        player_health: int,
        max_health: int,
        score: int,
        wave_number: int,
        current_fps: int,
        debug_mode: bool,
    ) -> None:
        """Draw the heads-up display with health, score, wave info"""
        # Health bar at bottom left (original position)
        self.draw_health_bar_bottom_left(surface, player_health, max_health)

        # Score at top left
        score_text = self.font.render(f"Score: {score:,}", True, WHITE)
        surface.blit(score_text, (10, 10))

        # Wave/Stage info at top left (below score)
        wave_text = self.font.render(stage_manager.get_wave_text(wave_number), True, WHITE)
        surface.blit(wave_text, (10, 50))

        # FPS counter at bottom right (always show, not just debug mode)
        fps_text = self.small_font.render(f"FPS: {current_fps}", True, (150, 150, 150))
        fps_rect = fps_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        surface.blit(fps_text, fps_rect)

    def draw_health_bar_bottom_left(self, surface: pygame.Surface, current_health: int, max_health: int) -> None:
        """Draw player health bar in bottom-left corner (original position)"""
        bar_width = 300
        bar_height = 30
        bar_x = 10
        bar_y = SCREEN_HEIGHT - 40

        # Health bar background (dark red)
        pygame.draw.rect(surface, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Health bar fill
        health_percent = max(0, current_health / max_health)
        health_width = int(bar_width * health_percent)

        # Color based on health percentage
        if health_percent > 0.6:
            health_color = (0, 255, 0)  # Green
        elif health_percent > 0.3:
            health_color = (255, 255, 0)  # Yellow
        else:
            health_color = (255, 0, 0)  # Red

        if health_width > 0:
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))

        # Health bar border
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # Health text (centered in bar)
        health_text = self.small_font.render(f"{current_health}/{max_health}", True, WHITE)
        text_x = bar_x + bar_width // 2 - health_text.get_width() // 2
        text_y = bar_y + bar_height // 2 - health_text.get_height() // 2
        surface.blit(health_text, (text_x, text_y))

    def draw_pause_screen(
        self,
        surface: pygame.Surface,
        console_active: bool,
        console_input: str,
        console_message: str,
        console_message_time: float,
    ) -> None:
        """Draw pause screen overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Pause text
        pause_text = self.font.render("PAUSED", True, WHITE)
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
            control_text = self.font.render(control, True, UI_ACCENT)  # Changed from small_font to font
            control_rect = control_text.get_rect(
                center=(SCREEN_WIDTH // 2, y_start + i * 40)
            )  # Increased spacing from 30 to 40
            surface.blit(control_text, control_rect)

        # Debug console
        if console_active:
            self._draw_debug_console(surface, console_input, console_message, console_message_time)

    def draw_game_over_screen(
        self,
        surface: pygame.Surface,
        score: int,
        wave_number: int,
        total_kills: int,
        time_survived: float,
    ) -> None:
        """Draw game over screen with final stats"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Game Over text
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        surface.blit(game_over_text, game_over_rect)

        # Final stats
        stats = [
            f"Final Score: {score:,}",
            f"Waves Survived: {wave_number}",
            f"Total Kills: {total_kills}",
            f"Time: {time_survived:.1f}s",
        ]

        y_start = SCREEN_HEIGHT // 2 - 80
        for i, stat in enumerate(stats):
            stat_text = self.small_font.render(stat, True, WHITE)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 35))
            surface.blit(stat_text, stat_rect)

        # Controls
        restart_text = self.small_font.render("R or ENTER - Restart", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        surface.blit(restart_text, restart_rect)

        menu_text = self.small_font.render("ESC - Main Menu", True, YELLOW)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110))
        surface.blit(menu_text, menu_rect)

    def draw_wave_transition_text(self, surface: pygame.Surface, text: str, progress: float) -> None:
        """Draw wave transition text with fade effect"""
        # Calculate alpha based on progress (fade in, stay, fade out)
        if progress < 0.2:
            alpha = int(255 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(255 * ((1.0 - progress) / 0.2))
        else:
            alpha = 255

        if alpha <= 0:
            return

        # Create surface for alpha blending
        text_surface = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)

        # Main text
        wave_text = self.font.render(text, True, (*WHITE, alpha))
        text_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        text_surface.blit(wave_text, text_rect)

        # Position on screen
        surface.blit(text_surface, (0, SCREEN_HEIGHT // 2 - 50))

    def draw_combo_indicator(self, surface: pygame.Surface, combo: int, combo_timer: float) -> None:
        """Draw combo multiplier indicator"""
        if combo <= 1:
            return

        # Position in top center
        x = SCREEN_WIDTH // 2
        y = 100

        # Create combo text
        combo_text = f"{combo}x COMBO!"
        text_surface = self.font.render(combo_text, True, YELLOW)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)

        # Timer bar
        bar_width = 150
        bar_height = 8
        bar_x = x - bar_width // 2
        bar_y = y + 25

        # Background
        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))

        # Timer bar
        timer_width = int(bar_width * (combo_timer / 3.0))  # 3.0s max combo time
        if timer_width > 0:
            pygame.draw.rect(surface, YELLOW, (bar_x, bar_y, timer_width, bar_height))

    def _draw_debug_console(
        self,
        surface: pygame.Surface,
        console_input: str,
        console_message: str,
        console_message_time: float,
    ) -> None:
        """Draw debug console overlay"""
        console_height = 150
        console_y = SCREEN_HEIGHT - console_height

        # Console background
        console_surface = pygame.Surface((SCREEN_WIDTH, console_height))
        console_surface.set_alpha(200)
        console_surface.fill((0, 0, 0))
        surface.blit(console_surface, (0, console_y))

        # Console border
        pygame.draw.rect(surface, UI_ACCENT, (0, console_y, SCREEN_WIDTH, console_height), 2)

        # Console title
        title_text = self.small_font.render("DEBUG CONSOLE", True, UI_ACCENT)
        surface.blit(title_text, (10, console_y + 10))

        # Input line
        input_text = f"> {console_input}_"
        input_surface = self.small_font.render(input_text, True, WHITE)
        surface.blit(input_surface, (10, console_y + 40))

        # Console message (if any)
        if console_message and time.time() - console_message_time < 3.0:
            message_surface = self.small_font.render(console_message, True, GREEN)
            surface.blit(message_surface, (10, console_y + 70))

        # Available commands
        commands_text = "Commands: /stage #, /wave #, /heal, /kill"
        commands_surface = self.small_font.render(commands_text, True, (150, 150, 150))
        surface.blit(commands_surface, (10, console_y + 100))

    def draw_crosshair(self, surface: pygame.Surface, pos: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        """Draw crosshair at given position"""
        x, y = pos
        size = 15
        thickness = 2

        pygame.draw.circle(surface, color, pos, size, thickness)
        pygame.draw.line(surface, color, (x - size - 8, y), (x + size + 8, y), thickness)
        pygame.draw.line(surface, color, (x, y - size - 8), (x, y + size + 8), thickness)

    def draw_damage_flash(self, surface: pygame.Surface, alpha: int) -> None:
        """Draw red damage flash overlay"""
        if alpha <= 0:
            return

        flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash_surface.fill((255, 0, 0, alpha))
        surface.blit(flash_surface, (0, 0))
