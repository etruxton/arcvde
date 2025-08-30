"""
Sound Manager for handling game audio effects
"""

# Standard library imports
import os

# Third-party imports
import pygame


class SoundManager:
    """Manages all game sound effects"""

    def __init__(self):
        """Initialize the sound manager"""
        print("=== SOUND MANAGER INITIALIZATION ===")
        
        # Check system info
        import platform
        import os
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Architecture: {platform.machine()}")
        print(f"Python: {platform.python_version()}")
        print(f"Is WSL: {'WSL' in os.uname().release if hasattr(os, 'uname') else 'Unknown'}")
        
        # Check environment variables that might affect audio
        print(f"PULSE_RUNTIME_PATH: {os.environ.get('PULSE_RUNTIME_PATH', 'Not set')}")
        print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
        print(f"SDL_AUDIODRIVER: {os.environ.get('SDL_AUDIODRIVER', 'Not set')}")
        
        self.enabled = True
        self.sounds = {}
        self.ambient_channel = None
        self.current_ambient = None
        self.effects_channel = None
        self.current_effect = None
        
        # Store base volumes separately since we can't add attributes to pygame Sound objects
        self.base_volumes = {}

        # Check if pygame is already initialized
        print(f"Pygame already initialized: {pygame.get_init()}")
        
        # Initialize pygame mixer (with settings that work well for both WAV and OGG)
        try:
            print("Initializing pygame mixer...")
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print(f"Pygame mixer initialized successfully")
            print(f"Mixer settings: {pygame.mixer.get_init()}")
        except Exception as e:
            print(f"ERROR: Failed to initialize pygame mixer: {e}")
            self.enabled = False
            return

        # Set volume
        pygame.mixer.set_num_channels(8)  # Allow 8 simultaneous sounds
        
        # Initialize master volume (will be loaded after sounds are loaded)
        self.master_volume = 0.7  # Default volume

        # Reserve channel 0 for ambient music
        self.ambient_channel = pygame.mixer.Channel(0)
        # Reserve channel 1 for stage ambient effects
        self.effects_channel = pygame.mixer.Channel(1)

        # Load sound effects
        self._load_sounds()
        
        # Load saved volume settings after sounds are loaded
        self._load_saved_volume()
        
        # Create fallback sounds for essential sounds that failed to load
        self._create_fallback_sounds()

    def _load_sounds(self):
        """Load all sound effects"""
        print("=== LOADING SOUND EFFECTS ===")
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sounds")
        print(f"Sound directory: {sound_dir}")
        print(f"Sound directory exists: {os.path.exists(sound_dir)}")
        
        if os.path.exists(sound_dir):
            print(f"Contents of sound directory: {os.listdir(sound_dir)}")
        else:
            print("ERROR: Sound directory does not exist!")

        # Define sound files to load (supports both .wav and .ogg)
        sound_files = {
            "shoot": "shoot.wav",
            "hit": "hit.wav",
            "enemy_hit": "hit.wav",  # Can use same or different sound
            "enemy_death": "hit.wav",  # Can be customized later
            "elevator": "Peachtea - Somewhere in the Elevator.ogg",  # Ambient music for menu
            "capybara_hunt": "DayAndNight-modified.ogg",  # Music for Capybara Hunt mode
            "boss_battle": "boss_battle_8_metal_loop.ogg",  # Legacy - keep for compatibility
            # Stage-specific music for Doomsday mode
            "stage1_music": "boss_battle_3_alternate.ogg",
            "stage2_music": "Boss Battle 4 V1.ogg",
            "stage3_music": "Boss Battle 6 V1.ogg",
            "stage4_music1": "boss_battle_8_retro_01_loop.ogg",
            "stage4_music2": "boss_battle_8_retro_02_loop.ogg",
            "stage4_music3": "boss_battle_8_metal_loop.ogg",
            # Stage atmospheric sound effects
            "stage2_fire_crackle": "stage2_fire_crackle.wav",
            "stage2_fire_ambient": "stage2_fire_ambient.wav",
            "stage3_static_mist": "stage3_static_mist.wav",
            "stage4_lightning": "stage4_lightning.wav",
            "stage4_thunder": "stage4_thunder.wav",
        }

        # Load each sound
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(sound_dir, filename)
            if os.path.exists(filepath):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(filepath)
                    # Set default volumes (relative to master volume)
                    if sound_name == "shoot":
                        base_volume = 0.3  # Lower shooting volume
                    elif sound_name in ["hit", "enemy_hit", "enemy_death"]:
                        base_volume = 0.4  # Lower hit sound volumes
                    elif "stage2_fire" in sound_name:
                        base_volume = 0.6  # Fire sounds at moderate volume
                    elif "stage3_static" in sound_name:
                        base_volume = 0.5  # Static at moderate volume
                    elif "stage4" in sound_name:
                        base_volume = 0.6  # Lightning/thunder
                    else:
                        base_volume = 0.7
                    
                    # Store base volume for later scaling
                    self.base_volumes[sound_name] = base_volume
                    # Apply current master volume with non-linear scaling
                    import math
                    self.sounds[sound_name].set_volume(base_volume * math.sqrt(self.master_volume))
                    print(f"Successfully loaded: {filename}")
                except pygame.error as e:
                    print(f"Could not load sound {filename}: {e}")
                    print("Make sure the file format is supported (WAV or OGG)")
                    self.sounds[sound_name] = None
                except Exception as e:
                    print(f"Unexpected error loading {filename}: {e}")
                    print(f"Full traceback for {filename}:")
                    import traceback
                    traceback.print_exc()
                    self.sounds[sound_name] = None
            else:
                print(f"Sound file not found: {filepath}")
                self.sounds[sound_name] = None

    def _load_saved_volume(self):
        """Load saved volume settings and apply to all sounds"""
        try:
            from utils.settings_manager import get_settings_manager
            settings_manager = get_settings_manager()
            saved_volume = settings_manager.get("master_volume", 0.7)
            self.set_master_volume(saved_volume)
            print(f"Loaded saved volume: {saved_volume:.1%}")
        except Exception as e:
            print(f"Could not load saved volume: {e}")
            self.set_master_volume(0.7)

    def _test_pygame_audio(self):
        """Test if pygame mixer can produce any sound at all"""
        print("=== TESTING PYGAME AUDIO CAPABILITIES ===")
        try:
            import numpy as np
            
            # Generate a simple 440Hz test tone
            duration = 0.1  # 100ms
            sample_rate = 44100
            frames = int(duration * sample_rate)
            
            # Create a sine wave
            arr = np.zeros((frames, 2), dtype=np.int16)
            for i in range(frames):
                val = int(16383 * np.sin(2 * np.pi * 440 * i / sample_rate))
                arr[i][0] = val  # Left channel
                arr[i][1] = val  # Right channel
            
            # Create pygame sound from array
            test_sound = pygame.sndarray.make_sound(arr)
            test_sound.set_volume(0.3)  # Moderate volume
            
            print("Generated test tone, attempting to play...")
            result = test_sound.play()
            print(f"Test sound play result: {result}")
            print("If you can't hear a short beep, there's a system audio issue")
            
        except ImportError:
            print("NumPy not available - trying simpler test...")
            # Try to create a simple click sound
            try:
                # Create a very simple sound buffer
                import array
                buf = array.array('h')
                for i in range(1000):  # Short click
                    buf.append(int(10000 if i < 100 else 0))
                
                test_sound = pygame.sndarray.make_sound(buf)
                test_sound.set_volume(0.5)
                result = test_sound.play()
                print(f"Simple test sound result: {result}")
            except Exception as e:
                print(f"Simple test failed: {e}")
        except Exception as e:
            print(f"Audio test failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Test loading a simple sound file to see if pygame can load sounds at all
        try:
            print("=== TESTING SOUND FILE LOADING ===")
            # Try to load one of our sound files directly
            test_sound_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sounds", "shoot.wav")
            print(f"Testing sound file: {test_sound_path}")
            print(f"File exists: {os.path.exists(test_sound_path)}")
            
            if os.path.exists(test_sound_path):
                # Get file info
                stat = os.stat(test_sound_path)
                print(f"File size: {stat.st_size} bytes")
                
                # Try to load it
                test_sound = pygame.mixer.Sound(test_sound_path)
                print(f"Successfully loaded test sound: {test_sound}")
                print(f"Sound length: {test_sound.get_length()} seconds")
                
                # Try to play it
                print("Attempting to play test sound...")
                result = test_sound.play()
                print(f"Play result: {result}")
                
            else:
                print("Test sound file not found")
                
        except Exception as e:
            print(f"Sound file loading test failed: {e}")
            import traceback
            traceback.print_exc()

    def _create_fallback_sounds(self):
        """Create simple fallback sounds for essential effects that failed to load"""
        print("=== CREATING FALLBACK SOUNDS ===")
        
        # Check which essential sounds failed to load
        essential_sounds = ["shoot", "hit"]
        
        for sound_name in essential_sounds:
            if sound_name in self.sounds and self.sounds[sound_name] is None:
                print(f"Creating fallback sound for '{sound_name}'...")
                try:
                    # Create a simple synthetic sound
                    if sound_name == "shoot":
                        # Create a short "pew" sound
                        fallback_sound = self._create_pew_sound()
                    elif sound_name == "hit":
                        # Create a short "pop" sound
                        fallback_sound = self._create_pop_sound()
                    
                    if fallback_sound:
                        self.sounds[sound_name] = fallback_sound
                        # Use the same lower base volumes for fallback sounds
                        if sound_name == "shoot":
                            self.base_volumes[sound_name] = 0.3
                        elif sound_name == "hit":
                            self.base_volumes[sound_name] = 0.4
                        else:
                            self.base_volumes[sound_name] = 0.5
                        print(f"Successfully created fallback sound for '{sound_name}'")
                    
                except Exception as e:
                    print(f"Failed to create fallback sound for '{sound_name}': {e}")

    def _create_pew_sound(self):
        """Create a simple 'pew' sound effect"""
        try:
            import numpy as np
            duration = 0.1  # 100ms
            sample_rate = 22050  # Lower sample rate for simpler sound
            frames = int(duration * sample_rate)
            
            # Create a frequency sweep from 800Hz to 200Hz (pew effect)
            # Make it stereo (2 channels)
            arr = np.zeros((frames, 2), dtype=np.int16)
            for i in range(frames):
                t = i / sample_rate
                # Frequency sweep with exponential decay
                freq = 800 * (0.25 ** (t * 10))  # Sweep down quickly
                amplitude = 8000 * np.exp(-t * 10)  # Decay amplitude
                sample_val = int(amplitude * np.sin(2 * np.pi * freq * t))
                arr[i][0] = sample_val  # Left channel
                arr[i][1] = sample_val  # Right channel
            
            return pygame.sndarray.make_sound(arr)
        except ImportError:
            # Fallback without numpy
            return self._create_simple_click()
        except Exception as e:
            print(f"Failed to create pew sound: {e}")
            return None

    def _create_pop_sound(self):
        """Create a simple 'pop' sound effect"""
        try:
            import numpy as np
            duration = 0.05  # 50ms
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            # Create a sharp click with some resonance
            # Make it stereo (2 channels)
            arr = np.zeros((frames, 2), dtype=np.int16)
            for i in range(frames):
                t = i / sample_rate
                # Quick burst at 1000Hz with fast decay
                amplitude = 12000 * np.exp(-t * 50)
                sample_val = int(amplitude * np.sin(2 * np.pi * 1000 * t))
                arr[i][0] = sample_val  # Left channel
                arr[i][1] = sample_val  # Right channel
            
            return pygame.sndarray.make_sound(arr)
        except ImportError:
            return self._create_simple_click()
        except Exception as e:
            print(f"Failed to create pop sound: {e}")
            return None

    def _create_simple_click(self):
        """Create a very simple click sound without numpy"""
        try:
            import array
            # Create a short click
            buf = array.array('h')
            for i in range(500):  # Very short sound
                if i < 10:
                    buf.append(8000)  # Sharp attack
                elif i < 50:
                    buf.append(int(8000 * (50-i)/40))  # Quick decay
                else:
                    buf.append(0)
            
            return pygame.sndarray.make_sound(buf)
        except Exception as e:
            print(f"Failed to create simple click: {e}")
            return None

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
        self.master_volume = volume
        import math
        
        # Use non-linear scaling for all sounds to make volume changes more dramatic
        volume_scaling_factor = math.sqrt(volume)
        
        for sound_name, sound in self.sounds.items():
            if sound and sound_name in self.base_volumes:
                # Scale the base volume using non-linear scaling
                base_vol = self.base_volumes[sound_name]
                new_volume = base_vol * volume_scaling_factor
                sound.set_volume(new_volume)
            elif sound:
                # Fallback for sounds without base volume stored
                fallback_volume = 0.7 * volume_scaling_factor
                sound.set_volume(fallback_volume)
        
        # Update channel volumes as well
        if self.current_ambient and self.ambient_channel:
            # Music uses a higher multiplier for more prominent presence
            ambient_volume = 0.8 * volume_scaling_factor
            self.ambient_channel.set_volume(ambient_volume)
        if self.current_effect and self.effects_channel:
            effects_volume = 0.3 * volume_scaling_factor
            self.effects_channel.set_volume(effects_volume)

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
                
                # Scale ambient volume with non-linear scaling for more dramatic changes
                import math
                volume = 0.8 * math.sqrt(self.master_volume)
                self.ambient_channel.set_volume(volume)
                
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
            return "stage1_music"
        elif stage == 2:
            return "stage2_music"
        elif stage == 3:
            return "stage3_music"
        else:  # Stage 4+
            return "stage4_music1"  # Start with first track for stage 4+

    def get_next_stage4_track(self, current_track: str) -> str:
        """Get the next track in the Stage 4+ alternating sequence"""
        if current_track == "stage4_music1":
            return "stage4_music2"
        elif current_track == "stage4_music2":
            return "stage4_music3"
        else:  # stage4_music3 or any other value
            return "stage4_music1"

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
                # Scale the provided volume using non-linear master volume scaling
                import math
                final_volume = volume * math.sqrt(self.master_volume)
                self.effects_channel.set_volume(final_volume)
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
                        # Use non-linear scaling for one-shot effects too
                        import math
                        channel.set_volume(volume * math.sqrt(self.master_volume))
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
