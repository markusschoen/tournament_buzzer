"""Key input listening helpers.

This module provides a lightweight abstraction over different global key capture
mechanisms.

On Linux (especially Wayland), `pynput` may not be able to capture media keys
because the desktop compositor intercepts them first. When available, we also
try to use `evdev` to monitor input events directly (requires permissions).

This module is intentionally optional: if `python-evdev` is not installed, we
fall back to `pynput` only.

The `TOURNAMENT_BUZZER_DISABLE_EVDEV` environment variable can be set to "1" or
"true" to force using `pynput` only (useful for running in CI/test environments).
"""

from __future__ import annotations

import os
import select
import sys
import threading
from typing import Callable, Iterable, Optional, Set, Union

from loguru import logger

from pynput import keyboard

# Optional evdev backend for Linux.
try:
    from evdev import InputDevice, categorize, ecodes, list_devices
except ImportError:  # pragma: no cover
    InputDevice = None  # type: ignore
    categorize = None  # type: ignore
    ecodes = None  # type: ignore
    list_devices = None  # type: ignore


def normalize_key_name(key_str: str) -> str:
    """Normalize various key name representations into a canonical form.

    Normal forms are used to compare key events from different backends (pynput,
    evdev) in a consistent way.

    Examples:
      - "Key.media_volume_up" -> "volume_up"
      - "KEY_VOLUMEUP" -> "volume_up"
      - "'a'" -> "a"
    """

    s = key_str.strip().lower()

    # Remove pynput prefixes
    for prefix in ("key.", "keycode."):
        if s.startswith(prefix):
            s = s[len(prefix) :]

    # Remove surrounding quotes from character keys
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]

    # Remove evdev prefix
    if s.startswith("key_"):
        s = s[len("key_") :]

    # Normalize common media key naming differences
    if s.startswith("media_"):
        s = s[len("media_") :]

    # Ensure volume_up/volume_down style
    if s.startswith("volume") and not s.startswith("volume_"):
        if s.endswith("up"):
            s = "volume_up"
        elif s.endswith("down"):
            s = "volume_down"

    s = s.replace(" ", "_").replace("-", "_")
    return s


class BaseKeyListener:
    """Abstract base class for key listeners."""

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class PynputKeyListener(BaseKeyListener):
    """Key listener implementation using pynput."""

    def __init__(
        self,
        on_press: Callable[[str], None],
        suppress: bool = False,
        debug_callback: Optional[Callable[[str], None]] = None,
    ):
        self._on_press = on_press
        self._debug_callback = debug_callback
        self._listener = keyboard.Listener(on_press=self._on_press_internal, suppress=suppress)

    def _on_press_internal(self, key: Union[str, keyboard.Key, keyboard.KeyCode]) -> None:
        key_str = str(key)
        if self._debug_callback:
            self._debug_callback(f"Key pressed: {key_str}")
        self._on_press(key_str)

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()


class EvdevKeyListener(BaseKeyListener):
    """Key listener implementation using python-evdev (Linux)."""

    def __init__(
        self,
        on_press: Callable[[str], None],
        key_names: Iterable[str],
        debug_callback: Optional[Callable[[str], None]] = None,
    ):
        if InputDevice is None or list_devices is None or ecodes is None:
            raise RuntimeError("python-evdev is not available")

        self._on_press = on_press
        self._debug_callback = debug_callback
        self._key_names = {normalize_key_name(k) for k in key_names}
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._devices = self._open_input_devices()

    def _open_input_devices(self):
        devices = []
        readable = []
        unreadable = []
        all_paths = list(list_devices())

        for path in all_paths:
            if not os.access(path, os.R_OK):
                unreadable.append(path)
                continue

            try:
                dev = InputDevice(path)
                devices.append(dev)
                readable.append(path)
            except (PermissionError, OSError):
                unreadable.append(path)

        if self._debug_callback:
            self._debug_callback(
                f"evdev devices: total={len(all_paths)} readable={len(readable)} "
                f"unreadable={len(unreadable)}"
            )
            if unreadable:
                self._debug_callback(
                    "evdev unreadable devices: " + ", ".join(unreadable)
                )
            for dev in devices:
                try:
                    self._debug_callback(f"evdev device: {dev.path} ({dev.name})")
                except Exception:
                    pass

        return devices

    def _read_loop(self) -> None:
        """Read input events and trigger callbacks."""
        while self._running.is_set():
            if not self._devices:
                self._running.wait(0.1)
                continue

            # Wait on any readable device. select() allows us to avoid blocking on a
            # single device when others may have pending events.
            fd_to_dev = {dev.fd: dev for dev in self._devices}
            try:
                readable_fds, _, _ = select.select(list(fd_to_dev), [], [], 0.1)
            except (OSError, ValueError):
                # In case a device was removed concurrently
                continue

            for fd in readable_fds:
                dev = fd_to_dev.get(fd)
                if dev is None:
                    continue

                try:
                    for event in dev.read():
                        if event.type != ecodes.EV_KEY or event.value != 1:
                            continue
                        key_name = ecodes.KEY.get(event.code)
                        if not key_name:
                            continue
                        norm = normalize_key_name(key_name)
                        if self._debug_callback:
                            self._debug_callback(f"[evdev] Key pressed: {key_name} ({norm})")
                        if norm in self._key_names:
                            self._on_press(key_name)
                except BlockingIOError:
                    continue
                except OSError:
                    # Device went away
                    try:
                        self._devices.remove(dev)
                        dev.close()
                    except Exception:
                        pass

    def start(self) -> None:
        if not self._devices:
            raise RuntimeError("No readable input devices found")

        self._running.set()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass


def create_key_listener(
    on_press: Callable[[str], None],
    trigger_keys: Iterable[str],
    suppress: bool = False,
    debug_callback: Optional[Callable[[str], None]] = None,
) -> BaseKeyListener:
    """Create a key listener suitable for the current platform.

    On Linux, we attempt to use python-evdev (if installed and allowed) to capture
    key events more reliably. If that fails or is disabled, we fall back to
    pynput.
    """

    disable_evdev = os.environ.get("TOURNAMENT_BUZZER_DISABLE_EVDEV", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if sys.platform.startswith("linux") and not disable_evdev and InputDevice is not None:
        try:
            listener = EvdevKeyListener(on_press, trigger_keys, debug_callback=debug_callback)
            if debug_callback:
                debug_callback("Using python-evdev for key capture")
            return listener
        except Exception as e:  # pragma: no cover
            if debug_callback:
                debug_callback(f"Failed to initialize evdev listener: {e}")

    # Fallback to pynput
    listener = PynputKeyListener(on_press, suppress=suppress, debug_callback=debug_callback)
    if debug_callback:
        debug_callback("Using pynput for key capture")
    return listener
