"""
Blinky Bird - A blink-controlled Flappy Bird clone.

Control a bird by blinking to make it flap through obstacles.
Uses computer vision blink detection for natural, hands-free gameplay.
"""

from .background import Background
from .bird import Bird
from .game_logic import BlinkyBirdGame, GameState
from .pipe import PipeManager, SkyscraperGap

# Backward compatibility alias
Pipe = SkyscraperGap

__all__ = ["BlinkyBirdGame", "GameState", "Bird", "SkyscraperGap", "Pipe", "PipeManager", "Background"]
