# Finger Gun Game

A real-time hand gesture recognition game where you use your finger gun to shoot targets and battle waves of enemies! This project combines OpenCV hand tracking with Pygame to create interactive shooting games controlled by your hand movements.

## Features

- **Two Game Modes:**
  - **Target Practice** - Classic target shooting with score tracking
  - **Arcade Mode** - Battle waves of approaching enemies in a doom-style survival game
- **Real-time hand tracking** using MediaPipe with enhanced gesture detection
- **Multi-mode detection system** that works even when pointing directly at the camera
- **Four unique enemy types** with detailed animations and AI behaviors
- **Dynamic difficulty** with 8 waves across 4 apocalyptic stages
- **Physics-based blood effects** with realistic particle simulation
- **Professional game structure** with multiple screens and settings
- **Camera selection** - switch between multiple cameras
- **Interactive tutorial** showing how to play
- **Visual feedback** showing detection mode and confidence
- **Debug console** for testing (accessible in arcade mode when paused)

## How It Works

Make a finger gun gesture (index finger extended, other fingers curled, thumb up) to aim, then flick your thumb down quickly to shoot. The enhanced shooting system now requires you to lift your thumb between shots for more realistic gunplay.

### Game Modes

#### Target Practice
Classic shooting range experience where targets spawn randomly on screen. Test your accuracy and speed as you shoot down targets before they disappear.

#### Arcade Mode
Face waves of approaching enemies in an apocalyptic survival game:
- **4 Enemy Types:** Zombies, Demons, Skulls, and Giants
- **4 Themed Stages:** Urban Decay, Hellscape, Ghostly Void, and Apocalypse
- **Special Effects:** Dynamic weather, particles, and stage-specific atmospheres
- **Combo System:** Chain kills for bonus points
- **Health System:** Survive enemy attacks and heal between waves

### Detection Modes

The game uses three intelligent detection modes:

- **Standard Mode** (Green crosshair) - Original detection method, works best at angles
- **Depth Mode** (Yellow crosshair) - Activates when pointing directly at camera using 3D coordinates
- **Wrist Angle Mode** (Purple crosshair) - Fallback method using wrist orientation

## Installation

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the Game
```bash
python main.py
```

The game will start with a main menu where you can:
- **ARCADE MODE** - Battle waves of enemies in survival mode
- **TARGET PRACTICE** - Classic target shooting game
- **HOW TO PLAY** - View detailed instructions
- **SETTINGS** - Configure camera and other options
- **QUIT** - Exit the game

### Game Controls

**In Menu:**
- Mouse clicks or shoot at buttons with finger gun
- Keyboard shortcuts: 1 for Arcade, 2 for Target Practice

**In Target Practice:**
- **Aim**: Make finger gun gesture and move your hand
- **Shoot**: Flick your thumb down (requires thumb reset between shots)
- **Pause**: Press P or SPACE
- **Reset**: Press R to restart
- **Menu**: Press ESC to return to main menu

**In Arcade Mode:**
- **Aim**: Make finger gun gesture and move your hand
- **Shoot**: Flick your thumb down (requires thumb reset between shots)
- **Pause**: Press P to pause and access debug console
- **Menu**: Press ESC to return to main menu

**Debug Console (Arcade Mode - when paused):**
- Type `/stage [1-4]` - Jump to specific stage
- Type `/wave [1-8]` - Jump to specific wave
- Type `/heal` - Restore full health
- Type `/kill` - Kill all enemies on screen

## Project Structure

```
finger-gun-pygame/
├── main.py                 # Main entry point
├── src/
│   ├── game/
│   │   ├── game_manager.py # Main game coordinator
│   │   ├── hand_tracker.py # Enhanced hand tracking with thumb reset
│   │   ├── target.py       # Target management and rendering
│   │   └── enemy.py        # Enemy system with 4 types and blood physics
│   ├── screens/
│   │   ├── menu_screen.py  # Main menu with animated enemy showcase
│   │   ├── game_screen.py  # Target practice gameplay
│   │   ├── arcade_screen.py # Arcade mode with waves and stages
│   │   ├── settings_screen.py # Camera and settings configuration
│   │   └── instructions_screen.py # How-to tutorial
│   └── utils/
│       ├── constants.py    # Game constants and configuration
│       └── camera_manager.py # Camera device management
├── assets/                 # Game assets (empty for now)
├── old_finger_gun_examples/ # Previous iterations
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Files Description

- **main.py** - Entry point that initializes and runs the game
- **game_manager.py** - Coordinates different screens and game flow
- **hand_tracker.py** - Enhanced finger gun detection with thumb reset mechanism
- **target.py** - Target spawning, animation, and hit detection
- **enemy.py** - Enemy AI, rendering, and physics-based blood effects
- **camera_manager.py** - Handles camera device detection and switching
- **menu_screen.py** - Main menu with animated enemy showcase
- **game_screen.py** - Target practice mode with score tracking
- **arcade_screen.py** - Wave-based survival mode with stages and bosses
- **settings_screen.py** - Camera selection and configuration
- **instructions_screen.py** - Interactive tutorial with examples

## Settings & Configuration

### Camera Settings
- Access via Settings menu
- Test different cameras before applying
- Automatic detection of available cameras
- Live preview of selected camera

### Game Configuration
All game constants can be modified in `src/utils/constants.py`:
- Screen resolution
- Target spawn rates
- Hand tracking thresholds
- UI colors and styling

## Tips for Best Results

1. **Lighting**: Ensure good lighting for better hand detection
2. **Distance**: Position yourself 2-3 feet from the camera
3. **Hand Position**: For standard mode, hold hand at slight angle to camera
4. **Pointing at Camera**: The enhanced version automatically switches to depth mode
5. **Camera Selection**: Try different cameras in Settings if tracking is poor

## Advanced Features

### Enhanced Hand Tracking
- **Thumb Reset Mechanism**: Requires deliberate thumb movement between shots
- **Cascading Detection**: Falls back through multiple detection methods
- **3D Coordinate Analysis**: Uses depth information when available
- **Adaptive Thresholds**: Adjusts sensitivity based on detection mode
- **Real-time Feedback**: Shows confidence scores and detection mode

### Arcade Mode Features
- **Enemy Types**:
  - **Zombies**: Slow but persistent, with rotting appearance
  - **Demons**: Fast triangular demons with bat wings
  - **Skulls**: Fragile floating skulls that die in one shot
  - **Giants**: Massive armored enemies with electric effects
- **Stage Themes**:
  - **Urban Decay**: Abandoned city with green atmosphere
  - **Hellscape**: Fiery environment with lava effects
  - **Ghostly Void**: Ethereal blue stage with mist
  - **Apocalypse**: Final stage with meteors and lightning
- **Physics System**: Realistic blood particles with gravity and splattering
- **Dynamic Difficulty**: Enemy speed and spawn rates increase with waves

### Game Features
- **Animated Targets**: Pulsing targets with hit animations
- **Smart Spawning**: Avoids camera area and existing targets
- **Performance Monitoring**: FPS counter and optimization
- **Pause/Resume**: Full game state management
- **Combo System**: Chain kills for bonus points in arcade mode

## Requirements

- Python 3.7+
- Webcam
- See `requirements.txt` for Python packages

## Troubleshooting

**Camera Issues:**
- Try different camera IDs in Settings
- Ensure camera isn't being used by other applications
- Check camera permissions

**Performance Issues:**
- Close other applications using the camera
- Reduce screen resolution in constants.py
- Try different MediaPipe model complexity settings

**Hand Tracking Issues:**
- Ensure good lighting
- Try different detection modes
- Adjust distance from camera
- Check the How To Play tutorial

## Future Enhancements

Planned improvements include:
- Sound effects and music for both game modes
- More enemy types and boss battles
- Power-ups and special abilities (rapid fire, explosive shots)
- Difficulty levels with adaptive AI
- High score tracking and leaderboards
- Custom hand gesture training for different weapons
- More stage themes and environmental hazards
- Weapon upgrades and progression system

---

Have fun shooting targets with your finger gun! 🔫