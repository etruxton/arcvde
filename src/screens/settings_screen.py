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
    GAME_STATE_CREDITS,
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

        # Volume management
        self.master_volume = self.settings_manager.get("master_volume", 0.7)
        self.current_view = "camera"  # "camera" or "volume"
        self.volume_bar = self._create_volume_bar()
        self.volume_changed = False

    def _create_ui_elements(self) -> None:
        """Create UI buttons and elements"""
        # Back button
        self.back_button = Button(50, 50, 120, 50, "BACK", self.button_font)

        # View switcher buttons at the top
        view_button_width = 150
        view_button_height = 50
        view_start_x = 200
        view_y = 130

        self.camera_view_button = Button(
            view_start_x, view_y, view_button_width, view_button_height, "CAMERA", self.button_font
        )
        self.volume_view_button = Button(
            view_start_x + view_button_width + 20, view_y, view_button_width, view_button_height, "VOLUME", self.button_font
        )

        # Credits button next to volume button
        self.credits_button = Button(
            view_start_x + 2 * (view_button_width + 20),
            view_y,
            view_button_width,
            view_button_height,
            "CREDITS",
            self.button_font,
        )

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
        self.test_button = Button(start_x + 150, start_y + 150, 150, button_height, "TEST CAMERA", self.button_font)

        self.apply_button = Button(start_x, start_y + 150, 100, button_height, "APPLY", self.button_font)

        # Debug mode toggle button
        self.debug_button = Button(start_x, start_y + 220, 200, button_height, "DEBUG MODE", self.button_font)

        self.all_buttons = (
            [self.back_button, self.camera_view_button, self.volume_view_button, self.credits_button]
            + self.camera_buttons
            + [self.test_button, self.apply_button, self.debug_button]
        )

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
                elif button == self.volume_view_button:
                    self._switch_to_volume_view()
                elif button == self.camera_view_button:
                    self._switch_to_camera_view()
                elif button == self.credits_button:
                    return GAME_STATE_CREDITS

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

        if self.volume_changed:
            # Save volume to settings
            self.settings_manager.set("master_volume", self.master_volume)
            self.volume_changed = False
            self.settings_changed = False
            print(f"Volume saved: {self.master_volume:.1%}")

    def _toggle_debug_mode(self) -> None:
        """Toggle debug mode on/off"""
        self.debug_mode = self.settings_manager.toggle("debug_mode")
        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")

    def _switch_to_volume_view(self) -> None:
        """Switch to volume configuration view"""
        self.current_view = "volume"
        print("Switched to volume configuration")

    def _create_volume_bar(self) -> list:
        """Create volume bar segments that can be shot"""
        bar_segments = []
        bar_x = 200
        bar_y = 350
        segment_width = 30
        segment_height = 40
        num_segments = 10
        spacing = 5

        for i in range(num_segments):
            x = bar_x + i * (segment_width + spacing)
            # Create a mock button for each segment for shooting detection
            segment = Button(x, bar_y, segment_width, segment_height, "", self.button_font)
            segment.volume_level = (i + 1) / num_segments  # Volume from 0.1 to 1.0
            bar_segments.append(segment)

        return bar_segments

    def _set_volume(self, volume_level: float) -> None:
        """Set the master volume level"""
        self.master_volume = volume_level
        self.volume_changed = True
        self.settings_changed = True

        # Apply volume immediately for feedback
        # Local application imports
        from utils.sound_manager import get_sound_manager

        sound_manager = get_sound_manager()
        sound_manager.set_master_volume(volume_level)

        # Play a test sound for feedback
        sound_manager.play("shoot")

    def _switch_to_camera_view(self) -> None:
        """Switch back to camera configuration view"""
        self.current_view = "camera"
        print("Switched to camera configuration")

    def update(self, dt: float, current_time: int) -> Optional[str]:
        """Update settings screen"""
        # Process hand tracking
        self.process_finger_gun_tracking()

        buttons_to_check = self.all_buttons.copy()
        if self.current_view == "volume":
            buttons_to_check.extend(self.volume_bar)

        shot_button = self.check_button_shoot(buttons_to_check)
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
            elif shot_button == self.volume_view_button:
                self._switch_to_volume_view()
            elif shot_button == self.camera_view_button:
                self._switch_to_camera_view()
            elif shot_button == self.credits_button:
                return GAME_STATE_CREDITS
            elif shot_button in self.volume_bar:
                self._set_volume(shot_button.volume_level)

        return None

    def draw(self) -> None:
        """Draw the settings screen"""
        # Clear screen
        self.screen.fill(UI_BACKGROUND)

        title_text = self.title_font.render("SETTINGS", True, VAPORWAVE_CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)

        if self.current_view == "camera":
            self._draw_camera_view()
        elif self.current_view == "volume":
            self._draw_volume_view()

        # Common elements (back button, camera preview, etc.)
        self._draw_common_elements()

    def _draw_camera_view(self) -> None:
        """Draw the camera configuration view"""
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

        # Draw view switcher buttons first
        view_buttons = [self.camera_view_button, self.volume_view_button, self.credits_button]
        self.update_button_finger_states(view_buttons)

        for button in view_buttons:
            # Highlight active view button
            if button == self.camera_view_button and self.current_view == "camera":
                highlight_rect = pygame.Rect(
                    button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                )
                pygame.draw.rect(self.screen, VAPORWAVE_PINK, highlight_rect, 3)

            button.draw(self.screen)

        # Draw camera-specific buttons
        buttons_to_show = [self.back_button] + self.camera_buttons + [self.test_button, self.apply_button, self.debug_button]
        self.update_button_finger_states(buttons_to_show)

        for button in buttons_to_show:
            # Highlight selected camera button
            if button in self.camera_buttons and button.camera_id == self.selected_camera:
                highlight_rect = pygame.Rect(
                    button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                )
                pygame.draw.rect(self.screen, UI_ACCENT, highlight_rect, 3)

            # Highlight debug button if enabled
            if button == self.debug_button and self.debug_mode:
                highlight_rect = pygame.Rect(
                    button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                )
                pygame.draw.rect(self.screen, GREEN, highlight_rect, 3)

            button.draw(self.screen)

        debug_status = "ON" if self.debug_mode else "OFF"
        debug_color = GREEN if self.debug_mode else GRAY
        status_text = self.button_font.render(f"Debug: {debug_status}", True, debug_color)
        self.screen.blit(status_text, (self.debug_button.rect.x + 220, self.debug_button.rect.y + 5))

        # Draw instructions
        instructions = [
            "Select a camera and click TEST to preview",
            "Click APPLY to save changes",
            "Press ESC or BACK to return to menu",
        ]

        for i, instruction in enumerate(instructions):
            text_surface = self.info_font.render(instruction, True, GRAY)
            self.screen.blit(text_surface, (200, SCREEN_HEIGHT - 100 + i * 25))

    def _draw_volume_view(self) -> None:
        """Draw the volume configuration view"""
        # Draw view switcher buttons first
        view_buttons = [self.camera_view_button, self.volume_view_button, self.credits_button]
        self.update_button_finger_states(view_buttons)

        for button in view_buttons:
            # Highlight active view button
            if button == self.volume_view_button and self.current_view == "volume":
                highlight_rect = pygame.Rect(
                    button.rect.x - 3, button.rect.y - 3, button.rect.width + 6, button.rect.height + 6
                )
                pygame.draw.rect(self.screen, VAPORWAVE_PINK, highlight_rect, 3)

            button.draw(self.screen)

        volume_title = self.section_font.render("Master Volume", True, UI_TEXT)
        self.screen.blit(volume_title, (200, 220))

        # Draw current volume info
        volume_text = f"Current Volume: {self.master_volume:.1%}"
        volume_surface = self.info_font.render(volume_text, True, UI_TEXT)
        self.screen.blit(volume_surface, (200, 260))

        # Draw volume bar
        bar_y = 350
        bar_title = self.info_font.render("Shoot the volume bars to adjust:", True, UI_TEXT)
        self.screen.blit(bar_title, (200, bar_y - 30))

        # Update and draw volume bar segments
        self.update_button_finger_states(self.volume_bar)

        for i, segment in enumerate(self.volume_bar):
            # Fill segments up to current volume level
            volume_level = (i + 1) / len(self.volume_bar)
            if volume_level <= self.master_volume:
                # Filled segment - use gradient from cyan to pink based on level
                if volume_level <= 0.3:
                    color = VAPORWAVE_CYAN
                elif volume_level <= 0.7:
                    color = UI_ACCENT
                else:
                    color = VAPORWAVE_PINK
            else:
                # Empty segment
                color = GRAY

            # Draw segment with border
            pygame.draw.rect(self.screen, color, segment.rect)
            pygame.draw.rect(self.screen, UI_TEXT, segment.rect, 2)

        # Draw control buttons
        buttons_to_show = [self.back_button, self.apply_button]
        self.update_button_finger_states(buttons_to_show)

        for button in buttons_to_show:
            button.draw(self.screen)

        # Draw instructions
        instructions = [
            "Shoot the volume bars to set master volume",
            "Click APPLY to save changes",
            "Click CAMERA button above to switch views",
        ]

        for i, instruction in enumerate(instructions):
            text_surface = self.info_font.render(instruction, True, GRAY)
            self.screen.blit(text_surface, (200, SCREEN_HEIGHT - 100 + i * 25))

    def _draw_common_elements(self) -> None:
        """Draw elements common to all views"""
        if self.crosshair_pos:
            self.draw_crosshair(self.crosshair_pos, self.crosshair_color)

        # Draw shooting animation
        self.draw_shoot_animation()

        # Draw camera preview (keep it visible in both views)
        preview_width = 400
        preview_height = 300
        preview_x = SCREEN_WIDTH - preview_width - 50
        preview_y = 200

        self.draw_camera_with_tracking(preview_x, preview_y, preview_width, preview_height)

        # Draw preview label
        label_text = self.info_font.render("Camera Preview", True, UI_TEXT)
        self.screen.blit(label_text, (preview_x, preview_y - 25))
