# Test Screenshots

This directory contains screenshots captured during Playwright end-to-end tests.

## How to Generate Screenshots

To run the Playwright tests and capture screenshots:

```bash
cd client
ENABLE_PLAYWRIGHT_TESTS=1 python -m pytest tests/test_e2e_client_server_streaming.py -v -s
```

**Note**: Playwright tests require a proper display environment (X11, Wayland, or virtual framebuffer).

## Expected Screenshots

When tests run successfully, the following screenshots will be captured:

1. `01_splash_screen.png` - Client UI splash screen
2. `02_server_api_root.png` - Server API root endpoint
3. `05_loading_screen.png` - Client loading screen
4. `06_all_done_screen.png` - "All done for today" screen
5. `07_error_screen.png` - Error screen with retry countdown
6. `10_system_operational.png` - Final system operational screenshot

## Running in Docker/CI

For containerized environments without display:

```bash
# Install xvfb (virtual framebuffer)
apt-get install -y xvfb

# Run with virtual display
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python -m pytest tests/test_e2e_client_server_streaming.py -v -s
```

## Running on Raspberry Pi

The tests will run natively on Raspberry Pi with display connected:

```bash
cd /home/pi/bobavision/client
ENABLE_PLAYWRIGHT_TESTS=1 python -m pytest tests/test_e2e_client_server_streaming.py -v -s
```

Screenshots will verify the actual UI appearance on the target hardware.

## Screenshot Verification

Screenshots serve multiple purposes:

1. **Visual regression testing** - Detect unintended UI changes
2. **Documentation** - Show what the UI actually looks like
3. **User verification** - Allow non-technical review of UI appearance
4. **Debugging** - Capture UI state during test failures

## Manual Screenshot Capture

To capture screenshots manually during development:

1. Start the client web server:
   ```bash
   cd client/src
   python -c "from web_server import WebServer; s = WebServer(); s.start(); input('Press Enter to stop...')"
   ```

2. Open browser to `http://localhost:5000` and navigate to each screen

3. Take screenshots using browser developer tools or OS screenshot utility

## Screen Layouts Tested

### Splash Screen (`01_splash_screen.png`)
- BobaVision logo
- Title text
- "Press the button to start" tagline
- Centered layout with gradient background

### Loading Screen (`05_loading_screen.png`)
- Animated spinner
- "Getting your video ready..." message
- Centered layout

### All Done Screen (`06_all_done_screen.png`)
- Celebration message
- "Great Watching!" title
- "You've watched all your videos for today"
- Return to splash after placeholder

### Error Screen (`07_error_screen.png`)
- Friendly error icon
- "Oops! Something went wrong" title
- "Trying again in 5 seconds..." countdown
- Gentle colors (no red/scary visuals)

## Responsive Design Verification

Screenshots are captured at default viewport size (1920x1080).

For responsive design testing, modify the Playwright tests to capture at different viewports:

```python
page.set_viewport_size({"width": 1280, "height": 720})  # HD
page.set_viewport_size({"width": 800, "height": 600})   # Small screen
```
