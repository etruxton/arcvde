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

### `input_handler.py`
**Comprehensive input and control management**

The **`CapybaraHuntInputHandler`** class handles:
- **Keyboard input processing**: ESC (menu), P/SPACE (pause), R (reset), RETURN (continue/retry)
- **Debug console management**: Console activation (/), command input, and command execution
- **Event delegation**: Mouse button clicks and UI interactions
- **State-aware input**: Context-sensitive input validation based on game state
- **Console commands**: /round # for debug round jumping

**Key Features:**
- **Centralized input**: All keyboard and event handling in one location
- **Console system**: Full debug console with command processing and feedback
- **Callback pattern**: Clean separation using callback functions for state changes
- **Input validation**: Context-aware input restrictions (e.g., pause only during active gameplay)
- **Reset coordination**: Coordinated game state and UI resets across components

**Supported Commands:**
- `/round #`: Jump to specific round number for testing

### `renderer.py`
**Comprehensive rendering and visual effects system**

The **`CapybaraHuntRenderer`** class provides:
- **Background creation**: Nature scene with sky gradients, mountains, hills, and pond
- **Animated scenery**: Dynamic clouds, birds, particles, flowers, grass tufts, sun rays, and pond ripples
- **Game UI rendering**: HUD elements (score, shots, hit markers), crosshairs, and shooting effects
- **Screen overlays**: Pause screen, game over screen, and round completion screens
- **Visual effects**: Punishment messages, shoot animations, and impact effects

**Key Features:**
- **Layered rendering**: Proper depth sorting for visual elements
- **Animated elements**: Time-based updates for moving scenery components
- **Responsive UI**: Dynamic screen adaptation and visual feedback
- **Performance optimized**: Efficient drawing with surface caching and batched operations

**Rendering Pipeline:**
1. Static background (mountains, hills, pond)
2. Animated scenery (clouds, birds, particles, grass)
3. Game entities (capybaras drawn by manager)
4. UI overlays and effects
5. Camera feed and debug information

### `state_manager.py`
**Game state management and flow control system**

The **`CapybaraHuntState`** class manages:
- **Core state variables**: Score, shots remaining, game over, pause, round completion time
- **State transitions**: Game resets, round progression, pause/resume functionality
- **State validation**: Shooting permissions, UI screen display logic, game flow control
- **State processing**: Round completion handling, game over transitions, performance-based reactions
- **Hit tracking**: Round progress markers and performance analytics

**Key Features:**
- **Centralized state**: All game state in one managed location
- **State queries**: Clean boolean methods for state checking (`can_shoot()`, `is_paused()`, etc.)
- **Transition safety**: Processing flags prevent duplicate state transitions
- **Performance tracking**: Hit markers and scoring with penalty system
- **Reactive system**: Automatic pond buddy mood management based on game events

**State Flow:**
1. **Initial state**: Fresh game with default values
2. **Active gameplay**: Shooting validation, hit tracking, score management
3. **Round transitions**: Completion processing, score bonuses, reaction triggers
4. **Game over handling**: Penalty calculations, final state management
5. **Reset capabilities**: Clean state restoration for new games

## Game Flow

1. **Spawning**: `CapybaraManager` spawns waves of `FlyingCapybara` instances
2. **Gameplay**: Players aim and shoot at balloons while `PondBuddy` reacts
3. **Interactions**: Hit detection, scoring, and state updates
4. **UI**: `CapybaraHuntUI` manages round completion and game over screens
5. **Progression**: Difficulty scaling and round advancement

## Integration

These components are used by `src/screens/capybara_hunt_screen.py`, which acts as the main orchestrator, handling:
- Game state management and logic coordination  
- Camera integration and hand tracking
- Sound management and effects

The main screen delegates specific responsibilities:
- **Rendering**: All visual rendering handled by `CapybaraHuntRenderer`
- **UI Management**: Button interactions handled by `CapybaraHuntUI`
- **Input Handling**: Keyboard and event processing handled by `CapybaraHuntInputHandler`
- **State Management**: Game state and flow control handled by `CapybaraHuntState`
- **Game Logic**: Entity management handled by `CapybaraManager`
- **Companion**: Emotional reactions handled by `PondBuddy`

## Design Philosophy

- **Single responsibility**: Each class focuses on one aspect of the game
- **Clean separation**: Game logic separated from rendering and UI
- **Reusability**: Components designed to be modular and testable
- **Maintainability**: Clear interfaces and well-defined responsibilities