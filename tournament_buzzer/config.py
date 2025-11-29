"""Configuration constants and settings for the tournament buzzer."""

from dataclasses import dataclass, field
from pathlib import Path

from pynput import keyboard


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
    keyboard.Key.media_volume_down,
    keyboard.Key.page_down,
    keyboard.Key.page_up,
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
