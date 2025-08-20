#!/usr/bin/env python3
"""
arCVde - Main Entry Point
A real-time hand gesture recognition shooting game.
"""

import pygame
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from game.game_manager import GameManager

def main():
    """Main entry point for arCVde."""
    # Initialize pygame
    pygame.init()
    
    try:
        # Create and run the game
        game = GameManager()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()