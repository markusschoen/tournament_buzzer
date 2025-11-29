"""Tests for the audio module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tournament_buzzer.audio import (
    AudioEngine,
    get_default_device_name,
    get_output_devices,
)
from tournament_buzzer.config import AudioConfig


class TestGetOutputDevices:
    """Tests for get_output_devices function."""

    def test_returns_list_of_tuples(self, mock_sounddevice):
        """Test that function returns list of (index, name) tuples."""
        devices = get_output_devices()

        assert isinstance(devices, list)
        assert all(isinstance(d, tuple) for d in devices)
        assert all(len(d) == 2 for d in devices)

    def test_filters_output_devices(self, mock_sounddevice):
        """Test that only output devices are returned."""
        devices = get_output_devices()

        # Should have 2 output devices (Built-in Output and USB Audio)
        # Microphone has 0 output channels so should be excluded
        assert len(devices) == 2
        device_names = [name for _, name in devices]
        assert "Microphone" not in device_names

    def test_includes_device_index(self, mock_sounddevice):
        """Test that device indices are included."""
        devices = get_output_devices()

        indices = [idx for idx, _ in devices]
        assert all(isinstance(idx, int) for idx in indices)


class TestGetDefaultDeviceName:
    """Tests for get_default_device_name function."""

    def test_returns_device_name(self, mock_sounddevice):
        """Test that function returns a device name."""
        mock_sounddevice.query_devices.return_value = {"name": "Default Output"}

        result = get_default_device_name()

        assert result == "Default Output"

    def test_returns_none_on_error(self, mock_sounddevice):
        """Test that function returns None on error."""
        mock_sounddevice.query_devices.side_effect = Exception("No device")

        result = get_default_device_name()

        assert result is None


class TestAudioEngine:
    """Tests for AudioEngine class."""

    def test_initialization(self, mock_sounddevice):
        """Test that AudioEngine initializes correctly."""
        engine = AudioEngine()

        assert engine.config is not None
        mock_sounddevice.OutputStream.assert_called_once()

    def test_initialization_with_custom_config(self, mock_sounddevice):
        """Test initialization with custom AudioConfig."""
        config = AudioConfig(sample_rate=48000, default_volume=0.5)
        engine = AudioEngine(config=config)

        assert engine.config.sample_rate == 48000
        assert engine._volume == 0.5

    def test_initialization_with_device(self, mock_sounddevice):
        """Test initialization with specific device."""
        engine = AudioEngine(device=1)

        # Check that OutputStream was called with device=1
        call_kwargs = mock_sounddevice.OutputStream.call_args[1]
        assert call_kwargs["device"] == 1

    def test_set_sound(self, mock_sounddevice):
        """Test setting different sound types."""
        engine = AudioEngine()

        for sound in ["Standard Beep", "Retro Buzzer", "Sci-Fi Chirp", "Penalty Whistle"]:
            engine.set_sound(sound)
            assert engine._current_sound == sound

    def test_set_volume(self, mock_sounddevice):
        """Test volume setting."""
        engine = AudioEngine()

        engine.set_volume(0.5)
        assert engine._volume == 0.5

    def test_set_volume_clamps_low(self, mock_sounddevice):
        """Test that volume is clamped to minimum."""
        engine = AudioEngine()

        engine.set_volume(-0.5)
        assert engine._volume == 0.0

    def test_set_volume_clamps_high(self, mock_sounddevice):
        """Test that volume is clamped to maximum."""
        engine = AudioEngine()

        engine.set_volume(1.5)
        assert engine._volume == 1.0

    def test_set_duration(self, mock_sounddevice):
        """Test setting sound duration."""
        engine = AudioEngine()

        engine.set_duration(0.8)
        assert engine._current_duration == 0.8

    def test_set_device(self, mock_sounddevice):
        """Test changing audio device."""
        engine = AudioEngine()

        # Reset mock to clear initialization call
        mock_sounddevice.OutputStream.reset_mock()

        engine.set_device(2)

        # Should have created new stream with new device
        mock_sounddevice.OutputStream.assert_called_once()
        call_kwargs = mock_sounddevice.OutputStream.call_args[1]
        assert call_kwargs["device"] == 2

    def test_trigger(self, mock_sounddevice):
        """Test triggering sound playback."""
        engine = AudioEngine()

        engine.trigger()

        assert engine._play_event.is_set()
        assert engine._beep_position == 0

    def test_close(self, mock_sounddevice):
        """Test closing the engine."""
        engine = AudioEngine()
        mock_stream = mock_sounddevice.OutputStream.return_value

        engine.close()

        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

    def test_audio_callback_silence_when_not_playing(self, mock_sounddevice):
        """Test that callback produces silence when not playing."""
        engine = AudioEngine()
        outdata = np.zeros((1024, 2), dtype=np.float32)

        # Not triggered - play_event is not set
        engine._audio_callback(outdata, 1024, None, None)

        assert np.allclose(outdata, 0)

    def test_audio_callback_produces_audio_when_triggered(self, mock_sounddevice):
        """Test that callback produces audio when triggered."""
        engine = AudioEngine()
        engine.trigger()

        outdata = np.zeros((512, 2), dtype=np.float32)
        engine._audio_callback(outdata, 512, None, None)

        # Output should have audio data (not all zeros)
        assert not np.allclose(outdata, 0)

    def test_audio_callback_clears_event_when_done(self, mock_sounddevice):
        """Test that play event is cleared after playback completes."""
        config = AudioConfig(default_duration=0.01)  # Very short
        engine = AudioEngine(config=config)
        engine.trigger()

        # Call callback with more frames than the waveform
        outdata = np.zeros((50000, 2), dtype=np.float32)
        engine._audio_callback(outdata, 50000, None, None)

        assert not engine._play_event.is_set()

    def test_handles_stream_error_gracefully(self, mock_sounddevice):
        """Test that stream errors are handled gracefully."""
        mock_sounddevice.OutputStream.side_effect = Exception("Audio error")

        # Should not raise
        engine = AudioEngine()

        assert engine._stream is None

    def test_regenerate_waveform(self, mock_sounddevice):
        """Test waveform regeneration."""
        engine = AudioEngine()
        original_data = engine._beep_data.copy()

        engine.set_sound("Retro Buzzer")

        # Waveform should be different
        assert not np.allclose(engine._beep_data, original_data)
