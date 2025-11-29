"""Audio engine for low-latency sound playback.

This module handles audio device management and real-time sound output.
The AudioEngine class maintains state for streaming audio, which is
necessary for the callback-based audio API.
"""

import threading

import sounddevice as sd
from loguru import logger

from .config import AudioConfig
from .waveforms import generate_waveform


def get_output_devices() -> list[tuple[int, str]]:
    """Get list of available output audio devices.

    Returns:
        List of (device_index, device_name) tuples
    """
    devices = sd.query_devices()
    return [
        (i, dev["name"])
        for i, dev in enumerate(devices)
        if dev["max_output_channels"] > 0
    ]


def get_default_device_name() -> str | None:
    """Get the name of the default output device."""
    try:
        device = sd.query_devices(kind="output")
        return device["name"]
    except Exception:
        return None


class AudioEngine:
    """Manages audio streaming and playback.

    This class is necessary because sounddevice uses a callback-based
    streaming model that requires maintaining state between callbacks.
    """

    def __init__(self, config: AudioConfig | None = None, device: int | None = None):
        """Initialize the audio engine.

        Args:
            config: Audio configuration settings
            device: Initial output device index (None for default)
        """
        self.config = config or AudioConfig()
        self._stream: sd.OutputStream | None = None
        self._play_event = threading.Event()
        self._lock = threading.Lock()

        self._beep_data = generate_waveform(
            "Standard Beep",
            self.config.default_duration,
            self.config,
        )
        self._beep_position = 0
        self._volume = self.config.default_volume
        self._current_sound = "Standard Beep"
        self._current_duration = self.config.default_duration

        self._start_stream(device)

    def _start_stream(self, device: int | None = None) -> None:
        """Start or restart the audio stream."""
        self._close_stream()

        try:
            self._stream = sd.OutputStream(
                samplerate=self.config.sample_rate,
                channels=2,
                callback=self._audio_callback,
                latency="low",
                device=device,
            )
            self._stream.start()
        except Exception as e:
            logger.error(f"Audio initialization error: {e}")
            logger.warning("No audio device available. Sounds will not play.")

    def _close_stream(self) -> None:
        """Safely close the current audio stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _audio_callback(self, outdata, frames, time_info, status) -> None:
        """Audio stream callback - called by sounddevice."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        with self._lock:
            if self._play_event.is_set():
                remaining = len(self._beep_data) - self._beep_position

                if remaining > 0:
                    to_copy = min(remaining, frames)
                    start = self._beep_position
                    end = start + to_copy
                    outdata[:to_copy] = self._beep_data[start:end] * self._volume
                    outdata[to_copy:] = 0
                    self._beep_position += to_copy

                    if self._beep_position >= len(self._beep_data):
                        self._play_event.clear()
                        self._beep_position = 0
                else:
                    outdata.fill(0)
                    self._play_event.clear()
                    self._beep_position = 0
            else:
                outdata.fill(0)

    def set_device(self, device_index: int) -> None:
        """Change the output audio device."""
        self._start_stream(device_index)

    def set_sound(self, sound_name: str) -> None:
        """Set the current sound type."""
        self._current_sound = sound_name
        self._regenerate_waveform()

    def set_duration(self, duration: float) -> None:
        """Set the sound duration."""
        self._current_duration = duration
        self._regenerate_waveform()

    def set_volume(self, volume: float) -> None:
        """Set the volume level (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def _regenerate_waveform(self) -> None:
        """Regenerate the waveform with current settings."""
        self._beep_data = generate_waveform(
            self._current_sound,
            self._current_duration,
            self.config,
        )

    def trigger(self) -> None:
        """Trigger sound playback."""
        with self._lock:
            self._beep_position = 0
            self._play_event.set()

    def close(self) -> None:
        """Clean up audio resources."""
        self._close_stream()
