#!/usr/bin/env python3
"""
Generate atmospheric sound effects for different stages in Doomsday mode
"""

import numpy as np
import wave
import struct
import random

def save_wav(filename, audio_data, sample_rate=44100):
    """Save audio data as WAV file"""
    # Normalize to 16-bit range
    audio_data = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    print(f"Generated: {filename}")

def generate_fire_crackling(duration=3.0, sample_rate=44100):
    """Generate fire crackling sound for Stage 2"""
    samples = int(duration * sample_rate)
    
    # Base layer: Pink noise for fire ambience
    pink_noise = np.random.randn(samples)
    
    # Apply low-pass filter effect (simple moving average)
    window_size = 5
    pink_noise = np.convolve(pink_noise, np.ones(window_size)/window_size, mode='same')
    
    # Add crackling pops
    crackles = np.zeros(samples)
    num_crackles = int(sample_rate * duration / 50)  # About 20 crackles per second
    
    for _ in range(num_crackles):
        pos = random.randint(0, samples - 100)
        # Create a short burst
        burst_length = random.randint(20, 80)
        burst = np.random.randn(burst_length) * random.uniform(0.3, 0.8)
        # Apply envelope
        envelope = np.hanning(burst_length)
        burst *= envelope
        crackles[pos:pos+burst_length] += burst
    
    # Combine layers
    fire_sound = pink_noise * 0.3 + crackles * 0.7
    
    # Add some low frequency rumble
    t = np.linspace(0, duration, samples)
    rumble = np.sin(2 * np.pi * 60 * t) * 0.1
    rumble += np.sin(2 * np.pi * 80 * t) * 0.05
    
    fire_sound += rumble
    
    # Apply soft clipping
    fire_sound = np.tanh(fire_sound * 0.5) * 2
    
    return fire_sound

def generate_static_mist(duration=5.0, sample_rate=44100):
    """Generate loopable ethereal static/mist sound for Stage 3"""
    samples = int(duration * sample_rate)
    
    # White noise base - consistent throughout
    white_noise = np.random.randn(samples) * 0.25
    
    # Apply smoother filtering for consistent sound
    filtered = white_noise.copy()
    
    # Simple low-pass filter for warmth
    alpha = 0.3
    for i in range(1, len(filtered)):
        filtered[i] = alpha * filtered[i] + (1 - alpha) * filtered[i-1]
    
    # Add subtle, continuous ethereal tones
    t = np.linspace(0, duration, samples)
    
    # Use integer multiples of duration for seamless looping
    cycles_1 = int(duration * 2)  # 2 cycles over duration
    cycles_2 = int(duration * 3)  # 3 cycles over duration
    
    # Simple sine waves that loop perfectly
    tone1 = np.sin(2 * np.pi * cycles_1 * t / duration) * 0.05
    tone2 = np.sin(2 * np.pi * cycles_2 * t / duration) * 0.04
    
    # Combine all elements
    static_sound = filtered * 0.7 + tone1 + tone2
    
    # Create seamless loop with crossfade
    crossfade_samples = int(0.5 * sample_rate)
    
    if crossfade_samples < len(static_sound) // 2:
        # Create crossfade weight
        crossfade = np.linspace(0, 1, crossfade_samples)
        
        # Store original beginning and end
        original_start = static_sound[:crossfade_samples].copy()
        original_end = static_sound[-crossfade_samples:].copy()
        
        # Crossfade the beginning and end together
        static_sound[:crossfade_samples] = original_start * crossfade + original_end * (1 - crossfade)
        static_sound[-crossfade_samples:] = original_end * crossfade + original_start * (1 - crossfade)
    
    return static_sound

def generate_lightning_thunder(duration=2.0, sample_rate=44100):
    """Generate lightning/thunder sound for Stage 4"""
    samples = int(duration * sample_rate)
    
    # Initial lightning crack (very short, high frequency)
    crack_duration = 0.05
    crack_samples = int(crack_duration * sample_rate)
    
    # High frequency burst for lightning
    t_crack = np.linspace(0, crack_duration, crack_samples)
    lightning = np.zeros(samples)
    
    # Multiple frequency components for electric sound
    crack_sound = (
        np.sin(2 * np.pi * 4000 * t_crack) * 0.5 +
        np.sin(2 * np.pi * 6000 * t_crack) * 0.3 +
        np.sin(2 * np.pi * 8000 * t_crack) * 0.2 +
        np.random.randn(crack_samples) * 0.8  # Add noise for electric effect
    )
    
    # Sharp attack envelope
    crack_envelope = np.exp(-t_crack * 50)
    crack_sound *= crack_envelope
    
    lightning[:crack_samples] = crack_sound
    
    # Thunder rumble (starts after lightning)
    thunder_start = int(0.1 * sample_rate)
    thunder_samples = samples - thunder_start
    
    # Low frequency rumble
    thunder = np.random.randn(thunder_samples)
    
    # Apply multiple low-pass filters for deep rumble
    for _ in range(3):
        # Simple low-pass filter
        alpha = 0.1
        for i in range(1, len(thunder)):
            thunder[i] = alpha * thunder[i] + (1 - alpha) * thunder[i-1]
    
    # Add some low frequency sine waves
    t_thunder = np.linspace(0, duration - 0.1, thunder_samples)
    thunder += np.sin(2 * np.pi * 30 * t_thunder) * 0.3
    thunder += np.sin(2 * np.pi * 50 * t_thunder) * 0.2
    thunder += np.sin(2 * np.pi * 80 * t_thunder) * 0.1
    
    # Thunder envelope (gradual build and decay)
    thunder_envelope = np.ones(thunder_samples)
    
    # Build up
    buildup = int(0.3 * sample_rate)
    thunder_envelope[:buildup] = np.linspace(0, 1, buildup)
    
    # Decay
    decay_start = int(0.8 * sample_rate)
    if decay_start < thunder_samples:
        decay_samples = thunder_samples - decay_start
        thunder_envelope[decay_start:] = np.linspace(1, 0, decay_samples)
    
    thunder *= thunder_envelope * 0.8
    
    # Add thunder to the lightning array
    lightning[thunder_start:] += thunder
    
    # Add some echo/reverb effect
    delay_samples = int(0.15 * sample_rate)
    if delay_samples < samples:
        echo = lightning.copy() * 0.3
        lightning[delay_samples:] += echo[:-delay_samples]
    
    return lightning

def generate_ambient_fire_loop(duration=5.0, sample_rate=44100):
    """Generate a loopable ambient fire sound for continuous playback"""
    samples = int(duration * sample_rate)
    
    # Consistent crackling fire ambience
    fire_ambient = np.random.randn(samples) * 0.2
    
    # Low-pass filter for warmth
    alpha = 0.3
    for i in range(1, len(fire_ambient)):
        fire_ambient[i] = alpha * fire_ambient[i] + (1 - alpha) * fire_ambient[i-1]
    
    # Add continuous low rumble
    t = np.linspace(0, duration, samples)
    rumble = np.sin(2 * np.pi * 50 * t) * 0.1
    rumble += np.sin(2 * np.pi * 70 * t) * 0.05
    
    fire_ambient += rumble
    
    # Make it loop smoothly
    fade_samples = int(0.5 * sample_rate)
    crossfade = np.linspace(0, 1, fade_samples)
    
    # Crossfade beginning and end
    original_start = fire_ambient[:fade_samples].copy()
    original_end = fire_ambient[-fade_samples:].copy()
    
    fire_ambient[:fade_samples] = original_start * (1 - crossfade) + original_end * crossfade
    fire_ambient[-fade_samples:] = original_end * (1 - crossfade) + original_start * crossfade
    
    return fire_ambient

def main():
    """Generate all sound effects"""
    print("Generating stage sound effects...")
    
    # Stage 2: Fire crackling
    fire_sound = generate_fire_crackling(duration=2.0)
    save_wav("../sounds/stage2_fire_crackle.wav", fire_sound)
    
    # Stage 2: Ambient fire loop
    fire_ambient = generate_ambient_fire_loop(duration=4.0)
    save_wav("../sounds/stage2_fire_ambient.wav", fire_ambient)
    
    # Stage 3: Static/mist - longer duration for better looping
    static_sound = generate_static_mist(duration=5.0)
    save_wav("../sounds/stage3_static_mist.wav", static_sound)
    
    # Stage 4: Lightning/thunder
    lightning_sound = generate_lightning_thunder(duration=2.5)
    save_wav("../sounds/stage4_lightning.wav", lightning_sound)
    
    # Stage 4: Just thunder (for variety)
    thunder_only = generate_lightning_thunder(duration=3.0)
    # Remove the initial crack
    thunder_only[:int(0.1 * 44100)] *= 0.1
    save_wav("../sounds/stage4_thunder.wav", thunder_only)
    
    print("\nAll sound effects generated successfully!")
    print("Files saved in the ../sounds/ directory")

if __name__ == "__main__":
    main()