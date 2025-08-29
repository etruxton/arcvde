"""
Settings screen for camera selection and configuration
"""

# Standard library imports
from typing import Optional

# Third-party imports
import pygame

# Local application imports
from screens.base_screen import BaseScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    GAME_STATE_MENU,
    GRAY,
    GREEN,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    UI_BACKGROUND,
    UI_TEXT,
    VAPORWAVE_CYAN,
    VAPORWAVE_PINK,
)
from utils.settings_manager import get_settings_manager
from utils.ui_components import Button


class SettingsScreen(BaseScreen):
    """Settings screen for game configuration"""

    def __init__(self, screen: pygame.Surface, camera_manager: CameraManager):
        super().__init__(screen, camera_manager)

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.section_font = pygame.font.Font(None, 48)
        self.button_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)

        self._create_ui_elements()

        self.selected_camera = self.camera_manager.camera_id
        self.settings_changed = False

        self.settings_manager = get_settings_manager()
        self.debug_mode = self.settings_manager.get("debug_mode", False)

    def _create_ui_elements(self) -> None:
        """Create UI buttons and elements"""
        # Back button
        self.back_button = Button(50, 50, 120, 50, "BACK", self.button_font)

        # Camera selection buttons
        button_width = 80
        button_height = 40
        start_x = 300
        start_y = 300
        spacing = 100

        self.camera_buttons = []
        available_cameras = self.camera_manager.get_available_cameras()

        for i, camera_id in enumerate(available_cameras):
            x = start_x + (i % 5) * spacing
            y = start_y + (i // 5) * (button_height + 20)

            button = Button(x, y, button_width, button_height, f"Cam {camera_id}", self.button_font)
            button.camera_id = camera_id
            self.camera_buttons.append(button)

        # Test camera button
        self.test_button = Button(start_x, start_y + 150, 150, button_height, "TEST CAMERA", self.button_font)

        self.apply_button = Button(start_x + 200, start_y + 150, 100, button_height, "APPLY", self.button_font)

        # Debug mode toggle button
        self.debug_button = Button(start_x, start_y + 220, 200, button_height, "DEBUG MODE", self.button_font)

        self.all_buttons = [self.back_button] + self.camera_buttons + [self.test_button, self.apply_button, self.debug_button]

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events, return next state if applicable"""
        for button in self.all_buttons:
            if button.handle_event(event):
                if button == self.back_button:
                    if self.settings_changed:
                        self._apply_settings()
                    return GAME_STATE_MENU
                elif button in self.camera_buttons:
                    self.selected_camera = button.camera_id
                    self.settings_changed = True
                elif button == self.test_button:
                    self._test_camera()
                elif button == self.apply_button:
                    self._apply_settings()
                elif button == self.debug_button:
                    self._toggle_debug_mode()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.settings_changed:
                    self._apply_settings()
                return GAME_STATE_MENU

        return None

    def _test_camera(self) -> None:
        """Test the selected camera"""
        if self.selected_camera != self.camera_manager.camera_id:
            success = self.camera_manager.switch_camera(self.selected_camera)
            if not success:
                print(f"Failed to switch to camera {self.selected_camera}")

    def _apply_settings(self) -> None:
        """Apply the current settings"""
        if self.selected_camera != self.camera_manager.camera_id:
            success = self.camera_manager.switch_camera(self.selected_camera)
            if success:
                self.settings_changed = False
                print(f"Switched to camera {self.selected_camera}")
            else:
                print(f"Failed to switch to camera {self.selected_camera}")
                # Revert selection
                self.selected_camera = self.camera_manager.camera_id

    def _toggle_debug_mode(self) -> None:
        """Toggle debug mode on/off"""
        self.debug_mode = self.settings_manager.toggle("debug_mode")
        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update settings screen"""
        # Process hand tracking
        self.process_finger_gun_tracking()

        shot_button = self.check_button_shoot(self.all_buttons)
        if shot_button:
            if shot_button == self.back_button:
                if self.settings_changed:
                    self._apply_settings()
                return GAME_STATE_MENU
            elif shot_button in self.camera_buttons:
                self.selected_camera = shot_button.camera_id
                self.settings_changed = True
            elif shot_button == self.test_button:
                self._test_camera()
            elif shot_button == self.apply_button:
                self._apply_settings()
            elif shot_button == self.debug_button:
                self._toggle_debug_mode()

        return None

    def draw(self) -> None:
        """Draw the settings screen"""
        # Clear screen
        self.screen.fill(UI_BACKGROUND)

        title_text = self.title_font.render("SETTINGS", True, VAPORWAVE_CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)

        camera_title = self.section_font.render("Camera Selection", True, UI_TEXT)
        self.screen.blit(camera_title, (200, 200))

        camera_info = self.camera_manager.get_camera_info()
        current_text = (
            f"Current: Camera {camera_info['current_id']} ({camera_info['resolution'][0]}x{camera_info['resolution'][1]})"
        )
        current_surface = self.info_font.render(current_text, True, UI_TEXT)
        self.screen.blit(current_surface, (200, 240))

        selected_text = f"Selected: Camera {self.selected_camera}"
        selected_color = UI_ACCENT if self.selected_camera != self.camera_manager.camera_id else UI_TEXT
        selected_surface = self.info_font.render(selected_text, True, selected_color)
        self.screen.blit(selected_surface, (200, 260))

        self.update_button_finger_states(self.all_buttons)

        for button in self.all_buttons:
            # Highlight selected camera button
            if button in self.camera_buttons and button.camera_id == self.selected_camera:
                highlight_rect = pygame.Rect(
                    button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                )
                pygame.draw.rect(self.screen, UI_ACCENT, highlight_rect, 3)

            # Highlight debug button if enabled
            if button == self.debug_button:
                if self.debug_mode:
                    highlight_rect = pygame.Rect(
                        button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                    )
                    pygame.draw.rect(self.screen, GREEN, highlight_rect, 3)

            button.draw(self.screen)

        debug_status = "ON" if self.debug_mode else "OFF"
        debug_color = GREEN if self.debug_mode else GRAY
        status_text = self.button_font.render(f"Debug: {debug_status}", True, debug_color)
        self.screen.blit(status_text, (self.debug_button.rect.x + 220, self.debug_button.rect.y + 5))

        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        self.draw_shoot_animation()

        # Draw camera preview
        preview_width = 400
        preview_height = 300
        preview_x = SCREEN_WIDTH - preview_width - 50
        preview_y = 200

        self.draw_camera_with_tracking(preview_x, preview_y, preview_width, preview_height)

        # Draw preview label
        label_text = self.info_font.render("Camera Preview", True, UI_TEXT)
        self.screen.blit(label_text, (preview_x, preview_y - 25))

        # Draw instructions
        instructions = [
            "Select a camera and click TEST to preview",
            "Click APPLY to save changes",
            "Press ESC or BACK to return to menu",
        ]

        for i, instruction in enumerate(instructions):
            text_surface = self.info_font.render(instruction, True, GRAY)
            self.screen.blit(text_surface, (200, SCREEN_HEIGHT - 100 + i * 25))
