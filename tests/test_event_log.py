"""Tests for the event_log module."""

import json
from datetime import datetime


from tournament_buzzer.event_log import (
    create_log_entry,
    export_log,
    format_log_entry,
    load_log,
    save_log,
)


class TestLoadLog:
    """Tests for load_log function."""

    def test_returns_empty_list_for_nonexistent_file(self, tmp_path):
        """Test that nonexistent file returns empty list."""
        log_file = tmp_path / "nonexistent.json"
        result = load_log(log_file)
        assert result == []

    def test_loads_existing_log(self, populated_log_file, sample_log_entries):
        """Test that existing log file is loaded correctly."""
        result = load_log(populated_log_file)
        assert result == sample_log_entries

    def test_returns_empty_list_for_invalid_json(self, tmp_path):
        """Test that invalid JSON returns empty list."""
        log_file = tmp_path / "invalid.json"
        log_file.write_text("not valid json {{{")
        result = load_log(log_file)
        assert result == []

    def test_returns_empty_list_for_empty_file(self, tmp_path):
        """Test that empty file returns empty list."""
        log_file = tmp_path / "empty.json"
        log_file.write_text("")
        result = load_log(log_file)
        assert result == []


class TestSaveLog:
    """Tests for save_log function."""

    def test_saves_entries_to_file(self, temp_log_file, sample_log_entries):
        """Test that entries are saved correctly."""
        result = save_log(temp_log_file, sample_log_entries)

        assert result is True
        assert temp_log_file.exists()

        with open(temp_log_file) as f:
            saved_data = json.load(f)
        assert saved_data == sample_log_entries

    def test_saves_empty_list(self, temp_log_file):
        """Test that empty list can be saved."""
        result = save_log(temp_log_file, [])

        assert result is True
        with open(temp_log_file) as f:
            saved_data = json.load(f)
        assert saved_data == []

    def test_overwrites_existing_file(self, populated_log_file):
        """Test that existing file is overwritten."""
        new_entries = [
            {"timestamp": "2025-11-29T12:00:00", "sound": "New", "key": None}
        ]
        save_log(populated_log_file, new_entries)

        with open(populated_log_file) as f:
            saved_data = json.load(f)
        assert saved_data == new_entries

    def test_returns_false_on_error(self, tmp_path):
        """Test that function returns False on write error."""
        # Try to write to a directory path (should fail)
        result = save_log(tmp_path, [])
        assert result is False


class TestExportLog:
    """Tests for export_log function."""

    def test_creates_timestamped_file(self, sample_log_entries, tmp_path, monkeypatch):
        """Test that export creates a timestamped file."""
        monkeypatch.chdir(tmp_path)

        result = export_log(sample_log_entries)

        assert result is not None
        assert result.exists()
        assert "tournament_log_" in result.name
        assert result.suffix == ".json"

    def test_uses_custom_base_name(self, sample_log_entries, tmp_path, monkeypatch):
        """Test that custom base name is used."""
        monkeypatch.chdir(tmp_path)

        result = export_log(sample_log_entries, base_name="custom_export")

        assert result is not None
        assert "custom_export_" in result.name

    def test_exported_content_matches_entries(
        self, sample_log_entries, tmp_path, monkeypatch
    ):
        """Test that exported content matches original entries."""
        monkeypatch.chdir(tmp_path)

        result = export_log(sample_log_entries)

        with open(result) as f:
            exported_data = json.load(f)
        assert exported_data == sample_log_entries

    def test_exports_empty_list(self, tmp_path, monkeypatch):
        """Test that empty list can be exported."""
        monkeypatch.chdir(tmp_path)

        result = export_log([])

        assert result is not None
        with open(result) as f:
            exported_data = json.load(f)
        assert exported_data == []


class TestCreateLogEntry:
    """Tests for create_log_entry function."""

    def test_creates_entry_with_sound_only(self):
        """Test entry creation with just sound name."""
        entry = create_log_entry("Standard Beep")

        assert entry["sound"] == "Standard Beep"
        assert entry["key"] is None
        assert "timestamp" in entry

    def test_creates_entry_with_key_info(self):
        """Test entry creation with key info."""
        entry = create_log_entry("Retro Buzzer", "page_up")

        assert entry["sound"] == "Retro Buzzer"
        assert entry["key"] == "page_up"

    def test_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO format."""
        entry = create_log_entry("Standard Beep")

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(entry["timestamp"])
        assert isinstance(parsed, datetime)

    def test_timestamp_is_current(self):
        """Test that timestamp is approximately current time."""
        before = datetime.now()
        entry = create_log_entry("Standard Beep")
        after = datetime.now()

        timestamp = datetime.fromisoformat(entry["timestamp"])
        assert before <= timestamp <= after


class TestFormatLogEntry:
    """Tests for format_log_entry function."""

    def test_formats_basic_entry(self, sample_log_entries):
        """Test basic entry formatting."""
        entry = sample_log_entries[0]
        result = format_log_entry(entry)

        assert "[10:00:00]" in result
        assert "Standard Beep" in result
        assert "key:" not in result

    def test_includes_key_when_requested(self, sample_log_entries):
        """Test that key is included when show_key=True."""
        entry = sample_log_entries[0]  # Has key "page_up"
        result = format_log_entry(entry, show_key=True)

        assert "(key: page_up)" in result

    def test_no_key_shown_when_key_is_none(self, sample_log_entries):
        """Test that no key info shown when key is None."""
        entry = sample_log_entries[1]  # Has key=None
        result = format_log_entry(entry, show_key=True)

        assert "key:" not in result

    def test_format_different_sounds(self):
        """Test formatting with different sound names."""
        for sound in [
            "Standard Beep",
            "Retro Buzzer",
            "Sci-Fi Chirp",
            "Penalty Whistle",
        ]:
            entry = {"timestamp": "2025-11-29T10:00:00", "sound": sound, "key": None}
            result = format_log_entry(entry)
            assert sound in result
