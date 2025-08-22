"""
Generate simple sound effects for the game
"""

# Standard library imports
import struct
import wave as wave_module

# Third-party imports
import numpy as np


def generate_shoot_sound(filename="../sounds/shoot.wav", duration=0.15, sample_rate=44100):
    """Generate a simple shooting sound effect"""

    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create a gunshot-like sound with multiple components:
    # 1. Initial bang (low frequency with quick decay)
    bang = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 30)

    # 2. Mid-range crack (higher frequency, shorter)
    crack = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 50) * 0.5

    # 3. High frequency pop
    pop = np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 100) * 0.3

    # 4. Noise component for realism
    noise = np.random.normal(0, 0.1, len(t)) * np.exp(-t * 20)

    # Combine all components
    sound = bang + crack + pop + noise

    # Normalize to prevent clipping
    sound = sound / np.max(np.abs(sound)) * 0.8

    # Convert to 16-bit integer
    sound_int = np.int16(sound * 32767)

    # Write WAV file
    with wave_module.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(sound_int.tobytes())

    print(f"Generated {filename}")


def generate_hit_sound(filename="../sounds/hit.wav", duration=0.2, sample_rate=44100):
    """Generate a hit/impact sound effect"""

    t = np.linspace(0, duration, int(sample_rate * duration))

    # Impact thud
    thud = np.sin(2 * np.pi * 100 * t) * np.exp(-t * 25)

    # Metallic ring
    ring = np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 15) * 0.4

    # Crunch noise
    noise = np.random.normal(0, 0.2, len(t)) * np.exp(-t * 30)

    sound = thud + ring + noise
    sound = sound / np.max(np.abs(sound)) * 0.7

    sound_int = np.int16(sound * 32767)

    with wave_module.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(sound_int.tobytes())

    print(f"Generated {filename}")


def generate_ambient_menu_sound(filename="../sounds/menu_ambient.wav", duration=30, sample_rate=44100):
    """Generate a calm, ambient menu background sound with random notes"""
    # Standard library imports
    import random

    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create multiple layers for ambient sound (reduced volumes)
    # 1. Very soft low drone
    drone = np.sin(2 * np.pi * 60 * t) * 0.05
    drone += np.sin(2 * np.pi * 90 * t) * 0.03

    # 2. Very subtle background atmosphere
    atmosphere = np.sin(2 * np.pi * 220 * t) * np.sin(2 * np.pi * 0.05 * t) * 0.02

    # 3. Soft noise layer for texture (reduced)
    noise = np.random.normal(0, 0.01, len(t))
    window_size = 100
    noise_filtered = np.convolve(noise, np.ones(window_size) / window_size, mode="same")

    # 4. Random notes that play occasionally
    # Musical notes in a pleasant scale (pentatonic)
    notes = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33]  # C, D, E, G, A, C, D
    random_notes = np.zeros(len(t))

    # Add random notes at random times
    num_notes = random.randint(8, 15)  # Number of notes to play
    for _ in range(num_notes):
        note_freq = random.choice(notes)
        start_time = random.uniform(0, duration - 0.5)
        note_duration = random.uniform(0.2, 0.8)  # Short notes

        start_idx = int(start_time * sample_rate)
        end_idx = min(int((start_time + note_duration) * sample_rate), len(t))

        if start_idx < len(t):
            # Create a note with envelope
            note_t = t[start_idx:end_idx] - t[start_idx]
            note_len = len(note_t)

            # Create ADSR envelope (Attack, Decay, Sustain, Release)
            envelope = np.ones(note_len)

            # Attack (10% of note duration)
            attack_len = int(note_len * 0.1)
            if attack_len > 0:
                envelope[:attack_len] = np.linspace(0, 1, attack_len)

            # Decay to sustain (20% of note duration)
            decay_len = int(note_len * 0.2)
            decay_start = attack_len
            decay_end = decay_start + decay_len
            if decay_end <= note_len:
                envelope[decay_start:decay_end] = np.linspace(1, 0.7, decay_len)

            # Sustain (40% of note duration)
            sustain_end = int(note_len * 0.7)
            if decay_end < sustain_end:
                envelope[decay_end:sustain_end] = 0.7

            # Release (last 30% of note duration - smooth fade out)
            release_start = sustain_end
            if release_start < note_len:
                envelope[release_start:] = np.linspace(0.7, 0, note_len - release_start)

            # Apply a smoother overall decay
            envelope *= np.exp(-note_t * 1.5)  # Gentler exponential decay

            note_signal = np.sin(2 * np.pi * note_freq * note_t) * envelope * 0.08
            random_notes[start_idx:end_idx] += note_signal

    # Combine all layers
    sound = drone + atmosphere + noise_filtered + random_notes

    # Apply fade in and fade out
    fade_duration = 2.0  # 2 seconds fade
    fade_samples = int(fade_duration * sample_rate)

    # Fade in
    fade_in = np.linspace(0, 1, fade_samples)
    sound[:fade_samples] *= fade_in

    # Fade out
    fade_out = np.linspace(1, 0, fade_samples)
    sound[-fade_samples:] *= fade_out

    # Normalize (even quieter)
    sound = sound / np.max(np.abs(sound)) * 0.25  # Much quieter for subtle background

    # Convert to 16-bit integer
    sound_int = np.int16(sound * 32767)

    # Write WAV file
    with wave_module.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(sound_int.tobytes())

    print(f"Generated {filename}")


if __name__ == "__main__":
    # Generate sound effects
    generate_shoot_sound()
    generate_hit_sound()
    generate_ambient_menu_sound()
    print("Sound effects generated successfully!")
