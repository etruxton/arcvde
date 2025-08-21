# arcvde

![arcvde Logo](assets/arCVde-2.png)

> **About the name**: "arcvde" is a playful pun on "arcade" - because this project will host a collection of arcade-style games powered by **CV** (Computer Vision)! 🎮👀

A real-time hand gesture recognition game where you use your finger gun to shoot targets and battle waves of enemies! This project combines OpenCV hand tracking with Pygame to create interactive shooting games controlled by your hand movements.

**What is OpenCV?** OpenCV (Open Source Computer Vision Library) is a powerful library that provides tools for image processing, computer vision, and machine learning. In arcvde, we use OpenCV with MediaPipe to track your hand movements in real-time, turning your fingers into game controllers!

## Features

- **Two Game Modes:**
  - **Target Practice** - Classic target shooting with score tracking
  - **Doomsday** - Battle waves of approaching enemies in a doom-style survival game
- **Real-time hand tracking** using MediaPipe with enhanced gesture detection
- **Multi-mode detection system** that works even when pointing directly at the camera
- **Interactive tutorial** showing how to play
- **Visual feedback** showing detection mode and confidence
- **Debug console** for testing (accessible in Doomsday mode when paused)

## How It Works

Make a finger gun gesture (index finger extended, other fingers curled, thumb up) to aim, then flick your thumb down quickly to shoot. The enhanced shooting system now requires you to lift your thumb between shots for more realistic gunplay.

### Game Modes

#### Target Practice
Classic shooting range experience where targets spawn randomly on screen. Test your accuracy and speed as you shoot down targets before they disappear.

#### Doomsday
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
- **DOOMSDAY** - Battle waves of enemies in survival mode
- **TARGET PRACTICE** - Classic target shooting game
- **HOW TO PLAY** - View detailed instructions
- **SETTINGS** - Configure camera and other options
- **QUIT** - Exit the game

### Game Controls

**In Menu:**
- Mouse clicks or shoot at buttons with finger gun
- Keyboard shortcuts: 1 for Doomsday, 2 for Target Practice

**In Target Practice:**
- **Aim**: Make finger gun gesture and move your hand
- **Shoot**: Flick your thumb down (requires thumb reset between shots)
- **Pause**: Press P or SPACE
- **Reset**: Press R to restart
- **Menu**: Press ESC to return to main menu

**In Doomsday:**
- **Aim**: Make finger gun gesture and move your hand
- **Shoot**: Flick your thumb down (requires thumb reset between shots)
- **Pause**: Press P to pause and access debug console
- **Menu**: Press ESC to return to main menu

**Debug Console (Doomsday - when paused):**
- Type `/stage [1-4]` - Jump to specific stage
- Type `/wave [1-8]` - Jump to specific wave
- Type `/heal` - Restore full health
- Type `/kill` - Kill all enemies on screen

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

Planned improvements to Doomsday include:
- Sound effects and music for both game modes
- More enemy types and boss battles
- Power-ups and special abilities (rapid fire, explosive shots)
- Difficulty levels with adaptive AI
- Custom hand gesture training for different weapons
- More stage themes and environmental hazards
- Weapon upgrades and progression system

Planned additions to arcvde:
- game like deer hunter or duck hunt that uses capybaras instead. Uses same finger gun shooting physics.
- galaga style game where you control the character with where you point
- pacman or snake style game where you control player with where you point ?
- maybe moreeeee

## Credits

### Music
- **Menu/Target Practice Music**: "Somewhere in the Elevator" by Peachtea
  - Source: https://opengameart.org/content/somewhere-in-the-elevator
  - License: CC-BY 3.0

- **Doomsday Mode Music**: "Boss Battle #8 Metal" 
  - Source: https://opengameart.org/content/boss-battle-8-metal
  - License: CC0 (Public Domain)

---

Have fun shooting targets with your finger gun! 🔫
