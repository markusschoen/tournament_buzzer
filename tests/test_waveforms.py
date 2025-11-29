"""Tests for the waveforms module."""

import numpy as np
import pytest

from tournament_buzzer.config import AudioConfig
from tournament_buzzer.waveforms import (
    apply_fade_out,
    generate_frequency_sweep,
    generate_sine_wave,
    generate_square_wave,
    generate_two_tone,
    generate_waveform,
    to_stereo_float32,
)


class TestGenerateSineWave:
    """Tests for generate_sine_wave function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        wave = generate_sine_wave(440, 1.0, 0.5, 44100)
        assert isinstance(wave, np.ndarray)

    def test_correct_length(self):
        """Test that output has correct number of samples."""
        duration = 0.5
        sample_rate = 44100
        wave = generate_sine_wave(440, duration, 0.5, sample_rate)
        expected_length = int(sample_rate * duration)
        assert len(wave) == expected_length

    def test_amplitude_bounds(self):
        """Test that wave amplitude stays within bounds."""
        amplitude = 0.5
        wave = generate_sine_wave(440, 1.0, amplitude, 44100)
        assert np.max(np.abs(wave)) <= amplitude + 1e-10

    def test_zero_amplitude(self):
        """Test that zero amplitude produces silence."""
        wave = generate_sine_wave(440, 1.0, 0.0, 44100)
        assert np.allclose(wave, 0)

    def test_frequency_affects_wave(self):
        """Test that different frequencies produce different waves."""
        wave_low = generate_sine_wave(100, 0.1, 0.5, 44100)
        wave_high = generate_sine_wave(1000, 0.1, 0.5, 44100)
        # Waves should be different
        assert not np.allclose(wave_low, wave_high)


class TestGenerateSquareWave:
    """Tests for generate_square_wave function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        wave = generate_square_wave(440, 1.0, 0.5, 44100)
        assert isinstance(wave, np.ndarray)

    def test_correct_length(self):
        """Test that output has correct number of samples."""
        duration = 0.5
        sample_rate = 44100
        wave = generate_square_wave(440, duration, 0.5, sample_rate)
        expected_length = int(sample_rate * duration)
        assert len(wave) == expected_length

    def test_amplitude_bounds(self):
        """Test that wave amplitude stays within bounds."""
        amplitude = 0.3
        wave = generate_square_wave(440, 1.0, amplitude, 44100)
        assert np.max(np.abs(wave)) <= amplitude + 1e-10

    def test_binary_values(self):
        """Test that square wave only has a few distinct values."""
        amplitude = 0.5
        wave = generate_square_wave(440, 0.1, amplitude, 44100)
        unique_values = np.unique(wave)
        # Should have 2-3 values: +amplitude, -amplitude, and possibly 0 at zero-crossings
        assert len(unique_values) <= 3
        # Main values should be ±amplitude
        assert np.isclose(np.max(wave), amplitude)
        assert np.isclose(np.min(wave), -amplitude)


class TestGenerateFrequencySweep:
    """Tests for generate_frequency_sweep function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        wave = generate_frequency_sweep(440, 880, 1.0, 0.5, 44100)
        assert isinstance(wave, np.ndarray)

    def test_correct_length(self):
        """Test that output has correct number of samples."""
        duration = 0.5
        sample_rate = 44100
        wave = generate_frequency_sweep(440, 880, duration, 0.5, sample_rate)
        expected_length = int(sample_rate * duration)
        assert len(wave) == expected_length

    def test_amplitude_bounds(self):
        """Test that wave amplitude stays within bounds."""
        amplitude = 0.4
        wave = generate_frequency_sweep(440, 880, 1.0, amplitude, 44100)
        assert np.max(np.abs(wave)) <= amplitude + 1e-10


class TestGenerateTwoTone:
    """Tests for generate_two_tone function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        wave = generate_two_tone(440, 880, 1.0, 0.5, 44100)
        assert isinstance(wave, np.ndarray)

    def test_correct_length(self):
        """Test that output has correct number of samples."""
        duration = 1.0
        sample_rate = 44100
        wave = generate_two_tone(440, 880, duration, 0.5, sample_rate)
        expected_length = int(sample_rate * duration)
        assert len(wave) == expected_length

    def test_two_halves_are_different(self):
        """Test that the two halves of the wave are different."""
        duration = 1.0
        sample_rate = 44100
        wave = generate_two_tone(440, 880, duration, 0.5, sample_rate)
        half = len(wave) // 2
        first_half = wave[:half]
        second_half = wave[half:]
        # The two halves should be different
        assert not np.allclose(first_half, second_half)


class TestApplyFadeOut:
    """Tests for apply_fade_out function."""

    def test_does_not_modify_short_waves(self):
        """Test that short waves are not affected by fade."""
        wave = np.ones(100)
        fade_samples = 500
        result = apply_fade_out(wave, fade_samples)
        # Wave is shorter than fade, so should be unchanged
        assert np.allclose(result, wave)

    def test_applies_fade_to_end(self):
        """Test that fade is applied to the end of the wave."""
        wave = np.ones(1000)
        fade_samples = 100
        result = apply_fade_out(wave, fade_samples)

        # Beginning should be unchanged
        assert np.allclose(result[:900], 1.0)
        # End should fade to zero
        assert result[-1] < 0.1

    def test_does_not_modify_original(self):
        """Test that the original array is not modified."""
        wave = np.ones(1000)
        original = wave.copy()
        fade_samples = 100
        apply_fade_out(wave, fade_samples)
        # Original should be unchanged
        assert np.allclose(wave, original)


class TestToStereoFloat32:
    """Tests for to_stereo_float32 function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        mono = np.array([0.1, 0.2, 0.3])
        stereo = to_stereo_float32(mono)
        assert isinstance(stereo, np.ndarray)

    def test_correct_shape(self):
        """Test that output has correct shape (n, 2)."""
        mono = np.array([0.1, 0.2, 0.3])
        stereo = to_stereo_float32(mono)
        assert stereo.shape == (3, 2)

    def test_channels_are_identical(self):
        """Test that both channels contain same data."""
        mono = np.array([0.1, 0.2, 0.3])
        stereo = to_stereo_float32(mono)
        assert np.allclose(stereo[:, 0], stereo[:, 1])

    def test_dtype_is_float32(self):
        """Test that output dtype is float32."""
        mono = np.array([0.1, 0.2, 0.3])
        stereo = to_stereo_float32(mono)
        assert stereo.dtype == np.float32


class TestGenerateWaveform:
    """Tests for generate_waveform function."""

    @pytest.mark.parametrize(
        "sound_name",
        ["Standard Beep", "Retro Buzzer", "Sci-Fi Chirp", "Penalty Whistle"],
    )
    def test_generates_all_sound_types(self, sound_name):
        """Test that all sound types can be generated."""
        wave = generate_waveform(sound_name, 0.4)
        assert isinstance(wave, np.ndarray)
        assert wave.shape[1] == 2  # Stereo

    def test_unknown_sound_returns_silence(self):
        """Test that unknown sound type returns silence."""
        wave = generate_waveform("Unknown Sound", 0.4)
        assert np.allclose(wave, 0)

    def test_uses_custom_config(self):
        """Test that custom config is respected."""
        config = AudioConfig(sample_rate=22050, fade_samples=100)
        duration = 1.0
        wave = generate_waveform("Standard Beep", duration, config)

        expected_length = int(22050 * duration)
        assert wave.shape[0] == expected_length

    def test_output_is_stereo_float32(self):
        """Test that output is stereo float32."""
        wave = generate_waveform("Standard Beep", 0.4)
        assert wave.dtype == np.float32
        assert wave.shape[1] == 2

    def test_duration_affects_length(self):
        """Test that duration parameter affects output length."""
        short = generate_waveform("Standard Beep", 0.1)
        long = generate_waveform("Standard Beep", 0.5)
        assert len(short) < len(long)
