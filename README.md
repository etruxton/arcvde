# ARCVDE

![ARCVDE Logo](assets/arCVde-3.png)

> **About the name**: "ARCVDE" is a playful pun on "ARCADE" - because this project will host a collection of arcade-style games powered by **CV** (Computer Vision)! 👀

A real-time hand gesture recognition game where you use your finger gun to shoot targets and battle waves of enemies! This project combines OpenCV hand tracking with Pygame to create interactive shooting games controlled by your hand movements.

**What is OpenCV?** OpenCV (Open Source Computer Vision Library) is a powerful library that provides tools for image processing, computer vision, and machine learning. In ARCVDE, we use OpenCV with MediaPipe to track your hand movements in real-time, turning your fingers into game controllers!

## Features

- **Four Game Modes:**
  - **Target Practice** - Classic target shooting with score tracking
  - **Doomsday** - Battle waves of approaching enemies in a doom-style survival game
  - **Capybara Hunt** - Save adorable capybaras by popping their balloons in this Duck Hunt-inspired mode
  - **Blinky Bird** - Cyberpunk-themed blink-controlled Flappy Bird clone
- **Real-time hand tracking** using MediaPipe with enhanced gesture detection
- **Multi-mode detection system** that works even when pointing directly at the camera
- **Interactive tutorial** showing how to play
- **Visual feedback** showing detection mode and confidence
- **Debug console** for testing (accessible in Doomsday and Capybara Hunt modes when paused)

## How It Works

Make a finger gun gesture (index finger extended, other fingers curled, thumb up) to aim, then flick your thumb down quickly to shoot. The enhanced shooting system now requires you to lift your thumb between shots for more realistic gunplay.

Future: will have different games with different hand controls.

### Game Modes

#### Target Practice
Classic shooting range experience where targets spawn randomly on screen. Test your accuracy and speed as you shoot down targets before they disappear.

![Target Practice Demo](assets/demo_gifs/target_practice_gif.gif)

#### Doomsday
Face waves of approaching enemies in an apocalyptic survival game:
- **4 Enemy Types:** Zombies, Demons, Skulls, and Giants
- **4 Themed Stages:** Urban Decay, Hellscape, Ghostly Void, and Apocalypse
- **Special Effects:** Dynamic weather, particles, and stage-specific atmospheres
- **Combo System:** Chain kills for bonus points
- **Health System:** Survive enemy attacks and heal between waves

#### Capybara Hunt
A wholesome twist on Duck Hunt where you save capybaras instead of hunting them:
- **Balloon Rescue Mechanic:** Shoot balloons to safely drop capybaras to the ground
- **Punishment System:** Lose points for accidentally shooting capybaras
- **Progressive Difficulty:** More capybaras spawn as rounds advance
- **Duck Hunt Rules:** 10 targets per round with increasing hit requirements
- **Animated Sprites:** Capybaras walk around happily after being saved

#### Blinky Bird
Navigate through a neon cyberpunk cityscape using only your blinks:
- **Blink-Controlled Gameplay:** Blink to make your chrome cyber-bird flap through obstacles
- **Cyberpunk Cityscape:** Fly through gaps between towering neon skyscrapers
- **Adaptive Blink Detection:** Automatic calibration works with or without glasses
- **Progressive Difficulty:** Skyscraper gaps narrow and move faster as your score increases
- **Stunning Visuals:** Multi-layered cyberpunk city with animated neon lights and particle effects

## Installation

### Prerequisites
- **Python 3.7+** - Download from [python.org](https://www.python.org/downloads/)
- **pip** - Usually included with Python installation
- Webcam

### Steps
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
- **CAPYBARA HUNT** - Save capybaras by popping their balloons
- **BLINKY BIRD** - Navigate through cyberpunk cityscape with blinks
- **TARGET PRACTICE** - Classic target shooting game
- **HOW TO PLAY** - View detailed instructions
- **SETTINGS** - Configure camera and other options
- **QUIT** - Exit the game

### Game Controls

**In Menu:**
- Mouse clicks or shoot at buttons with finger gun
- Keyboard shortcuts: 1 for Doomsday, 2 for Capybara Hunt, 3 for Blinky Bird, 4 for Target Practice

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

**In Capybara Hunt:**
- **Aim**: Make finger gun gesture and move your hand
- **Shoot**: Flick your thumb down to pop balloons (5 shots per wave)
- **Objective**: Shoot balloons to save capybaras, avoid shooting capybaras directly
- **Pause**: Press P to pause and access debug console
- **Menu**: Press ESC to return to main menu

**In Blinky Bird:**
- **Fly**: Blink to make your cyber-bird flap and gain altitude
- **Navigate**: Fly through gaps between neon skyscrapers in the cyberpunk cityscape
- **Pause**: Press P to pause the game
- **Restart**: Press R to restart after game over, or blink to restart
- **Recalibrate**: Press C to recalibrate blink detection
- **Menu**: Press ESC to return to main menu

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
- ~~Stage Transitions~~ ✅ **DONE!**
- Sound effects and music for both game modes
- More enemy types and boss battles
- Power-ups and special abilities (rapid fire, explosive shots)
- Custom hand gesture training for different weapons
- More stage themes and environmental hazards
- Weapon upgrades and progression system

Planned improvements to Capybara Hunt include:
- Enemy that you need to shoot to protect the capybara
- ~~Silly reactions by the pond buddy~~ ✅ **DONE!**
- More animations
- Difficulty settings
- More themes and backgrounds

Planned improvements to Blinky Bird include:
- ~~Synthwave music for cyberpunk atmosphere~~ ✅ **DONE!**
- Sound effects for flaps and collisions
- Multiple cyber-bird designs and unlockable skins
- Power-ups triggered by special blink patterns (double blink for boost)
- Different cyberpunk environments (rainy nights, neon districts, space stations)

Planned additions to ARCVDE:
- ~~Capybara Hunt - like duck hunt but you shoot capybaras? or something around them~~ ✅ **DONE! Cabypara Hunt where you shoot balloons carrying capy's**
- Galaga style game where you control the character with where you point
- PacMan or Snake style game where you control player with where you point ?
- ~~Flappy Bird where you control the bird by clapping. Clappy Bird! 👏~~ ✅ **DONE! Blinky Bird uses blinks instead**
- Angry Birds style game where you physically pinch and real back the bird to shoot it at a tower of blocks
- maybe moreeeee

## Credits

### Art Assets

#### Capybara Hunt Mode
- **Capybara Sprites**: "Simple Capybara Sprite Sheet" by Rainloaf
  - Source: https://rainloaf.itch.io/capybara-sprite-sheet
  - License: Free to use in commercial/non-commercial projects with credit to Rainloaf

### Music
- **Menu/Target Practice Music**: "Somewhere in the Elevator" by Peachtea
  - Source: https://opengameart.org/content/somewhere-in-the-elevator
  - License: CC-BY 3.0

#### Capybara Hunt Music
- **Background Music**: "Day & Night in Summerset" by edwinnington
  - Source: https://opengameart.org/content/day-night-in-summerset
  - License: CC-BY 3.0

#### Doomsday Mode Stage Music
- **Stage 1**: "Boss Battle 3 Alternate (8-bit)" by nene
  - Source: https://opengameart.org/content/boss-battle-3-alternate-8-bit
  - License: CC0 (Public Domain)

- **Stage 2**: "Boss Battle 4 (8-bit) - Re-upload" by nene
  - Source: https://opengameart.org/content/boss-battle-4-8-bit-re-upload
  - License: CC0 (Public Domain)

- **Stage 3**: "Boss Battle 6 (8-bit)" by nene
  - Source: https://opengameart.org/content/boss-battle-6-8-bit
  - License: CC0 (Public Domain)

- **Stage 4+**: "Boss Battle 8 Retro" by nene (alternating tracks)
  - Source: https://opengameart.org/content/boss-battle-8-retro
  - License: CC0 (Public Domain)

- **Stage 4+ Metal**: "Boss Battle 8 Metal" by nene (third alternating track)
  - Source: https://opengameart.org/content/boss-battle-8-metal
  - License: CC0 (Public Domain)

#### Blinky Bird Music
- **Background Music**: "Happy/melancholic synth + bells song | Adaptive layers pack" by 3xBlast
  - Source: https://opengameart.org/content/happymelancholic-synth-bells-song-adaptive-layers-pack
  - License: CC-BY 3.0

---
