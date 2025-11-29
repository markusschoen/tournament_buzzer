"""Event logging functionality for tournament documentation.

Provides functions for loading, saving, and managing tournament event logs.
Uses a simple JSON-based storage format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict, cast

from loguru import logger


class LogEntry(TypedDict):
    """Type definition for a log entry."""

    timestamp: str
    sound: str
    key: str | None


def load_log(log_file: Path) -> list[LogEntry]:
    """Load the event log from file.

    Args:
        log_file: Path to the log file

    Returns:
        List of log entries, empty list if file doesn't exist or is invalid
    """
    if not log_file.exists():
        return []

    try:
        with open(log_file, "r") as f:
            return cast(list[LogEntry], json.load(f))
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load log file: {e}")
        return []


def save_log(log_file: Path, entries: list[LogEntry]) -> bool:
    """Save the event log to file.

    Args:
        log_file: Path to the log file
        entries: List of log entries to save

    Returns:
        True if save was successful, False otherwise
    """
    try:
        with open(log_file, "w") as f:
            json.dump(entries, f, indent=2)
        return True
    except IOError as e:
        logger.error(f"Error saving log: {e}")
        return False


def export_log(
    entries: list[LogEntry], base_name: str = "tournament_log"
) -> Path | None:
    """Export the log to a timestamped file.

    Args:
        entries: List of log entries to export
        base_name: Base name for the export file

    Returns:
        Path to the exported file, or None if export failed
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_file = Path(f"{base_name}_{timestamp}.json")

    try:
        with open(export_file, "w") as f:
            json.dump(entries, f, indent=2)
        return export_file
    except IOError as e:
        logger.error(f"Error exporting log: {e}")
        return None


def create_log_entry(sound_name: str, key_info: str | None = None) -> LogEntry:
    """Create a new log entry.

    Args:
        sound_name: Name of the sound that was played
        key_info: Optional key that triggered the sound

    Returns:
        A new log entry dictionary
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "sound": sound_name,
        "key": key_info,
    }


def format_log_entry(entry: LogEntry, show_key: bool = False) -> str:
    """Format a log entry for display.

    Args:
        entry: The log entry to format
        show_key: Whether to include key information

    Returns:
        Formatted string representation
    """
    time_str = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
    line = f"[{time_str}] {entry['sound']}"

    if show_key and entry.get("key"):
        line += f" (key: {entry['key']})"

    return line
