"""
Sound Manager for handling game audio effects
"""

import pygame
import os

class SoundManager:
    """Manages all game sound effects"""
    
    def __init__(self):
        """Initialize the sound manager"""
        self.enabled = True
        self.sounds = {}
        self.ambient_channel = None
        self.current_ambient = None
        
        # Initialize pygame mixer (with settings that work well for both WAV and OGG)
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Set volume
        pygame.mixer.set_num_channels(8)  # Allow 8 simultaneous sounds
        
        # Reserve channel 0 for ambient music
        self.ambient_channel = pygame.mixer.Channel(0)
        
        # Load sound effects
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all sound effects"""
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sounds')
        
        # Define sound files to load (supports both .wav and .ogg)
        sound_files = {
            'shoot': 'shoot.wav',
            'hit': 'hit.wav',
            'enemy_hit': 'hit.wav',  # Can use same or different sound
            'enemy_death': 'hit.wav',  # Can be customized later
            'elevator': 'Peachtea - Somewhere in the Elevator.ogg',  # Ambient music for menu
            'boss_battle': 'boss_battle_8_metal_loop.ogg',  # Intense music for Doomsday mode
        }
        
        # Load each sound
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(sound_dir, filename)
            if os.path.exists(filepath):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(filepath)
                    # Set default volumes
                    if sound_name == 'shoot':
                        self.sounds[sound_name].set_volume(0.5)
                    else:
                        self.sounds[sound_name].set_volume(0.7)
                    print(f"Successfully loaded: {filename}")
                except pygame.error as e:
                    print(f"Could not load sound {filename}: {e}")
                    print(f"Make sure the file format is supported (WAV or OGG)")
                    self.sounds[sound_name] = None
                except Exception as e:
                    print(f"Unexpected error loading {filename}: {e}")
                    self.sounds[sound_name] = None
            else:
                print(f"Sound file not found: {filepath}")
                self.sounds[sound_name] = None
    
    def play(self, sound_name):
        """Play a sound effect"""
        if not self.enabled:
            return
        
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")
    
    def set_volume(self, sound_name, volume):
        """Set volume for a specific sound (0.0 to 1.0)"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].set_volume(volume)
    
    def set_master_volume(self, volume):
        """Set master volume for all sounds"""
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(volume)
    
    def toggle_enabled(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        return self.enabled
    
    def is_enabled(self):
        """Check if sound is enabled"""
        return self.enabled
    
    def play_ambient(self, sound_name, loops=-1, fade_ms=1000):
        """Play ambient music on loop"""
        if not self.enabled:
            return
        
        # Stop current ambient if playing
        self.stop_ambient(fade_ms=500)
        
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.current_ambient = sound_name
                # Play with fade in and loop forever (-1)
                self.ambient_channel.play(self.sounds[sound_name], loops=loops, fade_ms=fade_ms)
                self.ambient_channel.set_volume(0.15)  # Much lower volume for subtle ambient
            except Exception as e:
                print(f"Error playing ambient {sound_name}: {e}")
    
    def stop_ambient(self, fade_ms=1000):
        """Stop ambient music with fade out"""
        if self.ambient_channel and self.ambient_channel.get_busy():
            self.ambient_channel.fadeout(fade_ms)
            self.current_ambient = None
    
    def pause_ambient(self):
        """Pause ambient music"""
        if self.ambient_channel:
            self.ambient_channel.pause()
    
    def resume_ambient(self):
        """Resume ambient music"""
        if self.ambient_channel:
            self.ambient_channel.unpause()

# Global sound manager instance
_sound_manager = None

def get_sound_manager():
    """Get the global sound manager instance"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager