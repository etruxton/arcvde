"""
Game constants and configuration
"""

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Camera settings
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_X = SCREEN_WIDTH - CAMERA_WIDTH - 20
CAMERA_Y = 20
DEFAULT_CAMERA_ID = 0

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Vaporwave/Retro Color Palette
VAPORWAVE_PINK = (252, 17, 185)  # FC11B9 - Your brand pink
VAPORWAVE_CYAN = (16, 231, 245)  # 10E7F5 - Your brand blue/cyan
VAPORWAVE_PURPLE = (138, 43, 226)  # Deep purple for accents
VAPORWAVE_MAGENTA = (255, 20, 147)  # Hot pink variant
VAPORWAVE_MINT = (64, 224, 208)  # Mint green accent
VAPORWAVE_DARK = (25, 25, 35)  # Dark navy background
VAPORWAVE_MID_DARK = (45, 45, 65)  # Mid-tone dark
VAPORWAVE_LIGHT = (240, 240, 250)  # Off-white text

# UI Colors - Vaporwave Theme
UI_BACKGROUND = VAPORWAVE_DARK
UI_BUTTON = (60, 30, 80)  # Dark purple base
UI_BUTTON_HOVER = VAPORWAVE_PINK  # Your brand pink on hover
UI_BUTTON_ACTIVE = VAPORWAVE_CYAN  # Your brand cyan when clicked
UI_TEXT = VAPORWAVE_LIGHT
UI_ACCENT = VAPORWAVE_CYAN
UI_SECONDARY_ACCENT = VAPORWAVE_PINK

# Target settings
TARGET_SIZE = 50
TARGET_SPAWN_TIME = 2000  # milliseconds
MAX_TARGETS = 5

# Hand tracking thresholds
THUMB_INDEX_THRESHOLD = 35
MIDDLE_RING_THRESHOLD = 8
RING_PINKY_THRESHOLD = 8
INDEX_WRIST_THRESHOLD = 10
SHOOT_VELOCITY_THRESHOLD = 0.1
SHOOT_DISTANCE_THRESHOLD = 0.1
COOLDOWN_DURATION = 0.1  # Reduced - now using thumb reset mechanism instead

# Game states
GAME_STATE_LOADING = "loading"
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
GAME_STATE_ARCADE = "arcade"
GAME_STATE_CAPYBARA_HUNT = "capybara_hunt"
GAME_STATE_SETTINGS = "settings"
GAME_STATE_INSTRUCTIONS = "instructions"
GAME_STATE_PAUSED = "paused"
GAME_STATE_CLAPPY_BIRD = "clappy_bird"
