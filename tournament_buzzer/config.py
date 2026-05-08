"""Configuration constants and settings for the tournament buzzer."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger
from pynput import keyboard

# Default path for user configuration file
USER_CONFIG_FILE = Path.home() / ".tournament_buzzer_config.json"


@dataclass
class AudioConfig:
    """Audio-related configuration."""

    sample_rate: int = 44100
    default_duration: float = 0.4
    default_volume: float = 0.8
    fade_samples: int = 500


@dataclass
class TimingConfig:
    """Timing-related configuration."""

    default_delay: float = 0.5
    default_cooldown: float = 3.0
    min_delay: float = 0.0
    max_delay: float = 5.0
    min_cooldown: float = 0.5
    max_cooldown: float = 10.0
    min_duration: float = 0.1
    max_duration: float = 2.0


@dataclass
class AppConfig:
    """Application configuration."""

    title: str = "HEMA Tournament Buzzer"
    window_size: str = "500x700"
    log_file: Path = field(default_factory=lambda: Path("tournament_log.json"))
    log_enabled: bool = False  # Disable file logging by default


# Default trigger keys - can be customized per installation
DEFAULT_TRIGGER_KEYS = [
    keyboard.Key.media_volume_up,
    # keyboard.Key.media_volume_down,
    # keyboard.Key.page_down,
    # keyboard.Key.page_up,
]

# Available sound types - ordered for tournament ring assignment
# Recommended assignment: Ring 1=Low Horn, Ring 2=Triple Pulse, Ring 3=Rising Siren, Ring 4=Staccato Beeps
SOUND_OPTIONS = [
    # Primary tournament sounds (designed for maximum distinguishability)
    "Low Horn",  # Ring 1: Deep powerful blast (220Hz) - unmistakable low end
    "Triple Pulse",  # Ring 2: Three quick mid-range beeps (660Hz) - rhythmic pattern
    "Rising Siren",  # Ring 3: Upward frequency sweep (400-1000Hz) - distinctive motion
    "Staccato Beeps",  # Ring 4: Four descending notes - musical pattern
    # Additional tournament options
    "Double Blast",  # Two powerful horn blasts
    "High Alert",  # High-pitched attention grabber (880Hz)
    "Falling Siren",  # Downward sweep (opposite of Rising Siren)
    "Rapid Pulse",  # Five quick beeps for urgency
    # Legacy sounds (kept for backwards compatibility)
    "Standard Beep",
    "Retro Buzzer",
    "Sci-Fi Chirp",
    "Penalty Whistle",
]

# UI Colors
COLORS = {
    "ready": "grey",
    "waiting": "orange",
    "triggered": "#2ecc71",
    "cooldown": "#444444",
    "locked": "#2ecc71",
    "unlocked": "#e67e22",
}


def save_user_defaults(audio_config: AudioConfig, timing_config: TimingConfig) -> bool:
    """Save current settings as user defaults.

    Args:
        audio_config: Current audio configuration
        timing_config: Current timing configuration

    Returns:
        True if save was successful, False otherwise
    """
    config_data: dict[str, Any] = {
        "audio": asdict(audio_config),
        "timing": asdict(timing_config),
    }
    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
        logger.info(f"Saved user defaults to {USER_CONFIG_FILE}")
        return True
    except IOError as e:
        logger.error(f"Error saving user defaults: {e}")
        return False


def load_user_defaults() -> tuple[AudioConfig, TimingConfig]:
    """Load user defaults from config file.

    Returns:
        Tuple of (AudioConfig, TimingConfig) with user defaults,
        or default configs if no user file exists
    """
    if not USER_CONFIG_FILE.exists():
        return AudioConfig(), TimingConfig()

    try:
        with open(USER_CONFIG_FILE, "r") as f:
            config_data = json.load(f)

        audio_data = config_data.get("audio", {})
        timing_data = config_data.get("timing", {})

        audio_config = AudioConfig(
            sample_rate=audio_data.get("sample_rate", 44100),
            default_duration=audio_data.get("default_duration", 0.4),
            default_volume=audio_data.get("default_volume", 0.8),
            fade_samples=audio_data.get("fade_samples", 500),
        )

        timing_config = TimingConfig(
            default_delay=timing_data.get("default_delay", 0.5),
            default_cooldown=timing_data.get("default_cooldown", 3.0),
            min_delay=timing_data.get("min_delay", 0.0),
            max_delay=timing_data.get("max_delay", 5.0),
            min_cooldown=timing_data.get("min_cooldown", 0.5),
            max_cooldown=timing_data.get("max_cooldown", 10.0),
            min_duration=timing_data.get("min_duration", 0.1),
            max_duration=timing_data.get("max_duration", 2.0),
        )

        logger.info(f"Loaded user defaults from {USER_CONFIG_FILE}")
        return audio_config, timing_config
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load user config: {e}")
        return AudioConfig(), TimingConfig()


def get_factory_defaults() -> tuple[AudioConfig, TimingConfig]:
    """Get factory default configurations.

    Returns:
        Tuple of (AudioConfig, TimingConfig) with factory defaults
    """
    return AudioConfig(), TimingConfig()
