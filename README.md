# HEMA Tournament Buzzer

A customizable sound buzzer application designed for HEMA (Historical European Martial Arts) tournaments. Each tournament ring can have a distinct, easily recognizable sound that cuts through crowd noise.

## Features

- **12 Distinct Sounds** - Designed to be easily distinguishable in loud tournament environments
- **Multi-Ring Support** - Assign different sounds to different rings
- **Configurable Timing** - Adjustable delay, cooldown, and sound duration
- **Multiple Trigger Keys** - Supports various keyboard keys and presentation remotes
- **Low Latency Audio** - Responsive sound playback when you need it
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Recommended Sound Assignments

For tournaments with multiple rings, we recommend:

| Ring | Sound | Description |
|------|-------|-------------|
| Ring 1 | **Low Horn** | Deep, powerful blast (220Hz) - unmistakable low end |
| Ring 2 | **Triple Pulse** | Three quick mid-range beeps (660Hz) - rhythmic pattern |
| Ring 3 | **Rising Siren** | Upward frequency sweep (400-1000Hz) - distinctive motion |
| Ring 4 | **Staccato Beeps** | Four descending notes - musical pattern |

Additional sounds available: Double Blast, High Alert, Falling Siren, Rapid Pulse, and legacy sounds.

## Installation

### 1. Quick start (Windows/macOS)

1. Download from releases:
   - **Windows**: `tournament-buzzer-windows.exe`
   - **macOS**: `tournament-buzzer-macos.zip` (extract to get `.app`)
2. Run it.

> Linux binary is not currently published by CI; Linux users should install from source.

### 2. Linux install from source (preferred: evdev backend)

```bash
# Required system deps (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install -y libasound2-dev portaudio19-dev libx11-dev libxext-dev

# Run app with uv
git clone https://github.com/markusschoen/tournament_buzzer.git
cd tournament_buzzer
uv sync
uv run python main.py
```

- Linux prefers `python-evdev` for robust key capture.
- Fallback is `pynput`; this may miss media keys on Wayland or when input device access is blocked.
- For better Linux input permissions, add user to `input` group:
  `sudo usermod -aG input $USER` and re-login.

## Usage

1. **Launch the application**
2. **Select a sound** for your ring using the dropdown
3. **Configure timing**:
   - **Delay**: Time between trigger and sound (useful for syncing with visual signals)
   - **Cooldown**: Minimum time between sounds (prevents accidental double-triggers)
   - **Duration**: How long the sound plays
4. **Adjust volume** using the slider
5. **Trigger the buzzer** using:
   - The "Test / Manual" button
   - Default trigger keys: Volume Up, Volume Down, Page Up, Page Down

### Default Trigger Keys

The app responds to these keys by default (useful for wireless presenters):

- `Volume Up`
- `Volume Down`
- `Page Up`
- `Page Down`

## System Requirements

- **Windows**: Windows 10 or later
- **macOS**: macOS 11 (Big Sur) or later
- **Linux**: Most modern distributions (requires ALSA or PulseAudio)

> ⚠️ **Linux note (Ubuntu/Wayland)**: Some Bluetooth presentation remotes send media keys (Volume Up/Down) which may be captured by the OS before the app sees them. If you notice the system volume changing instead of the buzzer triggering, try running the app under X11 (e.g. set `GDK_BACKEND=x11`) or run with sufficient permissions to read input events.

### Linux Audio Dependencies

On Linux, you may need to install audio libraries:

```bash
# Debian/Ubuntu
sudo apt-get install libasound2-dev portaudio19-dev

# Fedora
sudo dnf install alsa-lib-devel portaudio-devel

# Arch
sudo pacman -S alsa-lib portaudio
```
### Linux Input Capture (Optional)

For reliable detection of Bluetooth remote button presses (especially media keys), the app can optionally use the `python-evdev` backend to read events from `/dev/input/event*`.

```bash
pip install evdev
```

Once enabled, the app will attempt to open all readable `/dev/input/event*` devices and will log which devices are being monitored (check the debug log panel).

> ⚠️ On many distributions, reading input event devices requires root or membership in the `input` group:
> ```bash
> sudo usermod -aG input $USER
> ```

If you run into issues with this approach (e.g., in CI or headless testing), you can force the app to use the default `pynput` backend by setting:

```bash
export TOURNAMENT_BUZZER_DISABLE_EVDEV=1
```
## Building from Source

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name tournament-buzzer main.py
```

The executable will be in the `dist/` folder.

## License

This project is privately maintained.

## Contributing

This is a private repository. Please contact the maintainer for contribution guidelines.
