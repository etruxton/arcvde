"""
Settings manager for storing and retrieving game settings
"""

# Standard library imports
import json
import os
from typing import Any, Dict


class SettingsManager:
    """Manages game settings for the current session only"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        # Session-only settings (no file persistence)
        self.settings = {
            "camera_id": 0,
            "debug_mode": False,  # Always starts OFF
            "sound_enabled": True,
            "music_volume": 0.5,
            "sfx_volume": 0.7,
        }

    def save_settings(self):
        """No-op for session-only settings"""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value (session only)"""
        self.settings[key] = value
        # No file saving for session-only settings

    def toggle(self, key: str) -> bool:
        """Toggle a boolean setting (session only)"""
        current = self.get(key, False)
        new_value = not current
        self.set(key, new_value)
        return new_value


# Singleton instance
def get_settings_manager() -> SettingsManager:
    """Get the singleton settings manager instance"""
    return SettingsManager()
