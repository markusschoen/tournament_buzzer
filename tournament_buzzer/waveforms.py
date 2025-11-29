"""Waveform generation functions for different buzzer sounds.

Each function generates a numpy array representing a stereo audio waveform.
Functions are pure and stateless - they take parameters and return data.

Sound Design Principles for HEMA Tournaments:
- Each ring needs a distinct sound that can be identified in a loud environment
- Sounds differ in: frequency range, rhythm pattern, timbre, and melodic contour
- Default order (Ring 1-4): Low Horn, Triple Pulse, Rising Siren, Staccato Beeps
"""

import numpy as np
from numpy.typing import NDArray

from .config import AudioConfig

# Type alias for numpy arrays
NDArrayFloat = NDArray[np.floating]


def generate_sine_wave(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> NDArrayFloat:
    """Generate a pure sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.asarray(amplitude * np.sin(2 * np.pi * frequency * t))


def generate_square_wave(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> NDArrayFloat:
    """Generate a square wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.asarray(amplitude * np.sign(np.sin(2 * np.pi * frequency * t)))


def generate_sawtooth_wave(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> NDArrayFloat:
    """Generate a sawtooth wave (rich harmonics, good for cutting through noise)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.asarray(amplitude * (2 * (t * frequency - np.floor(t * frequency + 0.5))))


def generate_frequency_sweep(
    start_freq: float,
    end_freq: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> NDArrayFloat:
    """Generate a linear frequency sweep (chirp)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    k = (end_freq - start_freq) / duration
    phase = 2 * np.pi * (start_freq * t + 0.5 * k * t**2)
    return np.asarray(amplitude * np.sin(phase))


def generate_two_tone(
    freq1: float,
    freq2: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> NDArrayFloat:
    """Generate a two-tone alternating signal."""
    half_duration = duration / 2
    t_half = np.linspace(
        0, half_duration, int(sample_rate * half_duration), endpoint=False
    )
    tone1 = np.sin(2 * np.pi * freq1 * t_half)
    tone2 = np.sin(2 * np.pi * freq2 * t_half)
    return np.asarray(amplitude * np.concatenate((tone1, tone2)))


def generate_pulsed_tone(
    frequency: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
    pulse_count: int,
    duty_cycle: float = 0.6,
) -> np.ndarray:
    """Generate a pulsed/beeping tone with specified number of pulses."""
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # Create the base tone
    tone = amplitude * np.sin(2 * np.pi * frequency * t)

    # Create pulse envelope
    pulse_duration = duration / pulse_count
    on_duration = pulse_duration * duty_cycle

    envelope = np.zeros(total_samples)
    for i in range(pulse_count):
        start_sample = int(i * pulse_duration * sample_rate)
        end_sample = int((i * pulse_duration + on_duration) * sample_rate)
        end_sample = min(end_sample, total_samples)
        if start_sample < total_samples:
            envelope[start_sample:end_sample] = 1.0

    return tone * envelope


def generate_horn_blast(
    base_freq: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a rich horn-like sound with harmonics (like an air horn)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Combine fundamental with harmonics for rich, penetrating sound
    wave = (
        0.5 * np.sin(2 * np.pi * base_freq * t)  # Fundamental
        + 0.3 * np.sin(2 * np.pi * base_freq * 2 * t)  # 2nd harmonic
        + 0.15 * np.sin(2 * np.pi * base_freq * 3 * t)  # 3rd harmonic
        + 0.05 * np.sin(2 * np.pi * base_freq * 4 * t)  # 4th harmonic
    )

    # Apply attack envelope for more natural horn sound
    attack_samples = int(0.05 * sample_rate)  # 50ms attack
    if len(wave) > attack_samples:
        attack = np.linspace(0, 1, attack_samples)
        wave[:attack_samples] *= attack

    return amplitude * wave


def generate_siren_sweep(
    low_freq: float,
    high_freq: float,
    duration: float,
    amplitude: float,
    sample_rate: int,
    cycles: int = 1,
) -> np.ndarray:
    """Generate a siren-like sweep that goes up and/or down."""
    total_samples = int(sample_rate * duration)

    # Create frequency modulation for siren effect
    cycle_duration = duration / cycles
    freq_mod = np.zeros(total_samples)

    for i in range(cycles):
        start_sample = int(i * cycle_duration * sample_rate)
        end_sample = int((i + 1) * cycle_duration * sample_rate)
        end_sample = min(end_sample, total_samples)
        cycle_samples = end_sample - start_sample

        # Rising sweep for each cycle
        freq_mod[start_sample:end_sample] = np.linspace(
            low_freq, high_freq, cycle_samples
        )

    # Generate the swept frequency signal
    phase = np.cumsum(2 * np.pi * freq_mod / sample_rate)
    return amplitude * np.sin(phase)


def generate_staccato_beeps(
    frequencies: list[float],
    duration: float,
    amplitude: float,
    sample_rate: int,
    gap_ratio: float = 0.3,
) -> np.ndarray:
    """Generate distinct staccato beeps at different frequencies."""
    total_samples = int(sample_rate * duration)
    wave = np.zeros(total_samples)

    beep_count = len(frequencies)
    segment_duration = duration / beep_count
    beep_duration = segment_duration * (1 - gap_ratio)

    for i, freq in enumerate(frequencies):
        start_time = i * segment_duration
        start_sample = int(start_time * sample_rate)
        beep_samples = int(beep_duration * sample_rate)
        end_sample = min(start_sample + beep_samples, total_samples)

        t = np.linspace(0, beep_duration, end_sample - start_sample, endpoint=False)
        beep = amplitude * np.sin(2 * np.pi * freq * t)

        # Quick fade in/out for each beep to prevent clicks
        fade_samples = min(50, len(beep) // 4)
        if len(beep) > fade_samples * 2:
            beep[:fade_samples] *= np.linspace(0, 1, fade_samples)
            beep[-fade_samples:] *= np.linspace(1, 0, fade_samples)

        wave[start_sample:end_sample] = beep

    return wave


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

    Sound Recommendations for HEMA Tournament Rings:
        Ring 1: Low Horn - Deep, powerful, unmistakable (220Hz base)
        Ring 2: Triple Pulse - Three quick mid-range beeps (660Hz)
        Ring 3: Rising Siren - Distinctive upward sweep (400-1000Hz)
        Ring 4: Staccato Beeps - Four quick descending notes
    """
    if config is None:
        config = AudioConfig()

    sample_rate = config.sample_rate
    fade_samples = config.fade_samples

    # === NEW TOURNAMENT-OPTIMIZED SOUNDS ===

    if sound_name == "Low Horn":
        # Ring 1 recommendation: Deep, powerful horn blast
        # Distinctive low frequency with rich harmonics, cuts through crowd noise
        wave = generate_horn_blast(220, duration, 0.5, sample_rate)

    elif sound_name == "Triple Pulse":
        # Ring 2 recommendation: Three quick beeps at mid frequency
        # Rhythmic pattern is easy to distinguish from sustained tones
        wave = generate_pulsed_tone(
            660, duration, 0.5, sample_rate, pulse_count=3, duty_cycle=0.65
        )

    elif sound_name == "Rising Siren":
        # Ring 3 recommendation: Upward frequency sweep
        # Very distinctive - the rising pattern is immediately recognizable
        wave = generate_siren_sweep(400, 1000, duration, 0.45, sample_rate, cycles=1)

    elif sound_name == "Staccato Beeps":
        # Ring 4 recommendation: Four quick descending notes
        # Musical pattern (descending 4ths) is memorable and distinct
        wave = generate_staccato_beeps(
            [880, 660, 495, 370], duration, 0.5, sample_rate, gap_ratio=0.25
        )

    # === ADDITIONAL SOUND OPTIONS ===

    elif sound_name == "Double Blast":
        # Two powerful blasts - good alternative for any ring
        wave = generate_pulsed_tone(
            440, duration, 0.5, sample_rate, pulse_count=2, duty_cycle=0.7
        )

    elif sound_name == "High Alert":
        # High-pitched attention-grabbing tone
        wave = generate_horn_blast(880, duration, 0.4, sample_rate)

    elif sound_name == "Falling Siren":
        # Opposite of Rising Siren - good contrast if using both
        wave = generate_siren_sweep(1000, 400, duration, 0.45, sample_rate, cycles=1)

    elif sound_name == "Rapid Pulse":
        # Fast pulsing for urgency (5 quick beeps)
        wave = generate_pulsed_tone(
            550, duration, 0.45, sample_rate, pulse_count=5, duty_cycle=0.5
        )

    # === LEGACY SOUNDS (kept for backwards compatibility) ===

    elif sound_name == "Standard Beep":
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
