# BobaVision Client

Raspberry Pi client for the Kids Single-Button Media Station.

## Setup

Install dependencies using UV:

```bash
cd client
uv sync
```

## Running the Client

### On Raspberry Pi (Production)

```bash
python src/main.py
```

This will use GPIO pin 17 for the physical button.

### Local Testing (Development)

For testing on your development machine without GPIO hardware:

```bash
python run_local.py
# or with uv:
uv run python run_local.py
```

**Controls:**
- **SPACE** - Simulate button press
- **Ctrl+C** - Quit

**Requirements:**
- macOS or Linux with GUI/X11
- pynput library (installed with dev dependencies)

### Configuration

Set these environment variables to configure the client:

```bash
export BOBAVISION_SERVER_URL="http://localhost:8000"
export BOBAVISION_CLIENT_ID="my-client"
export BOBAVISION_WEB_PORT="5000"
export BOBAVISION_GPIO_PIN="17"
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=html
```

## Troubleshooting

### "pynput failed to initialize"

This happens in headless environments without a display. The `run_local.py` script requires a GUI environment (macOS, Linux with X11, or Windows).

For production use on Raspberry Pi, use `src/main.py` which uses GPIO instead.

### "GPIO not available"

This is normal when running outside of a Raspberry Pi. Use `run_local.py` for local testing.

## Directory Structure

```
client/
├── src/
│   ├── main.py           # Main application entry point
│   ├── button.py         # GPIO button handler
│   ├── player.py         # mpv video player wrapper
│   ├── http_client.py    # API client for server communication
│   ├── state_machine.py  # Application state management
│   └── web_server.py     # Local web server for UI
├── tests/                # Test suite
├── run_local.py          # Local test runner with keyboard support
└── pyproject.toml        # Dependencies and configuration
```

## See Also

- [Client Development Guide](CLAUDE.md) - Detailed development documentation
- [Grand Plan](../docs/grand_plan.md) - Project overview and roadmap
