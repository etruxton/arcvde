"""
Audio management for Doomsday stage system
"""

# Standard library imports
import random


class StageAudio:
    """Manages audio and music for doomsday stages"""

    def __init__(self, sound_manager):
        self.sound_manager = sound_manager

        # Music tracking
        self.current_music_track = None
        self.music_started = False

    def start_stage_music(self, stage: int) -> None:
        """Start the appropriate music for a given stage"""
        if not hasattr(self.sound_manager, "play_stage_music"):
            return

        if stage == 4:
            # Stage 4 uses special alternating system
            self.current_music_track = self.sound_manager.get_stage_music(stage)
            self.sound_manager.play_stage_music(stage, loops=0)
            self.music_started = True
            return stage  # Return stage number to enable alternating mode
        else:
            # Other stages loop indefinitely
            self.current_music_track = self.sound_manager.play_stage_music(stage, loops=-1)
            self.music_started = True
            return None  # No alternating mode needed

        # Stage-specific ambient effects
        if stage == 2:
            # Hell's Gates - fire ambient
            self.sound_manager.play_stage_effect("stage2_fire_ambient", loops=-1, volume=0.08)
        elif stage == 3:
            # Demon Realm - static/mist ambient
            self.sound_manager.play_stage_effect("stage3_static_mist", loops=-1, volume=0.2)
        elif stage == 1:
            # Forest Path - stop any ambient effects
            self.sound_manager.stop_stage_effect()
        elif stage == 4:
            # Final Apocalypse - stop ambient effects for music focus
            self.sound_manager.stop_stage_effect()

    def handle_stage4_music_alternation(self) -> None:
        """Handle the alternating music logic for Stage 4+"""
        # Only handle if we're actually playing stage 4 music
        if self.sound_manager.is_ambient_finished():
            # Get next track in the alternation sequence
            next_track = self.sound_manager.get_next_stage4_track(self.current_music_track)
            print(f"Stage 4 music alternation: {self.current_music_track} -> {next_track}")

            self.current_music_track = next_track

            # Play the track with appropriate settings
            if next_track == "stage4_music3":
                self.sound_manager.play_ambient(next_track, loops=-1, fade_ms=1000)
            else:
                self.sound_manager.play_ambient(next_track, loops=0, fade_ms=1000)

            print(f"Now playing: {next_track}")

    def handle_stage_transition_audio(self, old_theme: int, new_theme: int) -> None:
        """Handle audio during stage transitions"""
        # Play transition sound effect
        if hasattr(self.sound_manager, "play_stage_transition"):
            self.sound_manager.play_stage_transition(new_theme)

        # Start new stage music
        self.start_stage_music(new_theme)

    def play_stage_effect(self, effect_name: str, **kwargs) -> None:
        """Play a stage-specific sound effect"""
        if hasattr(self.sound_manager, "play_one_shot_effect"):
            self.sound_manager.play_one_shot_effect(effect_name, **kwargs)

    def play_fire_crackle_effect(self, volume: float = 0.05) -> None:
        """Play fire crackling sound for stage 2"""
        if random.random() < 0.02:  # 2% chance per frame
            self.play_stage_effect("stage2_fire_crackle", volume=volume)

    def play_lightning_effects(self) -> None:
        """Play lightning/thunder effects for stage 4"""
        if hasattr(self.sound_manager, "play_one_shot_effect"):
            if random.random() < 0.3:  # 30% chance for lightning
                self.sound_manager.play_one_shot_effect("stage4_lightning", volume=0.4)
            if random.random() < 0.2:  # 20% chance for thunder
                self.sound_manager.play_one_shot_effect("stage4_thunder", volume=0.3)

    def stop_stage_effects(self) -> None:
        """Stop all stage ambient effects"""
        self.sound_manager.stop_stage_effect()

    def reset(self) -> None:
        """Reset audio manager to initial state"""
        self.current_music_track = None
        self.music_started = False
        self.stop_stage_effects()
