"""
Main game manager that handles different screens and game flow
"""

import pygame
import sys
from typing import Dict, Optional
from utils.constants import *
from utils.camera_manager import CameraManager
from screens.menu_screen import MenuScreen
from screens.game_screen import GameScreen
from screens.arcade_screen import ArcadeScreen
from screens.settings_screen import SettingsScreen
from screens.instructions_screen import InstructionsScreen

class GameManager:
    """Main game manager that coordinates all screens and game flow"""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Create screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Finger Gun Game")
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize camera manager
        self.camera_manager = CameraManager()
        self.camera_manager.initialize_camera(DEFAULT_CAMERA_ID)
        
        # Initialize screens
        self.screens: Dict[str, object] = {}
        self._initialize_screens()
        
        # Game state
        self.current_state = GAME_STATE_MENU
        self.running = True
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_update = 0
    
    def _initialize_screens(self) -> None:
        """Initialize all game screens"""
        self.screens[GAME_STATE_MENU] = MenuScreen(self.screen, self.camera_manager)
        self.screens[GAME_STATE_PLAYING] = GameScreen(self.screen, self.camera_manager)
        self.screens[GAME_STATE_ARCADE] = ArcadeScreen(self.screen, self.camera_manager)
        self.screens[GAME_STATE_SETTINGS] = SettingsScreen(self.screen, self.camera_manager)
        self.screens[GAME_STATE_INSTRUCTIONS] = InstructionsScreen(self.screen, self.camera_manager)
    
    def handle_events(self) -> None:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Let current screen handle the event
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, 'handle_event'):
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
            self.current_state = new_state
            
            # Reset game screen when entering gameplay
            if new_state == GAME_STATE_PLAYING:
                game_screen = self.screens[GAME_STATE_PLAYING]
                if hasattr(game_screen, 'reset_game'):
                    game_screen.reset_game()
            elif new_state == GAME_STATE_ARCADE:
                arcade_screen = self.screens[GAME_STATE_ARCADE]
                if hasattr(arcade_screen, 'reset_game'):
                    arcade_screen.reset_game()
        else:
            print(f"Unknown state: {new_state}")
    
    def update(self, dt: float) -> None:
        """Update current screen"""
        current_screen = self.screens.get(self.current_state)
        if current_screen and hasattr(current_screen, 'update'):
            result = current_screen.update(dt, pygame.time.get_ticks())
            # Handle state changes from update method (e.g., finger gun shooting)
            if result:
                if result == "quit":
                    self.running = False
                else:
                    self.change_state(result)
    
    def draw(self) -> None:
        """Draw current screen"""
        current_screen = self.screens.get(self.current_state)
        if current_screen and hasattr(current_screen, 'draw'):
            current_screen.draw()
        
        # Update display
        pygame.display.flip()
    
    def run(self) -> None:
        """Main game loop"""
        print("Starting Finger Gun Game...")
        print(f"Screen resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        print(f"Camera info: {self.camera_manager.get_camera_info()}")
        
        last_time = pygame.time.get_ticks()
        
        try:
            while self.running:
                # Calculate delta time
                current_time = pygame.time.get_ticks()
                dt = (current_time - last_time) / 1000.0  # Convert to seconds
                last_time = current_time
                
                # Handle events
                self.handle_events()
                
                if not self.running:
                    break
                
                # Update
                self.update(dt)
                
                # Draw
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
        
        # Release camera
        if self.camera_manager:
            self.camera_manager.release()
        
        # Quit pygame
        pygame.quit()
        print("Game cleanup complete")
    
    def get_current_screen_info(self) -> dict:
        """Get information about the current screen"""
        return {
            'current_state': self.current_state,
            'available_states': list(self.screens.keys()),
            'camera_info': self.camera_manager.get_camera_info() if self.camera_manager else None
        }