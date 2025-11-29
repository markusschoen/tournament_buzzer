"""Tests for the app module."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from tournament_buzzer.app import BuzzerApp, format_trigger_keys
from tournament_buzzer.config import AppConfig, AudioConfig, TimingConfig


class TestFormatTriggerKeys:
    """Tests for format_trigger_keys function."""

    def test_formats_single_key(self):
        """Test formatting a single key."""
        keys = [MagicMock(__str__=lambda self: "Key.page_up")]
        result = format_trigger_keys(keys)

        assert "Triggers:" in result

    def test_limits_displayed_keys(self):
        """Test that display is limited to max_display keys."""
        keys = [MagicMock(__str__=lambda self: f"Key.key_{i}") for i in range(15)]
        result = format_trigger_keys(keys, max_display=5)

        assert "..." in result

    def test_no_ellipsis_when_within_limit(self):
        """Test no ellipsis when within limit."""
        keys = [MagicMock(__str__=lambda self: "Key.a")]
        result = format_trigger_keys(keys, max_display=5)

        assert "..." not in result

    def test_removes_key_prefix(self):
        """Test that Key. prefix is removed."""
        # Create a mock that returns "Key.page_up" when str() is called
        mock_key = MagicMock()
        mock_key.__str__ = lambda self: "Key.page_up"
        keys = [mock_key]
        result = format_trigger_keys(keys)

        assert "Key." not in result
        assert "page_up" in result


class TestBuzzerApp:
    """Tests for BuzzerApp class.

    Note: These tests require a display and mock the audio/keyboard components.
    """

    @pytest.fixture
    def mock_audio_engine(self):
        """Mock the AudioEngine class."""
        with patch("tournament_buzzer.app.AudioEngine") as mock:
            engine_instance = MagicMock()
            mock.return_value = engine_instance
            yield mock, engine_instance

    @pytest.fixture
    def mock_keyboard(self):
        """Mock the keyboard listener."""
        with patch("tournament_buzzer.app.keyboard") as mock:
            listener_instance = MagicMock()
            mock.Listener.return_value = listener_instance
            yield mock, listener_instance

    @pytest.fixture
    def mock_devices(self):
        """Mock device functions."""
        with patch("tournament_buzzer.app.get_output_devices") as mock_get:
            with patch("tournament_buzzer.app.get_default_device_name") as mock_default:
                mock_get.return_value = [(0, "Device 1"), (1, "Device 2")]
                mock_default.return_value = "Device 1"
                yield mock_get, mock_default

    @pytest.fixture
    def app(self, mock_audio_engine, mock_keyboard, mock_devices, tmp_path):
        """Create a BuzzerApp for testing."""
        try:
            # Hide tk window
            root = tk.Tk()
            root.withdraw()
            root.destroy()

            app_config = AppConfig(log_file=tmp_path / "test_log.json")
            app = BuzzerApp(app_config=app_config, trigger_keys=[])
            app.withdraw()  # Hide the app window

            yield app

            # Cleanup
            app._listener.stop()
            app.destroy()
        except tk.TclError:
            pytest.skip("No display available for tkinter tests")

    def test_initialization(self, app):
        """Test that app initializes with correct state."""
        assert app._cooldown_locked is False
        assert app._debug_mode.get() is False

    def test_config_defaults(self, app):
        """Test that default configs are used when none provided."""
        assert app.audio_config is not None
        assert app.timing_config is not None

    def test_custom_configs(
        self, mock_audio_engine, mock_keyboard, mock_devices, tmp_path
    ):
        """Test that custom configs are respected."""
        try:
            audio_config = AudioConfig(sample_rate=48000)
            timing_config = TimingConfig(default_delay=1.0)
            app_config = AppConfig(
                title="Custom Title", log_file=tmp_path / "test.json"
            )

            app = BuzzerApp(
                app_config=app_config,
                audio_config=audio_config,
                timing_config=timing_config,
                trigger_keys=[],
            )
            app.withdraw()

            assert app.audio_config.sample_rate == 48000
            assert app.timing_config.default_delay == 1.0
            assert app.title() == "Custom Title"

            app._listener.stop()
            app.destroy()
        except tk.TclError:
            pytest.skip("No display available for tkinter tests")

    def test_on_sound_change(self, app, mock_audio_engine):
        """Test sound change handler."""
        _, engine = mock_audio_engine

        app._on_sound_change("Retro Buzzer")

        engine.set_sound.assert_called_with("Retro Buzzer")

    def test_on_delay_change(self, app):
        """Test delay change handler."""
        app._on_delay_change(1.5)

        assert app._delay_seconds == 1.5

    def test_on_cooldown_change(self, app):
        """Test cooldown change handler."""
        app._on_cooldown_change(5.0)

        assert app._cooldown_seconds == 5.0

    def test_on_duration_change(self, app, mock_audio_engine):
        """Test duration change handler."""
        _, engine = mock_audio_engine

        app._on_duration_change(0.8)

        assert app._duration_seconds == 0.8
        engine.set_duration.assert_called_with(0.8)

    def test_start_trigger_sequence_blocked_during_cooldown(self, app):
        """Test that trigger is blocked during cooldown."""
        app._cooldown_locked = True
        app._debug_mode.set(True)

        # Should not raise, and should not start sequence
        app._start_trigger_sequence("test_key")

        # Still locked
        assert app._cooldown_locked is True

    def test_update_status(self, app):
        """Test status update method."""
        app._update_status("TEST", "#ff0000", "Test info")

        assert app._status_label.cget("text") == "TEST"
        assert app._info_label.cget("text") == "Test info"

    def test_clear_log(self, app, tmp_path):
        """Test log clearing."""
        # Add some entries
        app._event_log = [{"timestamp": "2025-01-01", "sound": "Beep", "key": None}]

        app._clear_log()

        assert app._event_log == []

    def test_on_close(self, mock_audio_engine, mock_keyboard, mock_devices, tmp_path):
        """Test cleanup on close."""
        try:
            _, engine = mock_audio_engine
            _, listener = mock_keyboard

            app_config = AppConfig(log_file=tmp_path / "test.json")
            app = BuzzerApp(app_config=app_config, trigger_keys=[])
            app.withdraw()

            app._on_close()

            engine.close.assert_called_once()
            listener.stop.assert_called_once()
        except tk.TclError:
            pytest.skip("No display available for tkinter tests")


class TestBuzzerAppIntegration:
    """Integration tests for BuzzerApp.

    These tests verify that components work together correctly.
    """

    @pytest.fixture(autouse=True)
    def mock_all_externals(self):
        """Mock all external dependencies."""
        with patch("tournament_buzzer.app.AudioEngine") as mock_audio:
            with patch("tournament_buzzer.app.keyboard") as mock_kb:
                with patch("tournament_buzzer.app.get_output_devices") as mock_get:
                    with patch(
                        "tournament_buzzer.app.get_default_device_name"
                    ) as mock_default:
                        mock_audio.return_value = MagicMock()
                        mock_kb.Listener.return_value = MagicMock()
                        mock_get.return_value = [(0, "Test Device")]
                        mock_default.return_value = "Test Device"
                        yield

    def test_device_selector_populated(self, tmp_path):
        """Test that device selector is populated on init."""
        try:
            app_config = AppConfig(log_file=tmp_path / "test.json")
            app = BuzzerApp(app_config=app_config, trigger_keys=[])
            app.withdraw()

            # Device should be available in selector
            assert len(app._output_devices) == 1
            assert app._output_devices[0][1] == "Test Device"

            app._listener.stop()
            app.destroy()
        except tk.TclError:
            pytest.skip("No display available for tkinter tests")

    def test_log_persistence(self, tmp_path):
        """Test that log entries are persisted."""
        try:
            log_file = tmp_path / "test_log.json"
            app_config = AppConfig(log_file=log_file)

            app = BuzzerApp(app_config=app_config, trigger_keys=[])
            app.withdraw()

            # Manually add a log entry through the internal method
            from tournament_buzzer.event_log import create_log_entry, save_log

            entry = create_log_entry("Test Sound", "test_key")
            app._event_log.append(entry)
            save_log(log_file, app._event_log)

            # Verify file was created
            assert log_file.exists()

            app._listener.stop()
            app.destroy()
        except tk.TclError:
            pytest.skip("No display available for tkinter tests")
