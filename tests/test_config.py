"""Tests for the config module."""

import json
from pathlib import Path
from unittest.mock import patch

from pynput import keyboard

from tournament_buzzer.config import (
    COLORS,
    DEFAULT_TRIGGER_KEYS,
    SOUND_OPTIONS,
    AppConfig,
    AudioConfig,
    TimingConfig,
    get_factory_defaults,
    load_user_defaults,
    save_user_defaults,
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
            assert hasattr(keyboard.Key, key.name) or hasattr(
                keyboard.KeyCode, "from_char"
            )

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
        required_keys = {
            "ready",
            "waiting",
            "triggered",
            "cooldown",
            "locked",
            "unlocked",
        }
        assert required_keys <= set(COLORS.keys())

    def test_colors_are_valid(self):
        """Test that colors are non-empty strings."""
        for key, color in COLORS.items():
            assert isinstance(color, str)
            assert len(color) > 0


class TestSaveUserDefaults:
    """Tests for save_user_defaults function."""

    def test_saves_config_to_file(self, tmp_path):
        """Test that save_user_defaults writes config to file."""
        test_config_file = tmp_path / "test_config.json"
        audio_config = AudioConfig(default_duration=0.5, default_volume=0.7)
        timing_config = TimingConfig(default_delay=1.0, default_cooldown=4.0)

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", test_config_file):
            result = save_user_defaults(audio_config, timing_config)

        assert result is True
        assert test_config_file.exists()

        with open(test_config_file) as f:
            data = json.load(f)

        assert data["audio"]["default_duration"] == 0.5
        assert data["audio"]["default_volume"] == 0.7
        assert data["timing"]["default_delay"] == 1.0
        assert data["timing"]["default_cooldown"] == 4.0

    def test_returns_false_on_io_error(self, tmp_path):
        """Test that save_user_defaults returns False on IO error."""
        # Use a path that cannot be written to
        invalid_path = Path("/nonexistent_dir/config.json")

        audio_config = AudioConfig()
        timing_config = TimingConfig()

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", invalid_path):
            result = save_user_defaults(audio_config, timing_config)

        assert result is False


class TestLoadUserDefaults:
    """Tests for load_user_defaults function."""

    def test_loads_config_from_file(self, tmp_path):
        """Test that load_user_defaults reads config from file."""
        test_config_file = tmp_path / "test_config.json"
        config_data = {
            "audio": {
                "sample_rate": 48000,
                "default_duration": 0.6,
                "default_volume": 0.9,
                "fade_samples": 600,
            },
            "timing": {
                "default_delay": 0.8,
                "default_cooldown": 2.5,
                "min_delay": 0.1,
                "max_delay": 4.0,
                "min_cooldown": 1.0,
                "max_cooldown": 8.0,
                "min_duration": 0.2,
                "max_duration": 1.5,
            },
        }
        with open(test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", test_config_file):
            audio_config, timing_config = load_user_defaults()

        assert audio_config.sample_rate == 48000
        assert audio_config.default_duration == 0.6
        assert audio_config.default_volume == 0.9
        assert audio_config.fade_samples == 600
        assert timing_config.default_delay == 0.8
        assert timing_config.default_cooldown == 2.5

    def test_returns_factory_defaults_when_file_missing(self, tmp_path):
        """Test that load_user_defaults returns factory defaults if file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.json"

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", nonexistent_file):
            audio_config, timing_config = load_user_defaults()

        factory_audio, factory_timing = get_factory_defaults()
        assert audio_config.default_duration == factory_audio.default_duration
        assert timing_config.default_delay == factory_timing.default_delay

    def test_returns_factory_defaults_on_invalid_json(self, tmp_path):
        """Test that load_user_defaults returns factory defaults on invalid JSON."""
        test_config_file = tmp_path / "invalid.json"
        test_config_file.write_text("not valid json {{{")

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", test_config_file):
            audio_config, timing_config = load_user_defaults()

        factory_audio, factory_timing = get_factory_defaults()
        assert audio_config.default_duration == factory_audio.default_duration
        assert timing_config.default_delay == factory_timing.default_delay

    def test_handles_partial_config(self, tmp_path):
        """Test that load_user_defaults handles partial config with defaults."""
        test_config_file = tmp_path / "partial.json"
        config_data = {
            "audio": {"default_duration": 0.7},
            # timing section missing
        }
        with open(test_config_file, "w") as f:
            json.dump(config_data, f)

        with patch("tournament_buzzer.config.USER_CONFIG_FILE", test_config_file):
            audio_config, timing_config = load_user_defaults()

        assert audio_config.default_duration == 0.7
        # Should use default for missing fields
        assert audio_config.sample_rate == 44100
        # Should use default for missing timing section
        assert timing_config.default_delay == 0.5


class TestGetFactoryDefaults:
    """Tests for get_factory_defaults function."""

    def test_returns_tuple_of_configs(self):
        """Test that get_factory_defaults returns AudioConfig and TimingConfig."""
        audio_config, timing_config = get_factory_defaults()

        assert isinstance(audio_config, AudioConfig)
        assert isinstance(timing_config, TimingConfig)

    def test_returns_default_values(self):
        """Test that get_factory_defaults returns default dataclass values."""
        audio_config, timing_config = get_factory_defaults()

        # Check AudioConfig defaults
        assert audio_config.sample_rate == 44100
        assert audio_config.default_duration == 0.4
        assert audio_config.default_volume == 0.8
        assert audio_config.fade_samples == 500

        # Check TimingConfig defaults
        assert timing_config.default_delay == 0.5
        assert timing_config.default_cooldown == 3.0

    def test_returns_new_instances(self):
        """Test that get_factory_defaults returns new instances each time."""
        audio1, timing1 = get_factory_defaults()
        audio2, timing2 = get_factory_defaults()

        assert audio1 is not audio2
        assert timing1 is not timing2
