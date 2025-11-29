"""Tests for the config module."""

from pathlib import Path

import pytest
from pynput import keyboard

from tournament_buzzer.config import (
    COLORS,
    DEFAULT_TRIGGER_KEYS,
    SOUND_OPTIONS,
    AppConfig,
    AudioConfig,
    TimingConfig,
)


class TestAudioConfig:
    """Tests for AudioConfig dataclass."""

    def test_default_values(self):
        """Test that AudioConfig has sensible defaults."""
        config = AudioConfig()

        assert config.sample_rate == 44100
        assert config.default_duration == 0.4
        assert config.default_volume == 0.8
        assert config.fade_samples == 500

    def test_custom_values(self):
        """Test AudioConfig with custom values."""
        config = AudioConfig(
            sample_rate=48000,
            default_duration=1.0,
            default_volume=0.5,
            fade_samples=1000,
        )

        assert config.sample_rate == 48000
        assert config.default_duration == 1.0
        assert config.default_volume == 0.5
        assert config.fade_samples == 1000


class TestTimingConfig:
    """Tests for TimingConfig dataclass."""

    def test_default_values(self):
        """Test that TimingConfig has sensible defaults."""
        config = TimingConfig()

        assert config.default_delay == 0.5
        assert config.default_cooldown == 3.0
        assert config.min_delay == 0.0
        assert config.max_delay == 5.0
        assert config.min_cooldown == 0.5
        assert config.max_cooldown == 10.0
        assert config.min_duration == 0.1
        assert config.max_duration == 2.0

    def test_default_values_within_bounds(self):
        """Test that default values are within min/max bounds."""
        config = TimingConfig()

        assert config.min_delay <= config.default_delay <= config.max_delay
        assert config.min_cooldown <= config.default_cooldown <= config.max_cooldown

    def test_custom_values(self):
        """Test TimingConfig with custom values."""
        config = TimingConfig(
            default_delay=1.0,
            default_cooldown=5.0,
        )

        assert config.default_delay == 1.0
        assert config.default_cooldown == 5.0


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_default_values(self):
        """Test that AppConfig has sensible defaults."""
        config = AppConfig()

        assert config.title == "HEMA Tournament Buzzer"
        assert config.window_size == "500x700"
        assert config.log_file == Path("tournament_log.json")

    def test_custom_values(self):
        """Test AppConfig with custom values."""
        custom_path = Path("/tmp/custom_log.json")
        config = AppConfig(
            title="Custom Title",
            window_size="800x600",
            log_file=custom_path,
        )

        assert config.title == "Custom Title"
        assert config.window_size == "800x600"
        assert config.log_file == custom_path


class TestConstants:
    """Tests for module-level constants."""

    def test_trigger_keys_not_empty(self):
        """Test that DEFAULT_TRIGGER_KEYS is not empty."""
        assert len(DEFAULT_TRIGGER_KEYS) > 0

    def test_trigger_keys_are_keyboard_keys(self):
        """Test that trigger keys are valid keyboard keys."""
        for key in DEFAULT_TRIGGER_KEYS:
            assert hasattr(keyboard.Key, key.name) or hasattr(keyboard.KeyCode, "from_char")

    def test_sound_options_not_empty(self):
        """Test that SOUND_OPTIONS is not empty."""
        assert len(SOUND_OPTIONS) > 0

    def test_sound_options_are_strings(self):
        """Test that all sound options are strings."""
        for option in SOUND_OPTIONS:
            assert isinstance(option, str)
            assert len(option) > 0

    def test_colors_has_required_keys(self):
        """Test that COLORS has all required keys."""
        required_keys = {"ready", "waiting", "triggered", "cooldown", "locked", "unlocked"}
        assert required_keys <= set(COLORS.keys())

    def test_colors_are_valid(self):
        """Test that colors are non-empty strings."""
        for key, color in COLORS.items():
            assert isinstance(color, str)
            assert len(color) > 0
