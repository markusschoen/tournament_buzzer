"""Tests for key listener normalization utilities."""

import pytest

from tournament_buzzer.key_listener import normalize_key_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Key.media_volume_down", "volume_down"),
        ("Key.media_volume_up", "volume_up"),
        ("KEY_VOLUMEDOWN", "volume_down"),
        ("KEY_VOLUMEUP", "volume_up"),
        ("XF86AudioLowerVolume", "volume_down"),
        ("XF86AudioRaiseVolume", "volume_up"),
        ("AudioLowerVolume", "volume_down"),
        ("AudioRaiseVolume", "volume_up"),
        ("<269025041>", "volume_down"),
        ("<269025043>", "volume_up"),
        ("0x1008ff11", "volume_down"),
        ("0x1008ff13", "volume_up"),
        ("KeyCode(vk=269025041)", "volume_down"),
        ("KeyCode(vk=269025043)", "volume_up"),
    ],
)
def test_normalize_key_name_handles_media_key_variants(raw: str, expected: str) -> None:
    """Normalize media key names from pynput, evdev, and Linux/X11 remotes."""

    assert normalize_key_name(raw) == expected


def test_normalize_key_name_keeps_character_key() -> None:
    """Character key normalization should remain unchanged."""

    assert normalize_key_name("'a'") == "a"
