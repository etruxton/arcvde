# Doomsday Game Components

This directory contains the core game logic and components for the **Doomsday** game mode, a doom-style survival game where players battle waves of approaching enemies using finger gun detection in a 3D perspective environment.

## Files Overview

### `enemy.py`
**Enemy entities, combat mechanics, and visual effects**

Contains core classes for the enemy system:
- **`BloodParticle`**: 3D blood particle effects with physics, gravity, and perspective scaling
- **`Enemy`**: Individual enemy entities with AI, movement, combat, and death mechanics
- **`EnemyManager`**: Manages enemy spawning, wave progression, hit detection, and combat system

**Key Features:**
- **4 Enemy Types**: Zombies, Demons, Skulls, and Giants with different speeds, health, and sizes
- **3D Movement System**: Enemies approach from distance with proper perspective scaling and positioning
- **Combat Mechanics**: Health system, blood effects, death animations, and scoring
- **Wave Management**: Progressive difficulty, enemy type mixing, and spawn timing
- **Visual Effects**: Blood particles, hit feedback, and perspective-based rendering

**Enemy Types:**
- **Zombie**: Standard enemy with moderate speed and health
- **Demon**: Fast-moving enemy with lower health
- **Skull**: Floating enemy with unique movement patterns
- **Giant**: Large, slow enemy with high health and damage

### `renderer.py`
**Comprehensive rendering system for all visual elements**

The **`DoomsdayRenderer`** class provides:
- **Main Game Rendering**: Coordinates all visual elements including backgrounds, effects, enemies, UI, and animations
- **Screen Overlays**: Pause screen, game over screen, and console interface rendering
- **Visual Effects**: Muzzle flash, shoot animations, damage flash, and screen shake coordination
- **Stage Backgrounds**: Detailed 4-stage backgrounds with animated elements (urban decay, hellscape, demon realm, apocalypse)
- **UI Management**: Health bars, score display, combo indicators, wave completion, and debug information
- **Camera Integration**: Handles camera feed rendering and positioning

**Key Features:**
- **Modular Design**: Clean separation of rendering from game logic
- **Performance Optimized**: Efficient surface management and alpha blending
- **Visual Consistency**: Maintains identical appearance to original implementation
- **Screen Shake Integration**: Coordinates shake effects with main game rendering
- **Font Management**: Centralized font handling for consistent typography

### `stage_manager.py`
**Stage progression, environmental effects, and stage management**

The **`StageManager`** class provides:
- **4 Themed Stages**: Urban Decay, Hellscape, Demon Realm, and Apocalypse environments
- **Dynamic Backgrounds**: 3D grid floors, atmospheric effects, and stage-specific visuals
- **Stage Transitions**: Dramatic screen effects with shake, flash, and fade transitions
- **Environmental Effects**: Fire particles, purple mist, lightning strikes, and ambient sounds
- **Stage Progression**: Wave-based advancement with proper state management
- **Console Commands**: Debug stage jumping with `/stage #` command support

**Stage Themes:**
1. **Urban Decay**: Dark urban environment with detailed buildings, grid floor, debris
2. **Hell's Gates**: Volcanoes, flowing lava rivers, lava pools, fire effects  
3. **Demon Realm**: Floating crystals, rotating portal vortex, scattered tentacles, purple atmosphere
4. **Final Apocalypse**: Destroyed buildings, animated ground cracks, meteors, lightning, ash particles

### `stage_audio.py`
**Audio management system for stage-specific music and effects**

The **`StageAudio`** class provides:
- **Stage Music**: Manages music tracks for each stage theme
- **Stage 4 Alternation**: Special 3-track alternation system (2 alternating + 1 looping metal track)
- **Sound Effects**: Fire crackling, lightning strikes, thunder effects
- **Ambient Effects**: Stage-specific ambient loops and environmental audio
- **Transition Audio**: Handles music changes during stage transitions

### `ui_manager.py`
**User interface rendering and HUD management**

The **`DoomsdayUI`** class provides:
- **HUD Elements**: Health bar, score display, FPS counter, stage information
- **Pause Screen**: Console interface, input handling, command feedback
- **Game Over Screen**: Final statistics, wave survived, kills, time played
- **Crosshair Rendering**: Dynamic crosshair with color feedback
- **Combo System**: Combo counter and timer display
- **Damage Flash**: Screen flash effects when player takes damage

**Key Features:**
- **Visual Effects**: Stage-specific particle systems and atmospheric rendering  
- **Transition System**: Smooth stage changes with visual feedback and proper timing
- **Screen Shake**: Dynamic camera shake effects during transitions and events

## Game Flow

1. **Stage Setup**: `StageManager` initializes theme, music, and visual effects
2. **Enemy Waves**: `EnemyManager` spawns progressive waves with mixed enemy types
3. **Combat**: Players shoot enemies while environmental effects enhance atmosphere
4. **Stage Progression**: Automatic advancement every 2 waves with dramatic transitions
5. **Audio Evolution**: Music becomes more intense as stages progress, with metal track looping in later stages

## Integration

These components are used by `src/screens/doomsday_screen.py`, which acts as the main orchestrator, handling:
- Game state management and player health system
- Camera integration and hand tracking for aiming  
- Console commands and debug functionality
- Core game logic and input processing

The main screen delegates specific responsibilities:
- **Enemy Management**: All enemy spawning, AI, and combat handled by `EnemyManager`
- **Stage Management**: Environmental effects and transitions handled by `StageManager` 
- **Audio Management**: All stage music and effects handled by `StageAudio`
- **UI Management**: All user interface rendering handled by `DoomsdayUI`
- **Rendering**: All visual rendering handled by `DoomsdayRenderer`
- **Game Logic**: Core game state, player health, scoring, and input handling in main screen

## Design Philosophy

- **Modular Architecture**: Clear separation between enemy logic and stage management
- **3D Perspective**: Consistent depth and scaling throughout enemy and environmental systems
- **Progressive Intensity**: Escalating difficulty, visual complexity, and audio intensity
- **Performance Optimized**: Efficient particle systems and rendering with proper cleanup
- **Console Integration**: Debug commands for testing and development support