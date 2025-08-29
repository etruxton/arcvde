# Capybara Hunt Game Components

This directory contains the core game logic and components for the **Capybara Hunt** game mode, a Duck Hunt-inspired mini-game where players shoot balloons (not the capybaras!) using finger gun detection.

## Files Overview

### `capybara.py`
**Core game entities and mechanics**

Contains two main classes:
- **`FlyingCapybara`**: Individual capybara entities that fly with balloons, can be shot, fall to ground, and exhibit various ground behaviors (walking, sitting, laying down, kicking, standing)
- **`CapybaraManager`**: Manages spawning, updating, hit detection, and game state for all capybaras in a round

**Key Features:**
- Animated sprite system with multiple behaviors (running, sleeping, sitting, kicking, etc.)
- Balloon physics and string animation
- Ground behavior AI with state transitions
- Hit detection for both balloons and capybaras
- Progressive difficulty scaling

### `pond_buddy.py`
**Companion character system**

The **`PondBuddy`** class provides:
- **Mood system**: Reacts to player actions with different emotional states
- **Speech bubbles**: Encouraging or snarky comments based on performance
- **Visual expressions**: Dynamic facial animations matching current mood
- **Priority-based reactions**: More important events override current mood
- **Idle behaviors**: Random reactions when not actively responding

**Mood Types:** neutral, happy, sad, excited, laughing, surprised, celebration, relieved, proud, disappointed, worried

### `ui_manager.py`
**User interface and button management**

The **`CapybaraHuntUI`** class handles:
- **Button creation**: Continue, retry, and menu buttons for different game states
- **Input handling**: Both mouse clicks and finger gun shooting at buttons
- **Visual feedback**: Button highlighting when aimed at with crosshair
- **State management**: Proper button lifecycle during game flow

**Supported Actions:**
- Continue to next round
- Retry after game over
- Return to main menu
- Visual crosshair targeting feedback

## Game Flow

1. **Spawning**: `CapybaraManager` spawns waves of `FlyingCapybara` instances
2. **Gameplay**: Players aim and shoot at balloons while `PondBuddy` reacts
3. **Interactions**: Hit detection, scoring, and state updates
4. **UI**: `CapybaraHuntUI` manages round completion and game over screens
5. **Progression**: Difficulty scaling and round advancement

## Integration

These components are used by `src/screens/capybara_hunt_screen.py`, which acts as the main orchestrator, handling:
- Scene rendering and animated backgrounds
- Camera integration and hand tracking
- Sound management and effects
- Overall game state coordination

## Design Philosophy

- **Single responsibility**: Each class focuses on one aspect of the game
- **Clean separation**: Game logic separated from rendering and UI
- **Reusability**: Components designed to be modular and testable
- **Maintainability**: Clear interfaces and well-defined responsibilities