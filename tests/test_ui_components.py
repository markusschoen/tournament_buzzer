"""Tests for the ui_components module.

Note: These tests require a display. They use tkinter's Tk class
which may fail in headless environments. Consider using pytest-xvfb
or similar for CI environments.
"""

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from tournament_buzzer.ui_components import (
    LockableCombobox,
    LockableSpinbox,
    append_to_log_display,
    clear_log_display,
    create_log_display,
    create_status_display,
    create_volume_slider,
    update_status_display,
)


@pytest.fixture
def tk_root():
    """Create a Tk root window for testing."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        yield root
        root.destroy()
    except tk.TclError:
        pytest.skip("No display available for tkinter tests")


class TestCreateStatusDisplay:
    """Tests for create_status_display function."""

    def test_returns_tuple_of_three(self, tk_root):
        """Test that function returns (frame, status_label, info_label)."""
        result = create_status_display(tk_root)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_frame_is_widget(self, tk_root):
        """Test that first element is a Frame widget."""
        frame, _, _ = create_status_display(tk_root)

        assert isinstance(frame, tk.Frame)

    def test_labels_have_default_text(self, tk_root):
        """Test that labels have default text values."""
        _, status_label, info_label = create_status_display(tk_root)

        assert status_label.cget("text") == "READY"
        assert info_label.cget("text") == "Waiting for signals..."


class TestUpdateStatusDisplay:
    """Tests for update_status_display function."""

    def test_updates_all_components(self, tk_root):
        """Test that all components are updated."""
        frame, status_label, info_label = create_status_display(tk_root)

        update_status_display(
            frame, status_label, info_label, "TEST", "#ff0000", "Test info"
        )

        assert status_label.cget("text") == "TEST"
        assert info_label.cget("text") == "Test info"
        assert status_label.cget("bg") == "#ff0000"


class TestLockableCombobox:
    """Tests for LockableCombobox class."""

    def test_initialization(self, tk_root):
        """Test that combobox initializes correctly."""
        combo = LockableCombobox(
            tk_root, "Test Label:", ["Option 1", "Option 2"], "Option 1"
        )

        assert combo.is_locked is True
        assert combo.get_value() == "Option 1"

    def test_toggle_unlocks(self, tk_root):
        """Test that toggle unlocks the combobox."""
        combo = LockableCombobox(tk_root, "Test:", ["A", "B"], "A")

        combo._toggle()

        assert combo.is_locked is False
        assert combo.button.cget("text") == "Set"

    def test_toggle_locks_and_calls_callback(self, tk_root):
        """Test that toggle locks and calls callback."""
        callback = MagicMock()
        combo = LockableCombobox(tk_root, "Test:", ["A", "B"], "A", on_change=callback)

        # Unlock first
        combo._toggle()
        combo.combobox.current(1)  # Select "B"
        # Lock
        combo._toggle()

        assert combo.is_locked is True
        assert combo.get_value() == "B"
        callback.assert_called_once_with("B")

    def test_lock_if_unlocked(self, tk_root):
        """Test lock_if_unlocked method."""
        combo = LockableCombobox(tk_root, "Test:", ["A", "B"], "A")

        # Already locked - should do nothing
        combo.lock_if_unlocked()
        assert combo.is_locked is True

        # Unlock then call lock_if_unlocked
        combo._toggle()  # unlock
        assert combo.is_locked is False

        combo.lock_if_unlocked()
        assert combo.is_locked is True

    def test_update_options(self, tk_root):
        """Test updating available options."""
        combo = LockableCombobox(tk_root, "Test:", ["A", "B"], "A")

        combo.update_options(["X", "Y", "Z"])

        assert combo.options == ["X", "Y", "Z"]
        assert combo.get_value() == "X"


class TestLockableSpinbox:
    """Tests for LockableSpinbox class."""

    def test_initialization(self, tk_root):
        """Test that spinbox initializes correctly."""
        spinbox = LockableSpinbox(tk_root, "Value:", 5.0, 0.0, 10.0, 0.5)

        assert spinbox.is_locked is True
        assert spinbox.get_value() == 5.0

    def test_toggle_unlocks(self, tk_root):
        """Test that toggle unlocks the spinbox."""
        spinbox = LockableSpinbox(tk_root, "Value:", 5.0, 0.0, 10.0, 0.5)

        spinbox._toggle()

        assert spinbox.is_locked is False
        assert spinbox.button.cget("text") == "Set"

    def test_toggle_locks_and_clamps_value(self, tk_root):
        """Test that toggle locks and clamps value to range."""
        spinbox = LockableSpinbox(tk_root, "Value:", 5.0, 0.0, 10.0, 0.5)

        # Unlock
        spinbox._toggle()
        spinbox.var.set(15.0)  # Above max
        # Lock
        spinbox._toggle()

        assert spinbox.is_locked is True
        assert spinbox.get_value() == 10.0  # Clamped to max

    def test_callback_called_on_lock(self, tk_root):
        """Test that callback is called when locking."""
        callback = MagicMock()
        spinbox = LockableSpinbox(
            tk_root, "Value:", 5.0, 0.0, 10.0, 0.5, on_change=callback
        )

        spinbox._toggle()  # unlock
        spinbox.var.set(7.5)
        spinbox._toggle()  # lock

        callback.assert_called_once_with(7.5)

    def test_format_string(self, tk_root):
        """Test custom format string."""
        spinbox = LockableSpinbox(
            tk_root, "Value:", 5.0, 0.0, 10.0, 0.5, format_str="{:.2f} units"
        )

        assert "5.00 units" in spinbox.value_label.cget("text")


class TestCreateVolumeSlider:
    """Tests for create_volume_slider function."""

    def test_returns_tuple_of_three(self, tk_root):
        """Test that function returns (frame, slider, label)."""
        callback = MagicMock()
        result = create_volume_slider(tk_root, 80, callback)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_initial_value(self, tk_root):
        """Test that initial value is set correctly."""
        callback = MagicMock()
        _, slider, label = create_volume_slider(tk_root, 75, callback)

        assert "75%" in label.cget("text")


class TestCreateLogDisplay:
    """Tests for create_log_display function."""

    def test_returns_tuple(self, tk_root):
        """Test that function returns (frame, text_widget)."""
        result = create_log_display(tk_root)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_text_is_disabled(self, tk_root):
        """Test that text widget starts disabled."""
        _, text = create_log_display(tk_root)

        assert text.cget("state") == "disabled"


class TestAppendToLogDisplay:
    """Tests for append_to_log_display function."""

    def test_appends_message(self, tk_root):
        """Test that message is appended to log."""
        _, text = create_log_display(tk_root)

        append_to_log_display(text, "Test message")

        text.config(state=tk.NORMAL)
        content = text.get(1.0, tk.END)
        text.config(state=tk.DISABLED)

        assert "Test message" in content

    def test_multiple_messages(self, tk_root):
        """Test appending multiple messages."""
        _, text = create_log_display(tk_root)

        append_to_log_display(text, "Message 1")
        append_to_log_display(text, "Message 2")

        text.config(state=tk.NORMAL)
        content = text.get(1.0, tk.END)
        text.config(state=tk.DISABLED)

        assert "Message 1" in content
        assert "Message 2" in content


class TestClearLogDisplay:
    """Tests for clear_log_display function."""

    def test_clears_content(self, tk_root):
        """Test that log content is cleared."""
        _, text = create_log_display(tk_root)

        append_to_log_display(text, "Some content")
        clear_log_display(text)

        text.config(state=tk.NORMAL)
        content = text.get(1.0, tk.END).strip()
        text.config(state=tk.DISABLED)

        assert content == ""
