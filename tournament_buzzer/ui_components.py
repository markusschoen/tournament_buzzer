"""Reusable UI components for the tournament buzzer application.

This module provides factory functions for creating consistent UI elements
with the "locked setting" pattern used throughout the application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable


def create_status_display(parent: tk.Misc) -> tuple[tk.Frame, tk.Label, tk.Label]:
    """Create the main status display area.

    Args:
        parent: Parent widget

    Returns:
        Tuple of (frame, status_label, info_label)
    """
    frame = tk.Frame(parent, bg="grey")
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    status_label = tk.Label(
        frame,
        text="READY",
        font=("Arial", 30, "bold"),
        bg="grey",
        fg="white",
    )
    status_label.pack(expand=True)

    info_label = tk.Label(
        frame,
        text="Waiting for signals...",
        font=("Arial", 10),
        bg="grey",
        fg="white",
    )
    info_label.pack(side=tk.BOTTOM, pady=5)

    return frame, status_label, info_label


def update_status_display(
    frame: tk.Frame,
    status_label: tk.Label,
    info_label: tk.Label,
    main_text: str,
    bg_color: str,
    sub_text: str,
) -> None:
    """Update the status display with new values.

    Args:
        frame: The status frame
        status_label: The main status label
        info_label: The info label
        main_text: Text for the main status
        bg_color: Background color
        sub_text: Text for the info line
    """
    status_label.config(text=main_text, bg=bg_color)
    info_label.config(text=sub_text, bg=bg_color)
    frame.config(bg=bg_color)


class LockableCombobox:
    """A combobox that can be locked/unlocked with a Change/Set button."""

    def __init__(
        self,
        parent: tk.Misc,
        label_text: str,
        options: list[str],
        initial_value: str,
        on_change: Callable[[str], None] | None = None,
        width: int = 15,
        font_size: int = 10,
    ):
        """Create a lockable combobox setting.

        Args:
            parent: Parent frame
            label_text: Label text to display
            options: List of options for the combobox
            initial_value: Initial selected value
            on_change: Callback when value is locked in
            width: Width of the combobox
            font_size: Font size for the value label
        """
        self.options = options
        self.on_change = on_change
        self.is_locked = True
        self._current_value = initial_value

        # Create frame
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=10, pady=5)

        # Label
        tk.Label(self.frame, text=label_text).pack(side=tk.LEFT)

        # Value label (shown when locked)
        self.value_label = tk.Label(
            self.frame,
            text=initial_value,
            font=("Arial", font_size, "bold"),
            fg="#2ecc71",
        )
        self.value_label.pack(side=tk.LEFT, padx=5)

        # Combobox (hidden initially)
        self.combobox = ttk.Combobox(
            self.frame,
            values=options,
            state="readonly",
            width=width,
        )
        if initial_value in options:
            self.combobox.current(options.index(initial_value))
        elif options:
            self.combobox.current(0)

        # Change/Set button
        self.button = ttk.Button(
            self.frame,
            text="Change",
            command=self._toggle,
            width=8,
        )
        self.button.pack(side=tk.LEFT, padx=2)

    def _toggle(self) -> None:
        """Toggle between locked and edit mode."""
        if self.is_locked:
            # Switch to edit mode
            self.is_locked = False
            self.value_label.pack_forget()
            self.combobox.pack(side=tk.LEFT, padx=5, before=self.button)
            self.button.config(text="Set")
        else:
            # Lock in the selection
            self.is_locked = True
            self._current_value = self.combobox.get()
            self.combobox.pack_forget()
            self.value_label.config(text=self._current_value)
            self.value_label.pack(side=tk.LEFT, padx=5, before=self.button)
            self.button.config(text="Change")

            if self.on_change:
                self.on_change(self._current_value)

    def get_value(self) -> str:
        """Get the current value."""
        return self._current_value

    def lock_if_unlocked(self) -> None:
        """Lock the setting if currently unlocked."""
        if not self.is_locked:
            self._toggle()

    def update_options(self, options: list[str], select_first: bool = True) -> None:
        """Update the available options."""
        self.options = options
        self.combobox["values"] = options
        if options and select_first:
            self.combobox.current(0)
            if self.is_locked:
                self._current_value = options[0]
                self.value_label.config(text=self._current_value)


class LockableSpinbox:
    """A spinbox that can be locked/unlocked with a Change/Set button."""

    def __init__(
        self,
        parent: tk.Misc,
        label_text: str,
        initial_value: float,
        min_value: float,
        max_value: float,
        increment: float,
        format_str: str = "{:.1f}s",
        on_change: Callable[[float], None] | None = None,
    ):
        """Create a lockable spinbox setting.

        Args:
            parent: Parent frame
            label_text: Label text to display
            initial_value: Initial value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            increment: Step increment
            format_str: Format string for displaying the value
            on_change: Callback when value is locked in
        """
        self.min_value = min_value
        self.max_value = max_value
        self.format_str = format_str
        self.on_change = on_change
        self.is_locked = True
        self._current_value = initial_value

        # Create frame
        self.frame = tk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=10, pady=5)

        # Label
        tk.Label(self.frame, text=label_text).pack(side=tk.LEFT)

        # Value label (shown when locked)
        self.value_label = tk.Label(
            self.frame,
            text=format_str.format(initial_value),
            font=("Arial", 10, "bold"),
            fg="#2ecc71",
        )
        self.value_label.pack(side=tk.LEFT, padx=5)

        # Spinbox variable and widget (hidden initially)
        self.var = tk.DoubleVar(value=initial_value)
        self.spinbox = ttk.Spinbox(
            self.frame,
            from_=min_value,
            to=max_value,
            increment=increment,
            textvariable=self.var,
            width=6,
        )

        # Change/Set button
        self.button = ttk.Button(
            self.frame,
            text="Change",
            command=self._toggle,
            width=8,
        )
        self.button.pack(side=tk.LEFT, padx=2)

    def _toggle(self) -> None:
        """Toggle between locked and edit mode."""
        if self.is_locked:
            # Switch to edit mode
            self.is_locked = False
            self.value_label.pack_forget()
            self.spinbox.pack(side=tk.LEFT, padx=5, before=self.button)
            self.button.config(text="Set")
        else:
            # Lock in the selection
            self.is_locked = True
            try:
                value = float(self.var.get())
                self._current_value = max(self.min_value, min(self.max_value, value))
            except ValueError:
                pass  # Keep previous value

            self.spinbox.pack_forget()
            self.value_label.config(text=self.format_str.format(self._current_value))
            self.value_label.pack(side=tk.LEFT, padx=5, before=self.button)
            self.button.config(text="Change")

            if self.on_change:
                self.on_change(self._current_value)

    def get_value(self) -> float:
        """Get the current value."""
        return self._current_value

    def set_value(self, value: float) -> None:
        """Set the current value programmatically.

        Args:
            value: The new value to set
        """
        self._current_value = max(self.min_value, min(self.max_value, value))
        self.var.set(self._current_value)
        self.value_label.config(text=self.format_str.format(self._current_value))
        if self.on_change:
            self.on_change(self._current_value)


def create_volume_slider(
    parent: tk.Misc,
    initial_value: float,
    on_change: Callable[[float], None],
) -> tuple[tk.Frame, ttk.Scale, tk.Label]:
    """Create a volume slider control.

    Args:
        parent: Parent widget
        initial_value: Initial volume (0-100)
        on_change: Callback for volume changes

    Returns:
        Tuple of (frame, slider, value_label)
    """
    frame = tk.Frame(parent)
    frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(frame, text="Volume:").pack(side=tk.LEFT)

    var = tk.DoubleVar(value=initial_value)
    value_label = tk.Label(frame, text=f"{int(initial_value)}%", width=5)

    def _on_change(value: str) -> None:
        vol = float(value)
        value_label.config(text=f"{int(vol)}%")
        on_change(vol / 100.0)

    slider = ttk.Scale(
        frame,
        from_=0,
        to=100,
        variable=var,
        orient=tk.HORIZONTAL,
        command=_on_change,
    )
    slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    value_label.pack(side=tk.LEFT)

    return frame, slider, value_label


def create_log_display(parent: tk.Misc) -> tuple[tk.LabelFrame, tk.Text]:
    """Create the event log display area.

    Args:
        parent: Parent widget

    Returns:
        Tuple of (frame, text_widget)
    """
    frame = tk.LabelFrame(parent, text="Event Log")
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    text = tk.Text(frame, height=8, state=tk.DISABLED, font=("Courier", 9))
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text.pack(fill=tk.BOTH, expand=True)

    return frame, text


def append_to_log_display(text_widget: tk.Text, message: str) -> None:
    """Append a message to the log display.

    Args:
        text_widget: The text widget to append to
        message: Message to append
    """
    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, message + "\n")
    text_widget.see(tk.END)
    text_widget.config(state=tk.DISABLED)


def clear_log_display(text_widget: tk.Text) -> None:
    """Clear all content from the log display.

    Args:
        text_widget: The text widget to clear
    """
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.config(state=tk.DISABLED)
