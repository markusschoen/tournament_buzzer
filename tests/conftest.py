"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tournament_buzzer.config import AppConfig, AudioConfig, TimingConfig


@pytest.fixture
def audio_config():
    """Provide a default AudioConfig for testing."""
    return AudioConfig()


@pytest.fixture
def timing_config():
    """Provide a default TimingConfig for testing."""
    return TimingConfig()


@pytest.fixture
def app_config(tmp_path):
    """Provide an AppConfig with a temporary log file."""
    return AppConfig(log_file=tmp_path / "test_log.json")


@pytest.fixture
def temp_log_file(tmp_path):
    """Provide a temporary log file path."""
    return tmp_path / "test_log.json"


@pytest.fixture
def sample_log_entries():
    """Provide sample log entries for testing."""
    return [
        {"timestamp": "2025-11-29T10:00:00", "sound": "Standard Beep", "key": "page_up"},
        {"timestamp": "2025-11-29T10:01:00", "sound": "Retro Buzzer", "key": None},
        {"timestamp": "2025-11-29T10:02:00", "sound": "Sci-Fi Chirp", "key": "page_down"},
    ]


@pytest.fixture
def populated_log_file(temp_log_file, sample_log_entries):
    """Create a log file with sample entries."""
    with open(temp_log_file, "w") as f:
        json.dump(sample_log_entries, f)
    return temp_log_file


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module for testing without audio hardware."""
    with patch("tournament_buzzer.audio.sd") as mock_sd:
        # Mock query_devices to return some fake devices
        mock_sd.query_devices.return_value = [
            {"name": "Built-in Output", "max_output_channels": 2, "max_input_channels": 0},
            {"name": "USB Audio", "max_output_channels": 2, "max_input_channels": 0},
            {"name": "Microphone", "max_output_channels": 0, "max_input_channels": 1},
        ]
        
        # Mock OutputStream
        mock_stream = MagicMock()
        mock_sd.OutputStream.return_value = mock_stream
        
        yield mock_sd


@pytest.fixture
def mock_keyboard():
    """Mock pynput keyboard module."""
    with patch("tournament_buzzer.app.keyboard") as mock_kb:
        mock_listener = MagicMock()
        mock_kb.Listener.return_value = mock_listener
        yield mock_kb
