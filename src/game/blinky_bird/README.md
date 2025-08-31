# Blinky Bird Game Module

A cyberpunk-themed, blink-controlled Flappy Bird clone that uses computer vision for natural, hands-free gameplay. Players control a futuristic bird by blinking to navigate through neon-lit skyscraper obstacles in a stunning cyberpunk cityscape.

## Overview

Blinky Bird combines the classic Flappy Bird gameplay with innovative computer vision controls and a breathtaking cyberpunk aesthetic. Instead of keyboard or mouse input, players use blinking motions detected by their camera to control a chrome-plated cyber-bird through towering neon skyscrapers. The game features adaptive difficulty, smooth physics, stunning visual effects, and an immersive night-city atmosphere.

## Features

- **Blink-Controlled Gameplay**: Deliberate blinks make the cyber-bird flap
- **Automatic Calibration**: Adapts to individual players and glasses wearers
- **Progressive Difficulty**: Skyscraper gaps get narrower and faster as score increases
- **Smooth Physics**: Realistic bird movement with gravity and momentum
- **Cyberpunk Cityscape**: Multi-layer parallax scrolling with animated neon skyscrapers
- **Stunning Visual Effects**: Chrome-metallic bird with neon glow effects and cyber-aesthetics
- **Night City Atmosphere**: Dark sky with twinkling stars and pulsing neon lights
- **High Score Tracking**: Persistent best score tracking
- **Dynamic Lighting**: Animated window lights and neon edge effects

## Game Architecture

### Core Components

1. **Cyber-Bird** (`bird.py`)
   - Physics-based movement with gravity and flapping
   - Animated metallic wings with neon accent lighting
   - Chrome body with cyan glow effects and cyber-googly eyes
   - Angular design with particle glow effects

2. **Skyscraper Obstacle System** (`pipe.py`) 
   - Procedural building generation with neon-lit gaps
   - Dynamic window lighting with flickering animations
   - Difficulty scaling (narrower gaps, faster movement)
   - Pulsing neon edge effects at gap entrances
   - Multiple neon color schemes (cyan, magenta, yellow, green, orange)

3. **Cyberpunk Cityscape** (`background.py`)
   - Multi-layer parallax scrolling with background/foreground skyscrapers
   - Animated neon building windows with randomized lighting patterns
   - Night sky gradient with twinkling stars
   - Neon street with glowing lane markers and animated lighting

4. **Game Logic** (`game_logic.py`)
   - State management (calibration, playing, game over)
   - Score tracking and collision detection
   - Blink input handling and game coordination

### Game States

1. **WAITING_FOR_CALIBRATION**: Initial state, waiting for blink detector
2. **CALIBRATING**: Blink detector is learning player's baseline
3. **READY**: Calibration complete, waiting for first blink to start
4. **PLAYING**: Active gameplay with physics and obstacles
5. **GAME_OVER**: Collision detected, showing score and restart option

## Quick Start

```python
from game.blinky_bird import BlinkyBirdGame
from game.cv.blink_detection import BlinkDetector
import pygame

# Initialize game and detector
game = BlinkyBirdGame(800, 600)
detector = BlinkDetector(calibration_time=2.0)

# Game loop
while running:
    # Process camera frame
    blink_detected, blink_type = detector.process_frame(camera_frame)
    
    # Handle blink input
    if blink_detected:
        game.handle_blink(blink_type)
    
    # Update game
    game_state = game.update(dt)
    
    # Render
    game.draw(screen)
```

## Controls

- **Any Blink**: Make bird flap
- **Calibration**: Look at camera for 2 seconds during startup
- **Restart**: Blink after game over to play again

## Gameplay Mechanics

### Bird Physics
- **Gravity**: Constant downward acceleration
- **Flapping**: Upward velocity burst on wink detection
- **Rotation**: Bird rotates based on vertical velocity
- **Animation**: Wing flapping animation during ascent

### Difficulty Scaling
- **Pipe Gaps**: Start at 150px, decrease by 2px per point (minimum 100px)
- **Pipe Speed**: Increases by 0.1 units per point (maximum 4 units)
- **Spawn Rate**: Consistent 300px spacing between pipes

### Scoring System
- **+1 Point**: For each pipe successfully passed
- **High Score**: Automatically tracked and displayed
- **Visual Feedback**: Score display with current and best scores

## Customization

### Cyber-Bird Appearance
```python
# In bird.py, modify cyberpunk colors
self.body_color = (40, 40, 60)       # Dark metallic body
self.body_accent = (0, 255, 255)     # Cyan neon accents
self.wing_color = (60, 60, 80)       # Darker metallic wings  
self.wing_accent = (255, 0, 255)     # Magenta neon wing edges
self.pupil_color = (0, 255, 150)     # Bright green cyber pupil
```

### Difficulty Settings
```python
# In pipe.py PipeManager
self.base_gap_size = 150           # Starting gap size
self.min_gap_size = 100            # Minimum gap size
self.gap_reduction_per_score = 2   # Gap reduction per point
self.base_speed = 2                # Starting speed
self.max_speed = 4                 # Maximum speed
```

### Physics Tuning
```python
# In bird.py
self.gravity = 0.6                 # Downward acceleration
self.flap_strength = -12           # Upward velocity on flap
self.max_fall_speed = 10           # Terminal velocity
```

## Integration with Blink Detection

The game integrates seamlessly with the advanced blink detection module:

```python
# Blink types handled by game
blink_type_mapping = {
    "Blink": "Flap cyber-bird (both eyes closed simultaneously)",
    "Calibrating": "Show calibration UI with progress bar",
    "None": "No action"
}

# Game state responses
state_responses = {
    "CALIBRATING": "Display calibration progress with neon UI",
    "READY": "Show 'blink to start' message with cyberpunk styling",
    "PLAYING": "Active gameplay with neon cityscape",
    "GAME_OVER": "Show score and 'blink to restart' with pink neon text"
}
```

## Performance Considerations

- **Frame Rate**: Optimized for 60 FPS gameplay
- **Memory Usage**: Efficient object pooling for pipes and clouds
- **Rendering**: Minimal overdraw with layered drawing order
- **Physics**: Fixed timestep physics for consistent behavior

## Visual Style

### Art Direction
- **Cyberpunk Aesthetic**: Dark atmosphere with vibrant neon accents
- **Smooth Animation**: Fluid wing flapping, rotation, and neon pulsing effects
- **Depth Effects**: Multi-layer parallax scrolling with atmospheric lighting
- **Particle Effects**: Glowing neon particles and metallic shine effects
- **Dynamic Lighting**: Animated window patterns and pulsing neon edges

### Color Palette
- **Sky**: Dark gradient from deep space black to purple horizon
- **Cyber-Bird**: Dark metallic chrome with cyan/magenta neon accents  
- **Skyscrapers**: Dark buildings with multi-colored neon windows (cyan, magenta, yellow, green, orange)
- **Street**: Dark asphalt with glowing cyan lane markers and animated lighting
- **UI**: Vaporwave theme with pink and cyan neon text
- **Effects**: Bright neon glows with alpha transparency for atmospheric depth

## Future Enhancements

### Potential Features
- **Power-ups**: Neon energy boosts triggered by different blink patterns
- **Multiple Cyber-Birds**: Unlock different futuristic bird designs and color schemes
- **Themed Cityscapes**: Various cyberpunk environments (rainy nights, neon districts, space stations)
- **Sound Integration**: Synthwave music and electronic sound effects
- **Holographic UI**: Advanced statistics and achievements with cyber-styling
- **Multiplayer**: Compare scores with holographic leaderboards

### Advanced Controls
- **Blink Intensity**: Different flap strengths based on blink duration
- **Double Blinks**: Boost mode for advanced players
- **Eye Tracking**: More precise control based on gaze direction
- **Facial Expressions**: Additional controls using smile/frown detection for special abilities

## Dependencies

- Pygame: Graphics and game engine with alpha blending support
- NumPy: Mathematical operations for particle effects
- MediaPipe: Advanced facial landmark detection for blink recognition
- OpenCV: Camera capture and image processing
- Computer Vision Module: Blink detection integration with glasses support

## Testing

### Unit Tests
```python
# Test bird physics
def test_bird_physics():
    bird = Bird(100, 100)
    bird.flap()
    assert bird.velocity_y < 0  # Upward movement

# Test collision detection
def test_pipe_collision():
    pipe = Pipe(100, 600)
    bird_rect = pygame.Rect(100, 100, 40, 40)
    assert pipe.check_collision(bird_rect)
```

### Integration Testing
- Calibration flow testing
- Game state transitions
- Wink input handling
- Score persistence

## Troubleshooting

### Common Issues

**"Cyber-bird doesn't respond to blinks"**
- Check blink detector calibration (look at camera for 2 seconds)
- Ensure good lighting on face for facial landmark detection
- Verify camera permissions and MediaPipe functionality
- Try recalibrating with 'C' key

**"Game too difficult"**
- Adjust gap_reduction_per_score in pipe.py (SkyscraperGap system)
- Modify gravity/flap_strength in bird.py
- Check blink detection sensitivity and cooldown timing

**"Performance issues with neon effects"**
- Reduce building count in background.py
- Lower alpha transparency levels for glow effects
- Disable some particle effects if needed
- Lower camera resolution
- Check CPU usage during blink detection and neon rendering

### Debug Mode
```python
# Enable debug info
game_info = game.get_game_info()
print(f"Bird Y: {game_info['bird_y']}")
print(f"Next pipe: {game_info.get('next_pipe', 'None')}")
```

This module provides a complete, visually stunning cyberpunk gaming experience that demonstrates the potential of computer vision controls in immersive casual games. The combination of blink detection technology with atmospheric neon aesthetics creates a unique and memorable gameplay experience.