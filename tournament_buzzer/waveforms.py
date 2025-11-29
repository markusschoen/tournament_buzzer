"""Waveform generation functions for different buzzer sounds.

Each function generates a numpy array representing a stereo audio waveform.
Functions are pure and stateless - they take parameters and return data.
"""

import numpy as np

from .config import AudioConfig


def generate_sine_wave(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * frequency * t)


def generate_square_wave(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a square wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return amplitude * np.sign(np.sin(2 * np.pi * frequency * t))


def generate_frequency_sweep(
    start_freq: float,
    end_freq: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a linear frequency sweep (chirp)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    k = (end_freq - start_freq) / duration
    phase = 2 * np.pi * (start_freq * t + 0.5 * k * t**2)
    return amplitude * np.sin(phase)


def generate_two_tone(
    freq1: float,
    freq2: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a two-tone alternating signal."""
    half_duration = duration / 2
    t_half = np.linspace(0, half_duration, int(sample_rate * half_duration), endpoint=False)
    tone1 = np.sin(2 * np.pi * freq1 * t_half)
    tone2 = np.sin(2 * np.pi * freq2 * t_half)
    return amplitude * np.concatenate((tone1, tone2))


def apply_fade_out(wave: np.ndarray, fade_samples: int) -> np.ndarray:
    """Apply a fade-out envelope to prevent audio clicks."""
    if len(wave) > fade_samples:
        wave = wave.copy()
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    return wave


def to_stereo_float32(wave: np.ndarray) -> np.ndarray:
    """Convert mono waveform to stereo float32 format."""
    return np.column_stack((wave, wave)).astype(np.float32)


def generate_waveform(
    sound_name: str,
    duration: float,
    config: AudioConfig | None = None,
) -> np.ndarray:
    """Generate a waveform for the specified sound type.

    Args:
        sound_name: Name of the sound preset
        duration: Duration in seconds
        config: Audio configuration (uses defaults if None)

    Returns:
        Stereo float32 numpy array ready for playback
    """
    if config is None:
        config = AudioConfig()

    sample_rate = config.sample_rate
    fade_samples = config.fade_samples

    if sound_name == "Standard Beep":
        wave = generate_sine_wave(880, duration, 0.5, sample_rate)
    elif sound_name == "Retro Buzzer":
        wave = generate_square_wave(150, duration, 0.3, sample_rate)
    elif sound_name == "Sci-Fi Chirp":
        wave = generate_frequency_sweep(600, 1200, duration, 0.4, sample_rate)
    elif sound_name == "Penalty Whistle":
        wave = generate_two_tone(1000, 1500, duration, 0.4, sample_rate)
    else:
        # Silent fallback
        wave = np.zeros(int(sample_rate * duration))

    wave = apply_fade_out(wave, fade_samples)
    return to_stereo_float32(wave)
