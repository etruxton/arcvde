#!/usr/bin/env python3
"""
arcvde - Main Entry Point
A real-time hand gesture recognition shooting game.
"""

# Standard library imports
import os
import sys

# Third-party imports
import pygame

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Local application imports
from game.game_manager import GameManager  # noqa: E402


def main():
    """Main entry point for arcvde."""
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
