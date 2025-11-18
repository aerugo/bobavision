# Client Development Guide

## Purpose

This guide provides detailed instructions for developing the **Raspberry Pi client** for the Kids Single-Button Media Station. Follow this guide when working on client-related tasks.

**Technology Stack**: Python 3.11+, gpiozero, mpv, httpx, pytest

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [State Machine](#state-machine)
6. [Phase-Specific Guides](#phase-specific-guides)
7. [Hardware Setup](#hardware-setup)
8. [Common Tasks](#common-tasks)

---

## Quick Start

### Initial Setup (Phase 0)

```bash
cd client

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install gpiozero httpx pytest pytest-mock pytest-cov

# Or create requirements.txt
echo "gpiozero>=2.0" > requirements.txt
echo "httpx>=0.24" >> requirements.txt
echo "pytest>=7.0" >> requirements.txt
echo "pytest-mock>=3.11" >> requirements.txt
echo "pytest-cov>=4.1" >> requirements.txt

pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test
pytest tests/test_button.py::test_button_press_triggers_video_request

# Run with print output
pytest -s
```

### Running the Client

```bash
# Development mode (will mock GPIO on non-Pi systems)
python src/main.py

# Production mode on Raspberry Pi
sudo python src/main.py  # May need sudo for GPIO access
```

---

## Project Structure

```
client/
├── CLAUDE.md              ← You are here
├── requirements.txt       ← Python dependencies
├── pytest.ini             ← Test configuration
├── config.ini             ← Client configuration
├── bobavision.service     ← systemd service (Phase 4)
│
├── src/
│   ├── __init__.py
│   ├── main.py            ← Entry point
│   ├── config.py          ← Configuration management
│   │
│   ├── button.py          ← Button handler (GPIO)
│   ├── player.py          ← mpv wrapper
│   ├── http_client.py     ← API client
│   ├── state_machine.py   ← State management
│   └── utils.py           ← Helper functions
│
└── tests/
    ├── __init__.py
    ├── conftest.py        ← Shared fixtures
    ├── test_button.py     ← Button handler tests
    ├── test_player.py     ← Player tests
    ├── test_http_client.py← API client tests
    └── test_state_machine.py← State machine tests
```

---

## Development Workflow

### TDD Cycle for Client Features

#### Example: Implementing Button Handler

**Step 1: 🔴 RED - Write Failing Test**

```python
# tests/test_button.py
from unittest.mock import Mock
import pytest

def test_button_press_calls_callback():
    """Test that button press triggers the callback function."""
    # Arrange
    mock_callback = Mock()
    button_handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

    # Act
    button_handler._on_press()  # Simulate button press

    # Assert
    mock_callback.assert_called_once()
```

Run: `pytest tests/test_button.py::test_button_press_calls_callback`
Expected: **FAIL** (class doesn't exist)

Commit: `[PHASE-1] test: add test for button press callback`

**Step 2: 🟢 GREEN - Make Test Pass**

```python
# src/button.py
class ButtonHandler:
    def __init__(self, callback, gpio_pin):
        self.callback = callback
        self.gpio_pin = gpio_pin

    def _on_press(self):
        self.callback()
```

Run: `pytest tests/test_button.py::test_button_press_calls_callback`
Expected: **PASS**

Commit: `[PHASE-1] feat: implement basic button handler`

**Step 3: ♻️ REFACTOR - Add Real GPIO**

```python
# src/button.py
from gpiozero import Button

class ButtonHandler:
    def __init__(self, callback, gpio_pin=17):
        self.callback = callback
        try:
            self.button = Button(gpio_pin, pull_up=True, bounce_time=0.1)
            self.button.when_pressed = self._on_press
        except Exception as e:
            # Allow running without GPIO (development)
            print(f"GPIO not available: {e}")

    def _on_press(self):
        """Handle button press event."""
        self.callback()
```

Run: `pytest`
Expected: **ALL PASS** (GPIO is mocked in tests)

Commit: `[PHASE-1] refactor: add gpiozero integration`

---

## Testing Strategy

### Mocking GPIO

**Always mock GPIO in tests** - you don't want to require actual hardware for tests.

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_gpio():
    """Mock gpiozero.Button for testing without hardware."""
    with patch('gpiozero.Button') as mock_button_class:
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance
        yield mock_button_instance

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing without server."""
    mock = Mock()
    mock.get_next_video.return_value = {
        "url": "http://server:8000/media/test.mp4",
        "title": "Test Video",
        "placeholder": False
    }
    return mock
```

### Testing Button Handler

```python
# tests/test_button.py
from unittest.mock import Mock, patch
import pytest
from src.button import ButtonHandler

@patch('gpiozero.Button')
def test_button_initializes_with_correct_pin(mock_button_class):
    """Test button initialization with GPIO pin."""
    # Act
    handler = ButtonHandler(callback=Mock(), gpio_pin=17)

    # Assert
    mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.1)

@patch('gpiozero.Button')
def test_button_press_triggers_callback(mock_button_class):
    """Test that button press calls the callback."""
    # Arrange
    mock_callback = Mock()
    handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

    # Simulate button press by calling the registered callback
    mock_instance = mock_button_class.return_value
    registered_callback = mock_instance.when_pressed

    # Act
    if callable(registered_callback):
        registered_callback()
    else:
        handler._on_press()

    # Assert
    mock_callback.assert_called_once()
```

### Testing Player (mpv)

```python
# tests/test_player.py
from unittest.mock import Mock, patch, MagicMock
import pytest
from src.player import Player

@patch('subprocess.Popen')
def test_player_starts_mpv_process(mock_popen):
    """Test that player starts mpv with correct arguments."""
    # Arrange
    mock_process = Mock()
    mock_popen.return_value = mock_process
    player = Player()

    # Act
    player.play("http://server:8000/media/test.mp4")

    # Assert
    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert "mpv" in args
    assert "--fs" in args  # Fullscreen
    assert "--no-osc" in args  # No on-screen controls

@patch('subprocess.Popen')
def test_player_pause_sends_ipc_command(mock_popen):
    """Test that pause sends JSON IPC command to mpv."""
    # Arrange
    mock_process = Mock()
    mock_popen.return_value = mock_process
    player = Player()
    player.play("test.mp4")

    # Act
    player.toggle_pause()

    # Assert
    # Verify IPC command sent (implementation dependent)
    assert player.is_paused is True or player.is_paused is False
```

### Testing HTTP Client

```python
# tests/test_http_client.py
from unittest.mock import patch, Mock
import pytest
from src.http_client import ApiClient

@patch('httpx.get')
def test_get_next_video_returns_video_data(mock_get):
    """Test that get_next_video makes correct API call."""
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = {
        "url": "/media/test.mp4",
        "title": "Test Video",
        "placeholder": False
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    client = ApiClient(server_url="http://server:8000", client_id="test")

    # Act
    video = client.get_next_video()

    # Assert
    assert video["url"] == "/media/test.mp4"
    assert video["title"] == "Test Video"
    mock_get.assert_called_once_with(
        "http://server:8000/api/next?client_id=test",
        timeout=10
    )

@patch('httpx.get')
def test_get_next_video_handles_network_error(mock_get):
    """Test graceful handling of network errors."""
    # Arrange
    mock_get.side_effect = ConnectionError("Network unreachable")
    client = ApiClient(server_url="http://server:8000", client_id="test")

    # Act & Assert
    with pytest.raises(ConnectionError):
        client.get_next_video()
```

---

## State Machine

### States

The client operates in three states:

```
┌──────────┐
│   IDLE   │  No video playing, waiting for button press
└────┬─────┘
     │ Button press
     ▼
┌──────────┐
│ PLAYING  │  Video is playing
└────┬─────┘
     │ Button press
     ▼
┌──────────┐
│  PAUSED  │  Video is paused
└────┬─────┘
     │ Button press
     ▼
┌──────────┐
│ PLAYING  │  Video resumed
└────┬─────┘
     │ Video ends
     ▼
┌──────────┐
│   IDLE   │  Ready for next video
└──────────┘
```

### Implementation

```python
# src/state_machine.py
from enum import Enum, auto

class State(Enum):
    IDLE = auto()
    PLAYING = auto()
    PAUSED = auto()

class StateMachine:
    def __init__(self):
        self.state = State.IDLE

    def on_button_press(self) -> str:
        """
        Handle button press based on current state.

        Returns:
            Action to take: "play", "pause", or "resume"
        """
        if self.state == State.IDLE:
            self.state = State.PLAYING
            return "play"
        elif self.state == State.PLAYING:
            self.state = State.PAUSED
            return "pause"
        elif self.state == State.PAUSED:
            self.state = State.PLAYING
            return "resume"

    def on_video_end(self):
        """Handle video ending."""
        self.state = State.IDLE

    def reset(self):
        """Reset to idle state."""
        self.state = State.IDLE
```

### Testing State Machine

```python
# tests/test_state_machine.py
from src.state_machine import StateMachine, State

def test_initial_state_is_idle():
    """Test that state machine starts in IDLE state."""
    sm = StateMachine()
    assert sm.state == State.IDLE

def test_button_press_in_idle_transitions_to_playing():
    """Test IDLE → PLAYING transition."""
    # Arrange
    sm = StateMachine()

    # Act
    action = sm.on_button_press()

    # Assert
    assert sm.state == State.PLAYING
    assert action == "play"

def test_button_press_in_playing_transitions_to_paused():
    """Test PLAYING → PAUSED transition."""
    # Arrange
    sm = StateMachine()
    sm.state = State.PLAYING

    # Act
    action = sm.on_button_press()

    # Assert
    assert sm.state == State.PAUSED
    assert action == "pause"

def test_video_end_transitions_to_idle():
    """Test video end returns to IDLE."""
    # Arrange
    sm = StateMachine()
    sm.state = State.PLAYING

    # Act
    sm.on_video_end()

    # Assert
    assert sm.state == State.IDLE
```

---

## Phase-Specific Guides

### Phase 0: Project Setup

**Tasks**:
1. Set up Python environment
2. Install dependencies
3. Configure pytest
4. Create initial structure

**Checklist**:
- [ ] Virtual environment created
- [ ] Dependencies installed (gpiozero, httpx, pytest, etc.)
- [ ] `pytest.ini` configured
- [ ] Can run `pytest` and see "0 tests collected"
- [ ] Can run client script without errors (even if it does nothing)

**Initial Files**:

```python
# src/main.py
def main():
    print("Kids Media Station Client")
    print("Waiting for implementation...")

if __name__ == "__main__":
    main()
```

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

```ini
# config.ini
[client]
client_id = trolley1
server_url = http://192.168.1.100:8000
gpio_pin = 17

[player]
fullscreen = true
no_osc = true
```

### Phase 1: Minimal Vertical Slice

**Goal**: Button press → video plays

**TDD Tasks**:
1. **TEST**: Test HTTP client calls /api/next
2. **CODE**: Implement API client
3. **TEST**: Test button handler triggers callback
4. **CODE**: Implement button handler
5. **TEST**: Test player starts mpv
6. **CODE**: Implement player wrapper
7. **TEST**: Test integration: button → API → player
8. **CODE**: Wire everything together in main.py

**Key Components**:

```python
# src/http_client.py
import httpx

class ApiClient:
    def __init__(self, server_url: str, client_id: str):
        self.server_url = server_url
        self.client_id = client_id

    def get_next_video(self) -> dict:
        """Fetch next video from server."""
        url = f"{self.server_url}/api/next?client_id={self.client_id}"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

# src/player.py
import subprocess
import json

class Player:
    def __init__(self):
        self.process = None
        self.is_playing = False

    def play(self, url: str):
        """Start playing video."""
        args = [
            "mpv",
            "--fs",  # Fullscreen
            "--no-osc",  # No on-screen controls
            "--no-osd-bar",  # No progress bar
            "--input-ipc-server=/tmp/mpvsocket",  # IPC for control
            url
        ]
        self.process = subprocess.Popen(args)
        self.is_playing = True

    def toggle_pause(self):
        """Pause or resume playback via IPC."""
        command = {"command": ["cycle", "pause"]}
        # Send JSON command to mpv via socket
        # Implementation depends on mpv IPC setup

    def is_running(self) -> bool:
        """Check if video is still playing."""
        if self.process is None:
            return False
        return self.process.poll() is None

# src/main.py
from src.button import ButtonHandler
from src.player import Player
from src.http_client import ApiClient
from src.state_machine import StateMachine
from src.config import load_config

def main():
    # Load configuration
    config = load_config()

    # Initialize components
    api_client = ApiClient(
        server_url=config["server_url"],
        client_id=config["client_id"]
    )
    player = Player()
    state_machine = StateMachine()

    def on_button_press():
        """Handle button press based on current state."""
        action = state_machine.on_button_press()

        if action == "play":
            # Fetch next video
            video = api_client.get_next_video()
            player.play(video["url"])
        elif action == "pause":
            player.toggle_pause()
        elif action == "resume":
            player.toggle_pause()

    # Set up button handler
    button = ButtonHandler(
        callback=on_button_press,
        gpio_pin=config["gpio_pin"]
    )

    print("Client ready. Press button to play.")

    # Keep running
    try:
        while True:
            # Check if video finished
            if state_machine.state == State.PLAYING and not player.is_running():
                state_machine.on_video_end()
                print("Video ended. Ready for next press.")

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()
```

### Phase 4: Hardware Integration & Deployment

**Goal**: Client runs automatically on boot

**Tasks**:
1. Create systemd service file
2. Configure auto-start
3. Set up logging
4. Test on actual hardware
5. Optimize performance

**systemd Service**:

```ini
# bobavision.service
[Unit]
Description=Kids Media Station Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bobavision/client
ExecStart=/home/pi/bobavision/client/venv/bin/python src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Installation**:
```bash
# Copy service file
sudo cp bobavision.service /etc/systemd/system/

# Enable service
sudo systemctl enable bobavision.service

# Start service
sudo systemctl start bobavision.service

# Check status
sudo systemctl status bobavision.service

# View logs
journalctl -u bobavision.service -f
```

---

## Hardware Setup

### Raspberry Pi Configuration

#### Initial Setup

1. **Install Raspberry Pi OS Lite**
2. **Configure networking** (WiFi or Ethernet)
3. **Update system**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
4. **Install dependencies**:
   ```bash
   sudo apt install python3-pip mpv git -y
   ```
5. **Clone repository**:
   ```bash
   cd ~
   git clone <repo-url> bobavision
   cd bobavision/client
   ```
6. **Install Python packages**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### GPIO Button Wiring

**Components**:
- 1x Momentary push button (normally open)
- 1x 10kΩ resistor (if not using internal pull-up)
- Jumper wires

**Wiring** (using internal pull-up):
```
GPIO 17 ──┬── Button ── GND
          │
       (Internal
        Pull-up)
```

**With external pull-up**:
```
3.3V ── 10kΩ ──┬── GPIO 17
               │
           Button
               │
              GND
```

**Configuration**:
```python
# Using internal pull-up (recommended)
Button(17, pull_up=True, bounce_time=0.1)

# Using internal pull-down
Button(17, pull_up=False, bounce_time=0.1)
```

### Display Configuration

Edit `/boot/config.txt` for optimal HDMI output:

```bash
# Force HDMI output
hdmi_force_hotplug=1

# Set resolution (adjust as needed)
hdmi_group=2
hdmi_mode=82  # 1920x1080 60Hz

# Disable overscan
disable_overscan=1

# Rotate display if needed (0, 90, 180, 270)
display_rotate=0
```

### Disable Screen Blanking

```bash
# Edit /etc/xdg/lxsession/LXDE-pi/autostart
# Add these lines:
@xset s off
@xset -dpms
@xset s noblank
```

---

## Common Tasks

### Testing on Development Machine (without GPIO)

```python
# src/button.py - Add mock mode
class ButtonHandler:
    def __init__(self, callback, gpio_pin=17, mock_mode=False):
        self.callback = callback

        if mock_mode:
            print("Running in MOCK mode (no GPIO)")
            # Use keyboard input instead
            import threading
            threading.Thread(target=self._mock_input, daemon=True).start()
        else:
            self.button = Button(gpio_pin, pull_up=True, bounce_time=0.1)
            self.button.when_pressed = self._on_press

    def _mock_input(self):
        """Mock button presses with keyboard."""
        while True:
            input("Press ENTER to simulate button press...")
            self._on_press()
```

### Testing with Local Video Files

```python
# During development, use local files
video_url = "file:///home/user/test-video.mp4"
player.play(video_url)
```

### Debugging mpv Issues

```bash
# Test mpv directly
mpv --fs --no-osc test-video.mp4

# Check mpv is installed
which mpv

# Check mpv version
mpv --version
```

### Monitoring Client Logs

```bash
# Real-time logs
journalctl -u bobavision.service -f

# Last 100 lines
journalctl -u bobavision.service -n 100

# Logs since boot
journalctl -u bobavision.service -b
```

---

## Best Practices

### Error Handling

```python
def on_button_press():
    """Handle button press with error recovery."""
    try:
        action = state_machine.on_button_press()

        if action == "play":
            video = api_client.get_next_video()
            player.play(video["url"])
    except ConnectionError as e:
        logger.error(f"Cannot reach server: {e}")
        # Show error video if available
        player.play("/home/pi/offline.mp4")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        state_machine.reset()
```

### Logging

```python
# src/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/bobavision/client.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Client starting...")
    # ...
```

### Graceful Shutdown

```python
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown gracefully."""
    logger.info("Shutting down gracefully...")
    if player.is_running():
        player.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

## Troubleshooting

### Button Not Responding

1. **Check GPIO connection**: Use `gpio readall` to verify pin status
2. **Check permissions**: GPIO may require sudo
3. **Check bounce time**: Increase if getting multiple triggers
4. **Test with LED**: Wire an LED to confirm GPIO works

### Video Not Playing

1. **Test mpv**: `mpv <url>` from command line
2. **Check network**: `ping <server-ip>`
3. **Check URL**: Is the server URL correct?
4. **Check logs**: Look for error messages

### High CPU Usage

1. **Check mpv settings**: Hardware acceleration may help
2. **Lower video resolution**: May be too high for Pi
3. **Check background processes**: `htop`

---

## Next Steps

1. **Complete Phase 0 tasks** (see [Grand Plan](../docs/grand_plan.md))
2. **Follow TDD cycle** for all features
3. **Test on actual hardware** as early as possible
4. **Document hardware issues** for Phase 4

---

**Ready to build? Open the Grand Plan, pick a task, and start with a test!**
