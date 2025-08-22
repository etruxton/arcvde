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
        self.effects_channel = None
        self.current_effect = None
        
        # Initialize pygame mixer (with settings that work well for both WAV and OGG)
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Set volume
        pygame.mixer.set_num_channels(8)  # Allow 8 simultaneous sounds
        
        # Reserve channel 0 for ambient music
        self.ambient_channel = pygame.mixer.Channel(0)
        # Reserve channel 1 for stage ambient effects
        self.effects_channel = pygame.mixer.Channel(1)
        
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
            'boss_battle': 'boss_battle_8_metal_loop.ogg',  # Legacy - keep for compatibility
            # Stage-specific music for Doomsday mode
            'stage1_music': 'boss_battle_3_alternate.ogg',  # Stage 1 music
            'stage2_music': 'Boss Battle 4 V1.ogg',  # Stage 2 music  
            'stage3_music': 'Boss Battle 6 V1.ogg',  # Stage 3 music
            'stage4_music1': 'boss_battle_8_retro_01_loop.ogg',  # Stage 4+ first track
            'stage4_music2': 'boss_battle_8_retro_02_loop.ogg',  # Stage 4+ second track
            # Stage atmospheric sound effects
            'stage2_fire_crackle': 'stage2_fire_crackle.wav',
            'stage2_fire_ambient': 'stage2_fire_ambient.wav',
            'stage3_static_mist': 'stage3_static_mist.wav',
            'stage4_lightning': 'stage4_lightning.wav',
            'stage4_thunder': 'stage4_thunder.wav',
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
                    elif 'stage2_fire' in sound_name:
                        self.sounds[sound_name].set_volume(0.6)  # Fire sounds at moderate volume
                    elif 'stage3_static' in sound_name:
                        self.sounds[sound_name].set_volume(0.5)  # Static at moderate volume
                    elif 'stage4' in sound_name:
                        self.sounds[sound_name].set_volume(0.6)  # Lightning/thunder
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
    
    def get_stage_music(self, stage: int) -> str:
        """Get the appropriate music track name for a given stage"""
        if stage == 1:
            return 'stage1_music'
        elif stage == 2:
            return 'stage2_music'
        elif stage == 3:
            return 'stage3_music'
        else:  # Stage 4+
            return 'stage4_music1'  # Start with first track for stage 4+
    
    def get_next_stage4_track(self, current_track: str) -> str:
        """Get the next track in the Stage 4+ alternating sequence"""
        if current_track == 'stage4_music1':
            return 'stage4_music2'
        else:
            return 'stage4_music1'
    
    def is_ambient_finished(self) -> bool:
        """Check if current ambient music has finished playing"""
        return self.ambient_channel and not self.ambient_channel.get_busy()
    
    def play_stage_music(self, stage: int, loops: int = -1, fade_ms: int = 1000) -> str:
        """Play appropriate music for a stage and return the track name"""
        track_name = self.get_stage_music(stage)
        self.play_ambient(track_name, loops=loops, fade_ms=fade_ms)
        return track_name
    
    def play_stage_effect(self, effect_name: str, loops: int = -1, volume: float = 0.3):
        """Play a stage ambient effect on the effects channel"""
        if not self.enabled:
            return
        
        # Stop current effect if playing
        self.stop_stage_effect()
        
        if effect_name in self.sounds and self.sounds[effect_name]:
            try:
                self.current_effect = effect_name
                self.effects_channel.play(self.sounds[effect_name], loops=loops)
                self.effects_channel.set_volume(volume)
            except Exception as e:
                print(f"Error playing stage effect {effect_name}: {e}")
    
    def stop_stage_effect(self, fade_ms: int = 500):
        """Stop the current stage effect"""
        if self.effects_channel and self.effects_channel.get_busy():
            self.effects_channel.fadeout(fade_ms)
            self.current_effect = None
    
    def play_one_shot_effect(self, effect_name: str, volume: float = 0.5):
        """Play a one-shot sound effect (like lightning) on any available channel"""
        if not self.enabled:
            return
        
        if effect_name in self.sounds and self.sounds[effect_name]:
            try:
                # Find an available channel (skip 0 and 1 which are reserved)
                for i in range(2, 8):
                    channel = pygame.mixer.Channel(i)
                    if not channel.get_busy():
                        channel.play(self.sounds[effect_name])
                        channel.set_volume(volume)
                        break
            except Exception as e:
                print(f"Error playing one-shot effect {effect_name}: {e}")

# Global sound manager instance
_sound_manager = None

def get_sound_manager():
    """Get the global sound manager instance"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager