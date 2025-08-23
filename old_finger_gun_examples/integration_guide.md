# Integration Guide for Enhanced Hand Tracker

## Quick Start

### 1. Test the Enhanced Tracker
First, test the enhanced tracker standalone to verify it works with your setup:

```bash
python test_enhanced_tracker.py
```

Use the keyboard controls to toggle features and compare with the original tracker.

### 2. Replace in Your Game

To integrate the enhanced tracker into your game, you have two options:

#### Option A: Direct Replacement (Recommended for testing)

In your game files that import `HandTracker`, replace:

```python
from src.game.hand_tracker import HandTracker
```

With:

```python
from src.game.enhanced_hand_tracker import EnhancedHandTracker as HandTracker
```

#### Option B: Gradual Integration

1. Import both trackers:
```python
from src.game.hand_tracker import HandTracker
from src.game.enhanced_hand_tracker import EnhancedHandTracker
```

2. Add a configuration flag:
```python
USE_ENHANCED_TRACKER = True  # Set via config or command line

if USE_ENHANCED_TRACKER:
    tracker = EnhancedHandTracker(
        enable_preprocessing=True,
        enable_angles=True,
        enable_kalman=True
    )
else:
    tracker = HandTracker()
```

### 3. Update the Process Frame Call

The enhanced tracker returns additional stats:

```python
# Original code:
image, results = tracker.process_frame(frame)

# Enhanced code:
if isinstance(tracker, EnhancedHandTracker):
    image, results, stats = tracker.process_frame(frame)
    # Optional: Use stats for debugging/monitoring
else:
    image, results = tracker.process_frame(frame)
```

## Configuration Options

### Performance vs Quality Trade-offs

```python
# Maximum quality (may reduce FPS)
tracker = EnhancedHandTracker(
    enable_preprocessing=True,
    enable_angles=True,
    enable_kalman=True
)

# Balanced (good quality, minimal performance impact)
tracker = EnhancedHandTracker(
    enable_preprocessing=True,
    enable_angles=False,  # Disable if not pointing at camera often
    enable_kalman=True
)

# Maximum performance (minimal enhancements)
tracker = EnhancedHandTracker(
    enable_preprocessing=False,
    enable_angles=False,
    enable_kalman=True  # Keep this for smoothness
)
```

### Lighting-Specific Settings

For different lighting conditions, you can dynamically adjust:

```python
# Dark environment
if average_brightness < 80:
    tracker.enable_preprocessing = True
    tracker.preprocessor.clahe.clipLimit = 4.0  # Increase contrast

# Bright environment
elif average_brightness > 170:
    tracker.enable_preprocessing = True
    tracker.preprocessor.clahe.clipLimit = 2.0  # Reduce contrast

# Normal lighting
else:
    tracker.enable_preprocessing = False  # Save processing time
```

## Troubleshooting

### Issue: Lower FPS
**Solution**: Disable preprocessing or angles:
```python
tracker.enable_preprocessing = False
tracker.enable_angles = False
```

### Issue: Jittery detection
**Solution**: Ensure Kalman filter is enabled:
```python
tracker.enable_kalman = True
```

### Issue: Not detecting at screen edges
**Solution**: Ensure preprocessing is enabled:
```python
tracker.enable_preprocessing = True
```

### Issue: False positives
**Solution**: Increase detection thresholds in `utils/constants.py` or adjust the gesture buffer size:
```python
tracker.gesture_buffer = deque(maxlen=7)  # Require more consistent frames
```

## Performance Monitoring

Add this to your game loop to monitor performance:

```python
def draw_performance_overlay(screen, stats):
    """Draw performance stats on screen"""
    if not stats:
        return
    
    text_lines = [
        f"FPS: {1000/stats['total_ms']:.1f}",
        f"Mode: {stats['detection_mode']}",
        f"Confidence: {stats['confidence']:.2f}",
    ]
    
    for i, line in enumerate(text_lines):
        # Draw text using your game's font system
        render_text(screen, line, (10, 10 + i * 20))
```

## Migration Checklist

- [ ] Backup your current `hand_tracker.py`
- [ ] Test `test_enhanced_tracker.py` to verify it works
- [ ] Choose integration method (Direct replacement or Gradual)
- [ ] Update imports in your game files
- [ ] Test with different lighting conditions
- [ ] Adjust configuration based on performance
- [ ] Add performance monitoring (optional)
- [ ] Test all game features that use hand tracking

## Recommended Settings by Use Case

### For Gaming (Low Latency Priority)
```python
tracker = EnhancedHandTracker(
    enable_preprocessing=False,
    enable_angles=False,
    enable_kalman=True
)
```

### For Accuracy (Detection Priority)
```python
tracker = EnhancedHandTracker(
    enable_preprocessing=True,
    enable_angles=True,
    enable_kalman=True
)
```

### For Poor Lighting
```python
tracker = EnhancedHandTracker(
    enable_preprocessing=True,  # Critical for poor lighting
    enable_angles=True,
    enable_kalman=True
)
```

### For Pointing at Camera
```python
tracker = EnhancedHandTracker(
    enable_preprocessing=False,
    enable_angles=True,  # Critical for camera pointing
    enable_kalman=True
)
```

## API Compatibility

The enhanced tracker is fully backward compatible with the original HandTracker API. All methods have the same signatures:

- `process_frame(frame)` - Returns additional stats tuple
- `detect_finger_gun(hand_landmarks, width, height)` - Same return format
- `detect_shooting_gesture(thumb_tip, thumb_middle_dist)` - Same behavior
- `draw_landmarks(image, hand_landmarks)` - Same visualization
- `reset_tracking_state()` - Same reset behavior

## Next Steps

1. Run the test script to verify everything works
2. Start with all features enabled
3. Monitor performance in your game
4. Adjust settings based on your specific needs
5. Consider adding a settings menu for users to adjust these options