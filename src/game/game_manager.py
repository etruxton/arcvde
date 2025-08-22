"""
Main game manager that handles different screens and game flow
"""

# Standard library imports
import sys
import threading
from typing import Dict, Optional

# Third-party imports
import pygame

# Local application imports
from screens.doomsday_screen import DoomsdayScreen
from screens.instructions_screen import InstructionsScreen
from screens.loading_screen import LoadingScreen
from screens.menu_screen import MenuScreen
from screens.settings_screen import SettingsScreen
from screens.target_practice_screen import TargetPracticeScreen
from utils.camera_manager import CameraManager
from utils.constants import (
    DEFAULT_CAMERA_ID,
    FPS,
    GAME_STATE_ARCADE,
    GAME_STATE_INSTRUCTIONS,
    GAME_STATE_LOADING,
    GAME_STATE_MENU,
    GAME_STATE_PLAYING,
    GAME_STATE_SETTINGS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class GameManager:
    """Main game manager that coordinates all screens and game flow"""

    def __init__(self):
        pygame.init()

        # Set window icon
        try:
            icon = pygame.image.load("assets/CV.png")
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"Could not load icon: {e}")

        pygame.display.set_caption("arcvde")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()

        # Initialize loading screen immediately
        self.screens: Dict[str, object] = {}
        self.screens[GAME_STATE_LOADING] = LoadingScreen(self.screen)

        # Game state - start with loading screen
        self.current_state = GAME_STATE_LOADING
        self.running = True

        # Loading state tracking
        self.loading_complete = False
        self.camera_manager = None
        self.initialization_started = False

        # Performance tracking
        self.frame_count = 0
        self.last_fps_update = 0

    def _start_initialization(self) -> None:
        """Start initialization in a separate thread"""
        init_thread = threading.Thread(target=self._initialize_remaining_screens, daemon=True)
        init_thread.start()

    def _initialize_remaining_screens(self) -> None:
        """Initialize remaining game screens after camera is ready"""
        try:
            print("Initializing camera...")
            self.camera_manager = CameraManager()
            self.camera_manager.initialize_camera(DEFAULT_CAMERA_ID)

            print("Initializing game screens...")
            self.screens[GAME_STATE_MENU] = MenuScreen(self.screen, self.camera_manager)
            self.screens[GAME_STATE_PLAYING] = TargetPracticeScreen(self.screen, self.camera_manager)
            self.screens[GAME_STATE_ARCADE] = DoomsdayScreen(self.screen, self.camera_manager)
            self.screens[GAME_STATE_SETTINGS] = SettingsScreen(self.screen, self.camera_manager)
            self.screens[GAME_STATE_INSTRUCTIONS] = InstructionsScreen(self.screen, self.camera_manager)

            self.loading_complete = True
            print("Loading complete!")
        except Exception as e:
            print(f"Error during initialization: {e}")
            self.loading_complete = True  # Mark as complete even if failed to prevent infinite loop

    def handle_events(self) -> None:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Let current screen handle the event
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, "handle_event"):
                next_state = current_screen.handle_event(event)

                if next_state:
                    if next_state == "quit":
                        self.running = False
                    else:
                        self.change_state(next_state)

    def change_state(self, new_state: str) -> None:
        """Change the current game state"""
        if new_state in self.screens:
            print(f"Changing state from {self.current_state} to {new_state}")
            old_state = self.current_state
            self.current_state = new_state

            # Handle music transitions
            # Local application imports
            from utils.sound_manager import get_sound_manager

            sound_manager = get_sound_manager()

            # When leaving Doomsday, stop the music and sound effects immediately
            if old_state == GAME_STATE_ARCADE:
                sound_manager.stop_ambient(fade_ms=100)  # Quick fade
                sound_manager.stop_stage_effect(fade_ms=100)  # Stop any stage effects

            # When entering menu, instructions, or target practice, start elevator music
            if new_state in [GAME_STATE_MENU, GAME_STATE_INSTRUCTIONS, GAME_STATE_PLAYING, GAME_STATE_SETTINGS]:
                if sound_manager.current_ambient != "elevator":
                    sound_manager.play_ambient("elevator")

            # When entering Doomsday, let the doomsday screen handle its own music
            elif new_state == GAME_STATE_ARCADE:
                pass  # Doomsday screen will manage its own stage-specific music

            # Reset target practice screen when entering gameplay
            if new_state == GAME_STATE_PLAYING:
                target_practice_screen = self.screens[GAME_STATE_PLAYING]
                if hasattr(target_practice_screen, "reset_game"):
                    target_practice_screen.reset_game()
            elif new_state == GAME_STATE_ARCADE:
                doomsday_screen = self.screens[GAME_STATE_ARCADE]
                if hasattr(doomsday_screen, "reset_game"):
                    doomsday_screen.reset_game()
        else:
            print(f"Unknown state: {new_state}")

    def update(self, dt: float) -> None:
        """Update current screen"""
        # Handle loading state specially
        if self.current_state == GAME_STATE_LOADING:
            # Initialize remaining screens if not done yet
            if not self.loading_complete and not self.initialization_started:
                # Check if we've shown the loading screen for at least a moment
                loading_screen = self.screens.get(GAME_STATE_LOADING)
                if loading_screen and hasattr(loading_screen, "animation_time"):
                    # Start loading other resources after loading screen has been visible for 0.2 seconds
                    if loading_screen.animation_time > 0.2:
                        self.initialization_started = True
                        # Start initialization in a way that allows rendering between steps
                        self._start_initialization()

            # Update loading screen and check if it wants to transition
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, "update"):
                # Pass loading status to loading screen
                if hasattr(current_screen, "set_loading_complete"):
                    current_screen.set_loading_complete(self.loading_complete)

                result = current_screen.update(dt, pygame.time.get_ticks())
                if result:
                    if result == "quit":
                        self.running = False
                    elif self.loading_complete:  # Only allow transition if loading is complete
                        self.change_state(result)
        else:
            # Normal screen updates
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, "update"):
                result = current_screen.update(dt, pygame.time.get_ticks())
                if result:
                    if result == "quit":
                        self.running = False
                    else:
                        self.change_state(result)

    def draw(self) -> None:
        """Draw current screen"""
        current_screen = self.screens.get(self.current_state)
        if current_screen and hasattr(current_screen, "draw"):
            current_screen.draw()

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop"""
        print("Starting arCVde...")
        print(f"Screen resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        print("Camera will be initialized during loading...")

        last_time = pygame.time.get_ticks()

        try:
            while self.running:
                # Calculate delta time
                current_time = pygame.time.get_ticks()
                dt = (current_time - last_time) / 1000.0  # Convert to seconds
                last_time = current_time

                self.handle_events()

                if not self.running:
                    break

                self.update(dt)
                self.draw()

                # Control frame rate
                self.clock.tick(FPS)

                # Track performance
                self.frame_count += 1
                if current_time - self.last_fps_update > 5000:  # Every 5 seconds
                    avg_fps = self.frame_count / ((current_time - self.last_fps_update) / 1000.0)
                    print(f"Average FPS: {avg_fps:.1f}")
                    self.frame_count = 0
                    self.last_fps_update = current_time

        except KeyboardInterrupt:
            print("\nGame interrupted by user")

        except Exception as e:
            print(f"An error occurred during game execution: {e}")
            raise

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources"""
        print("Cleaning up resources...")

        # Release camera (only if it was initialized)
        if self.camera_manager:
            self.camera_manager.release()

        # Quit pygame
        pygame.quit()
        print("Game cleanup complete")

    def get_current_screen_info(self) -> dict:
        """Get information about the current screen"""
        return {
            "current_state": self.current_state,
            "available_states": list(self.screens.keys()),
            "camera_info": self.camera_manager.get_camera_info() if self.camera_manager else "Camera not initialized yet",
        }
