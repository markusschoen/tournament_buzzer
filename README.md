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

### Option 1: Download Pre-built Executable (Recommended)

1. Go to the [Releases](../../releases) page
2. Download the executable for your operating system:
   - **Windows**: `tournament-buzzer-windows.exe`
   - **macOS**: `tournament-buzzer-macos`
   - **Linux**: `tournament-buzzer-linux`
3. Run the application

> **Note for macOS users**: You may need to right-click the app and select "Open" the first time to bypass Gatekeeper.

> **Note for Linux users**: You may need to make the file executable first: `chmod +x tournament-buzzer-linux`

### Option 2: Install from Source

Requires Python 3.13 or later.

```bash
# Clone the repository
git clone https://github.com/markusschoen/tournament_buzzer.git
cd tournament_buzzer

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install .

# Run the application
python main.py
# Or use the installed command:
tournament-buzzer
```

### Option 3: Development Installation

```bash
# Clone and enter the repository
git clone https://github.com/markusschoen/tournament_buzzer.git
cd tournament_buzzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

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
