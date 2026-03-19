"""Main application module for the HEMA Tournament Buzzer.

This module ties together all components and manages the application lifecycle.
"""

import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from .audio import AudioEngine, get_default_device_name, get_output_devices
from .key_listener import create_key_listener, normalize_key_name
from .config import (
    COLORS,
    DEFAULT_TRIGGER_KEYS,
    SOUND_OPTIONS,
    AppConfig,
    AudioConfig,
    TimingConfig,
    get_factory_defaults,
    load_user_defaults,
    save_user_defaults,
)
from .event_log import (
    LogEntry,
    create_log_entry,
    export_log,
    format_log_entry,
    load_log,
    save_log,
)
from .ui_components import (
    LockableCombobox,
    LockableSpinbox,
    append_to_log_display,
    clear_log_display,
    create_log_display,
    create_status_display,
    create_volume_slider,
    update_status_display,
)


def format_trigger_keys(keys: list, max_display: int = 8) -> str:
    """Format trigger keys for display.

    Args:
        keys: List of keyboard keys
        max_display: Maximum number of keys to show

    Returns:
        Formatted string of key names
    """
    key_names = [str(k).replace("Key.", "").replace("KeyCode.", "") for k in keys]
    display = ", ".join(key_names[:max_display])
    if len(keys) > max_display:
        display += "..."
    return f"Triggers: {display}"


class BuzzerApp(tk.Tk):
    """Main application window for the tournament buzzer."""

    def __init__(
        self,
        app_config: AppConfig | None = None,
        audio_config: AudioConfig | None = None,
        timing_config: TimingConfig | None = None,
        trigger_keys: list | None = None,
    ):
        """Initialize the buzzer application.

        Args:
            app_config: Application configuration
            audio_config: Audio configuration
            timing_config: Timing configuration
            trigger_keys: List of keys that trigger the buzzer
        """
        super().__init__()

        # Load user defaults if no config provided
        if audio_config is None or timing_config is None:
            user_audio, user_timing = load_user_defaults()
            audio_config = audio_config or user_audio
            timing_config = timing_config or user_timing

        # Configuration
        self.app_config = app_config or AppConfig()
        self.audio_config = audio_config
        self.timing_config = timing_config
        self.trigger_keys = trigger_keys or DEFAULT_TRIGGER_KEYS
        # Normalized trigger key names for cross-backend comparisons
        self._trigger_key_names = {normalize_key_name(str(k)) for k in self.trigger_keys}

        # State
        self._cooldown_locked = False
        self._event_log: list[LogEntry] = []
        if self.app_config.log_enabled:
            self._event_log = load_log(self.app_config.log_file)

        # Initialize audio
        self._audio = AudioEngine(self.audio_config)

        # Timing state (will be updated by UI controls)
        self._delay_seconds = self.timing_config.default_delay
        self._cooldown_seconds = self.timing_config.default_cooldown
        self._duration_seconds = self.audio_config.default_duration
        self._volume = self.audio_config.default_volume

        # Debug mode
        self._debug_mode = tk.BooleanVar(value=False)

        # Setup window
        self.title(self.app_config.title)
        self.geometry(self.app_config.window_size)

        # Build UI
        self._build_ui()

        # Start input listener
        # On Linux, attempt to use evdev (better media key capture), but fall back to
        # pynput if evdev cannot access input devices.
        self._listener = create_key_listener(
            on_press=self._on_key_press,
            trigger_keys=self._trigger_key_names,
            suppress=True,
            debug_callback=self._add_debug_log,
        )

        try:
            self._listener.start()
        except RuntimeError as e:
            # If evdev fails (no readable /dev/input/event*), fall back to pynput.
            self._add_debug_log(f"Key listener failed: {e}. Falling back to pynput.")

            # Show user a helpful message once.
            if "TOURNAMENT_BUZZER_DISABLE_EVDEV" not in os.environ:
                messagebox.showwarning(
                    "Input Device Access",
                    "Could not access any /dev/input/event* devices.\n"
                    "The app will use a fallback listener, but media keys may not work.\n\n"
                    "To enable evdev, add your user to the `input` group (and log out/in):\n"
                    "  sudo usermod -aG input $USER\n"
                    "Then restart the app.",
                )

            os.environ["TOURNAMENT_BUZZER_DISABLE_EVDEV"] = "1"
            self._listener = create_key_listener(
                on_press=self._on_key_press,
                trigger_keys=self._trigger_key_names,
                suppress=True,
                debug_callback=self._add_debug_log,
            )
            self._listener.start()

        # Setup cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Status display
        self._status_frame, self._status_label, self._info_label = (
            create_status_display(self)
        )

        # Sound selector
        self._sound_selector = LockableCombobox(
            self,
            "Ring Sound:",
            SOUND_OPTIONS,
            SOUND_OPTIONS[0],
            on_change=self._on_sound_change,
        )

        # Add manual trigger button to sound selector frame
        btn_test = ttk.Button(
            self._sound_selector.frame,
            text="Test / Manual",
            command=self._start_trigger_sequence,
        )
        btn_test.pack(side=tk.RIGHT)

        # Device selector
        self._setup_device_selector()

        # Delay setting
        self._delay_control = LockableSpinbox(
            self,
            "Delay (seconds):",
            self.timing_config.default_delay,
            self.timing_config.min_delay,
            self.timing_config.max_delay,
            0.1,
            "{:.1f}s",
            on_change=self._on_delay_change,
        )

        # Cooldown setting
        self._cooldown_control = LockableSpinbox(
            self,
            "Cooldown (seconds):",
            self.timing_config.default_cooldown,
            self.timing_config.min_cooldown,
            self.timing_config.max_cooldown,
            0.5,
            "{:.1f}s",
            on_change=self._on_cooldown_change,
        )

        # Duration setting
        self._duration_control = LockableSpinbox(
            self,
            "Sound Duration (seconds):",
            self.audio_config.default_duration,
            self.timing_config.min_duration,
            self.timing_config.max_duration,
            0.1,
            "{:.1f}s",
            on_change=self._on_duration_change,
        )

        # Volume slider
        self._volume_slider_frame, self._volume_slider, self._volume_label = (
            create_volume_slider(
                self,
                self.audio_config.default_volume * 100,
                self._on_volume_change,
            )
        )

        # Configuration buttons
        self._setup_config_buttons()

        # Debug controls
        self._setup_debug_controls()

        # Event log display
        _, self._log_text = create_log_display(self)

        # Trigger keys info
        self._setup_trigger_keys_info()

    def _setup_device_selector(self) -> None:
        """Setup the audio device selector with refresh button."""
        devices = get_output_devices()
        device_names = [name for _, name in devices]
        self._output_devices = devices

        # Find default device
        initial_device = device_names[0] if device_names else "No device"
        default_name = get_default_device_name()
        if default_name and default_name in device_names:
            initial_device = default_name

        self._device_selector = LockableCombobox(
            self,
            "Output Device:",
            device_names,
            initial_device,
            on_change=self._on_device_change,
            width=35,
            font_size=9,
        )

        # Add refresh button
        btn_refresh = ttk.Button(
            self._device_selector.frame,
            text="↻",
            width=3,
            command=self._refresh_devices,
        )
        btn_refresh.pack(side=tk.LEFT)

    def _setup_debug_controls(self) -> None:
        """Setup debug mode controls."""
        frame = tk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(
            frame,
            text="Debug Mode (show key presses)",
            variable=self._debug_mode,
        ).pack(side=tk.LEFT)

        ttk.Button(
            frame,
            text="Clear Log",
            command=self._clear_log,
        ).pack(side=tk.RIGHT)

        ttk.Button(
            frame,
            text="Export Log",
            command=self._export_log,
        ).pack(side=tk.RIGHT, padx=5)

    def _setup_config_buttons(self) -> None:
        """Setup configuration save/reset buttons."""
        frame = tk.LabelFrame(self, text="Configuration")
        frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            frame,
            text="Save as Defaults",
            command=self._save_as_defaults,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            frame,
            text="Factory Reset",
            command=self._factory_reset,
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _setup_trigger_keys_info(self) -> None:
        """Setup the trigger keys information display."""
        frame = tk.LabelFrame(self, text="Trigger Keys")
        frame.pack(fill=tk.X, padx=10, pady=5)

        keys_text = format_trigger_keys(self.trigger_keys)
        tk.Label(
            frame,
            text=keys_text,
            font=("Courier", 9),
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=5, pady=2)

    # Event handlers

    def _on_sound_change(self, sound_name: str) -> None:
        """Handle sound selection change."""
        self._audio.set_sound(sound_name)
        self._add_debug_log(f"Sound locked to: {sound_name}")

    def _on_device_change(self, device_name: str) -> None:
        """Handle device selection change."""
        for device_id, name in self._output_devices:
            if name == device_name:
                self._audio.set_device(device_id)
                self._add_debug_log(f"Audio device locked to: {device_name}")
                break

    def _on_delay_change(self, value: float) -> None:
        """Handle delay setting change."""
        self._delay_seconds = value
        self._add_debug_log(f"Delay locked to: {value:.1f}s")

    def _on_cooldown_change(self, value: float) -> None:
        """Handle cooldown setting change."""
        self._cooldown_seconds = value
        self._add_debug_log(f"Cooldown locked to: {value:.1f}s")

    def _on_duration_change(self, value: float) -> None:
        """Handle duration setting change."""
        self._duration_seconds = value
        self._audio.set_duration(value)
        self._add_debug_log(f"Duration locked to: {value:.1f}s")

    def _on_volume_change(self, value: float) -> None:
        """Handle volume setting change."""
        self._volume = value
        self._audio.set_volume(value)

    def _refresh_devices(self) -> None:
        """Refresh the list of audio devices."""
        self._output_devices = get_output_devices()
        device_names = [name for _, name in self._output_devices]
        self._device_selector.update_options(device_names)
        self._add_debug_log(f"Refreshed audio devices: {len(device_names)} found")

    def _on_key_press(self, key) -> None:
        """Handle keyboard input."""
        key_str = str(key)
        if self._debug_mode.get():
            self.after(0, lambda: self._add_debug_log(f"Key pressed: {key_str}"))

        norm_key = normalize_key_name(key_str)
        if norm_key in self._trigger_key_names:
            self._start_trigger_sequence(key_str)

    def _start_trigger_sequence(self, key_info: str | None = None) -> None:
        """Start the buzzer trigger sequence."""
        if self._cooldown_locked:
            if self._debug_mode.get():
                self.after(0, lambda: self._add_debug_log("Blocked: In Cooldown"))
            return

        # Auto-lock settings on first trigger
        self._sound_selector.lock_if_unlocked()

        self._cooldown_locked = True

        # Get current sound and log
        current_sound = self._sound_selector.get_value()
        self._audio.set_sound(current_sound)

        # Add log entry
        entry = create_log_entry(current_sound, key_info)
        self._event_log.append(entry)
        if self.app_config.log_enabled:
            save_log(self.app_config.log_file, self._event_log)
        self._update_log_display(entry)

        # Update status
        self._update_status(
            "WAITING...",
            COLORS["waiting"],
            f"Playing in {self._delay_seconds:.1f}s",
        )

        # Run sequence in background
        threading.Thread(target=self._run_sequence, daemon=True).start()

    def _run_sequence(self) -> None:
        """Run the trigger sequence (called in background thread)."""
        # Wait for delay
        time.sleep(self._delay_seconds)

        # Play sound
        self._audio.trigger()

        # Update to triggered state
        self.after(
            0,
            lambda: self._update_status(
                "STOP!",
                COLORS["triggered"],
                "Sound Playing",
            ),
        )

        # Cooldown
        remaining = self._cooldown_seconds - self._delay_seconds
        if remaining > 0:
            time.sleep(0.5)
            self.after(
                0,
                lambda: self._update_status(
                    "COOLDOWN",
                    COLORS["cooldown"],
                    "Ignoring inputs...",
                ),
            )
            time.sleep(remaining - 0.5)

        # Ready again
        self._cooldown_locked = False
        self.after(
            0,
            lambda: self._update_status(
                "READY",
                COLORS["ready"],
                "Waiting for signals...",
            ),
        )

    def _update_status(self, main_text: str, bg_color: str, sub_text: str) -> None:
        """Update the status display."""
        update_status_display(
            self._status_frame,
            self._status_label,
            self._info_label,
            main_text,
            bg_color,
            sub_text,
        )

    def _update_log_display(self, entry: LogEntry) -> None:
        """Update the log display with a new entry."""
        line = format_log_entry(entry, self._debug_mode.get())
        append_to_log_display(self._log_text, line)

    def _add_debug_log(self, message: str) -> None:
        """Add a debug message to the log display."""
        time_str = datetime.now().strftime("%H:%M:%S")
        append_to_log_display(self._log_text, f"[{time_str}] DEBUG: {message}")

    def _clear_log(self) -> None:
        """Clear the event log."""
        self._event_log = []
        if self.app_config.log_enabled:
            save_log(self.app_config.log_file, self._event_log)
        clear_log_display(self._log_text)

    def _export_log(self) -> None:
        """Export the event log."""
        export_path = export_log(self._event_log)
        if export_path:
            self._add_debug_log(f"Log exported to {export_path}")

    def _save_as_defaults(self) -> None:
        """Save current settings as new defaults."""
        # Create config objects from current settings
        audio_config = AudioConfig(
            sample_rate=self.audio_config.sample_rate,
            default_duration=self._duration_seconds,
            default_volume=self._volume,
            fade_samples=self.audio_config.fade_samples,
        )
        timing_config = TimingConfig(
            default_delay=self._delay_seconds,
            default_cooldown=self._cooldown_seconds,
            min_delay=self.timing_config.min_delay,
            max_delay=self.timing_config.max_delay,
            min_cooldown=self.timing_config.min_cooldown,
            max_cooldown=self.timing_config.max_cooldown,
            min_duration=self.timing_config.min_duration,
            max_duration=self.timing_config.max_duration,
        )

        if save_user_defaults(audio_config, timing_config):
            self._add_debug_log("Settings saved as defaults")
            # Update stored configs
            self.audio_config = audio_config
            self.timing_config = timing_config
        else:
            self._add_debug_log("Failed to save defaults")

    def _reset_to_defaults(self) -> None:
        """Reset all settings to user defaults (or factory defaults if no user config)."""
        audio_config, timing_config = load_user_defaults()
        self._apply_config(audio_config, timing_config)
        self._add_debug_log("Settings reset to user defaults")

    def _factory_reset(self) -> None:
        """Reset all settings to factory defaults with user confirmation."""
        from tkinter import messagebox

        if messagebox.askyesno(
            "Factory Reset",
            "Are you sure you want to reset all settings to factory defaults?\n\n"
            "This will discard any saved user defaults.",
        ):
            audio_config, timing_config = get_factory_defaults()
            self._apply_config(audio_config, timing_config)
            self._add_debug_log("Settings reset to factory defaults")

    def _apply_config(
        self, audio_config: AudioConfig, timing_config: TimingConfig
    ) -> None:
        """Apply configuration to UI and internal state.

        Args:
            audio_config: Audio configuration to apply
            timing_config: Timing configuration to apply
        """
        # Update internal state
        self._delay_seconds = timing_config.default_delay
        self._cooldown_seconds = timing_config.default_cooldown
        self._duration_seconds = audio_config.default_duration
        self._volume = audio_config.default_volume

        # Update UI controls
        self._delay_control.set_value(timing_config.default_delay)
        self._cooldown_control.set_value(timing_config.default_cooldown)
        self._duration_control.set_value(audio_config.default_duration)

        # Update volume slider
        self._volume_slider.set(audio_config.default_volume * 100)
        self._volume_label.config(text=f"{int(audio_config.default_volume * 100)}%")
        self._audio.set_volume(audio_config.default_volume)

        # Update stored configs
        self.audio_config = audio_config
        self.timing_config = timing_config

    def _on_close(self) -> None:
        """Handle application close."""
        self._audio.close()
        self._listener.stop()
        self.destroy()


def main() -> None:
    """Entry point for the application."""
    app = BuzzerApp()
    app.mainloop()
