# Code Refactoring Notes

## Overview
Both `capybara_hunt_screen.py` and `doomsday_screen.py` have grown quite large (1500+ and 1700+ lines respectively). Here are suggestions for breaking them down into more manageable, focused modules.

---

## CapybaraHuntScreen Refactoring Ideas

### 1. **Pond Buddy System** 🐾
**Current size:** ~200+ lines of pond buddy logic
**Suggested module:** `src/game/pond_buddy.py`

```python
class PondBuddy:
    def __init__(self, x, y)
    def set_mood(self, mood, duration, priority=1)
    def update(self, dt)
    def draw(self, screen)
    def on_capybara_hit(self)
    def on_capybara_miss(self) 
    def on_capybara_escape(self)
    def _draw_expressions(self, screen, mood, face_x, face_y)
```

### 2. **UI/Button Management** 🖱️
**Current size:** ~150+ lines of button creation and handling
**Suggested module:** `src/ui/capybara_hunt_ui.py`

```python
class CapybaraHuntUI:
    def create_continue_button(self)
    def create_retry_button(self)
    def create_menu_button(self)
    def handle_button_clicks(self, mouse_pos, shoot_detected)
    def draw_buttons(self, screen)
    def check_button_hit(self, button, crosshair_pos)
```

### 3. **Screen Rendering** 🎨
**Current size:** ~300+ lines of drawing methods
**Suggested module:** `src/ui/capybara_hunt_renderer.py`

```python
class CapybaraHuntRenderer:
    def draw_hud(self, screen, score, shots, round_num, hit_markers)
    def draw_hit_markers(self, screen, markers)
    def draw_round_complete_screen(self, screen, stats)
    def draw_game_over_screen(self, screen, stats)
    def draw_crosshair(self, screen, pos, color)
    def draw_scenery(self, screen)
```

### 4. **Game State Manager** 📊
**Current size:** ~100+ lines of state management
**Suggested module:** `src/game/capybara_hunt_state.py`

```python
class CapybaraHuntState:
    def __init__(self)
    def handle_round_completion(self, manager_data)
    def handle_game_over(self, manager_data)
    def can_shoot(self) -> bool
    def is_paused(self) -> bool
    def get_game_status(self) -> dict
```

### 5. **Input/Control Handler** 🕹️
**Current size:** ~150+ lines of input processing
**Suggested module:** `src/input/capybara_hunt_input.py`

```python
class CapybaraHuntInput:
    def __init__(self, hand_tracker, camera_manager)
    def process_hand_tracking(self)
    def handle_keyboard_events(self, events)
    def handle_mouse_events(self, events)
    def get_shoot_position(self) -> tuple
```

### 6. **Debug Console** 🐛
**Current size:** ~80+ lines of console logic
**Suggested module:** `src/debug/game_console.py`

```python
class GameConsole:
    def __init__(self)
    def handle_input(self, event)
    def execute_command(self, command, game_state)
    def draw(self, screen)
    def add_message(self, message, duration=3.0)
```

---

## DoomsdayScreen Refactoring Ideas

### 1. **Stage System** 🎭
**Current size:** ~400+ lines of stage management
**Suggested module:** `src/game/stage_manager.py`

```python
class StageManager:
    def __init__(self)
    def get_current_theme(self, wave_number) -> int
    def start_transition(self, old_theme, new_theme)
    def update_transition(self, dt)
    def is_transitioning(self) -> bool
    def get_transition_progress(self) -> float
    def complete_transition(self)
```

### 2. **Stage Rendering** 🌆
**Current size:** ~600+ lines of background/effects drawing
**Suggested module:** `src/graphics/stage_renderer.py`

```python
class StageRenderer:
    def __init__(self)
    def create_background(self, theme_id) -> pygame.Surface
    def draw_stage_background(self, surface, theme_id, alpha=255)
    def draw_stage_effects(self, surface, theme_id, time, alpha=255)
    def draw_transition_effect(self, surface, old_bg, new_bg, progress, effect_type)
    def draw_floor_grid(self, surface, theme_id)
```

### 3. **Audio Management** 🔊
**Current size:** ~50+ lines of music/sound logic
**Suggested module:** `src/audio/stage_audio.py`

```python
class StageAudio:
    def __init__(self, sound_manager)
    def start_stage_music(self, stage_id)
    def handle_stage4_alternation(self)
    def start_stage_ambient(self, stage_id)
    def stop_stage_effects(self)
    def transition_audio(self, old_stage, new_stage)
```

### 4. **Combat System** ⚔️
**Current size:** ~200+ lines of shooting/damage logic
**Suggested module:** `src/game/doomsday_combat.py`

```python
class DoomsdayCombat:
    def __init__(self)
    def handle_shoot(self, position, enemy_manager)
    def take_damage(self, damage, effects_manager)
    def draw_shoot_animation(self, surface, pos)
    def draw_muzzle_flash(self, surface, pos)
    def calculate_rapid_fire_bonus(self) -> float
```

### 5. **Screen Effects** ✨
**Current size:** ~100+ lines of visual effects
**Suggested module:** `src/graphics/screen_effects.py`

```python
class ScreenEffects:
    def __init__(self)
    def add_damage_flash(self, duration)
    def add_screen_shake(self, intensity, duration)
    def update(self, dt)
    def apply_effects(self, surface) -> pygame.Surface
    def draw_transition_text(self, surface, text, progress, effect_type)
```

### 6. **UI Rendering** 📱
**Current size:** ~200+ lines of UI drawing
**Suggested module:** `src/ui/doomsday_ui.py`

```python
class DoomsdayUI:
    def __init__(self)
    def draw_hud(self, surface, health, score, wave, time)
    def draw_health_bar(self, surface, current_health, max_health)
    def draw_pause_screen(self, surface)
    def draw_game_over_screen(self, surface, final_stats)
    def draw_debug_info(self, surface, debug_data)
```

---

## Implementation Priority

### CapybaraHuntScreen:
1. **Pond Buddy** (most self-contained, biggest impact)
2. **Screen Rendering** (lots of drawing methods)  
3. **Input Handler** (complex hand tracking logic)
4. **UI Management** (button handling)

### DoomsdayScreen:
1. **Stage Rendering** (largest chunk, very self-contained)
2. **Stage System** (transition logic is complex)
3. **Screen Effects** (visual effects are modular)
4. **Combat System** (shooting mechanics)

---

## Benefits After Refactoring

- **Easier to test** individual components
- **Better separation of concerns** 
- **More reusable code** (UI components could be shared)
- **Easier to debug** specific systems
- **Cleaner main screen files** that focus on orchestration
- **Better maintainability** for future features

---

## Notes

- Keep the main screen classes as orchestrators that coordinate these systems
- Use dependency injection to pass shared resources (screen, camera_manager, sound_manager)
- Consider using events/signals for loose coupling between systems
- Start with the largest, most self-contained modules first
- Test each extraction to ensure no functionality is lost