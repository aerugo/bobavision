# Display Setup Guide for BobaVision on Raspberry Pi

## Architecture Overview

BobaVision uses a dual-display approach:
- **Chromium (kiosk mode)** - For UI screens (splash, limit reached, error)
- **MPV** - For video playback

## Screen Versions Available

### Full Version (WebGL Shaders)
- `client/ui/splash.html` - WebGL shader animation
- `server/static/limit_reached.html` - WebGL shader animation
- **Pros**: Beautiful, artistic, flowing animations
- **Cons**: Higher GPU usage, may lag on older Pis

### Lite Version (CSS Only)
- `client/ui/splash_lite.html` - CSS gradient animation
- `server/static/limit_reached_lite.html` - CSS-only animation
- **Pros**: Lightweight, smooth on all Pi models
- **Cons**: Simpler visuals

## Raspberry Pi Setup

### 1. Install Chromium

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser unclutter
```

### 2. Enable Hardware Acceleration (Optional but Recommended)

Edit `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```

Add/uncomment:
```
dtoverlay=vc4-kms-v3d
gpu_mem=256
```

Reboot:
```bash
sudo reboot
```

### 3. Launch Chromium in Kiosk Mode

Create a startup script at `/home/pi/launch_bobavision_ui.sh`:

```bash
#!/bin/bash

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0 &

# Launch Chromium in kiosk mode
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --no-first-run \
  --enable-features=WebGL \
  --ignore-gpu-blacklist \
  --enable-gpu-rasterization \
  --enable-native-gpu-memory-buffers \
  --num-raster-threads=4 \
  http://localhost:5000/
```

Make it executable:
```bash
chmod +x /home/pi/launch_bobavision_ui.sh
```

### 4. Auto-start on Boot

Add to `~/.config/lxsession/LXDE-pi/autostart`:
```bash
@/home/pi/launch_bobavision_ui.sh
```

Or create a systemd service for headless setups.

## Display Flow

### Normal Operation:
1. **Pi boots** → Chromium displays `splash.html`
2. **Button press** → Chromium shows `loading.html`
3. **Video ready** → MPV launches fullscreen, covering Chromium
4. **Video ends** → MPV closes, Chromium visible again (splash)

### Daily Limit Reached:
1. **Button press** → API returns `/static/limit_reached.html`
2. **Client detects HTML URL** → Shows in Chromium (not MPV)
3. **Beautiful animation displays** → Child sees they're done for today

## Implementation Notes

### Current Issue
Right now, the client sends ALL URLs to MPV, including HTML pages. This doesn't work because MPV can't render HTML.

### Fix Needed
Update `client/src/main.py` to detect HTML URLs and display them in Chromium instead:

```python
def _fetch_and_play_video(self):
    # ... fetch video ...

    video_url = video_data["full_url"]

    # Check if this is an HTML page (UI screen)
    if video_url.endswith('.html'):
        # Display in Chromium (already running in background)
        # Could use WebSocket to tell Chromium to navigate
        # Or use wmctrl to focus Chromium window
        pass
    else:
        # Play video with MPV (launches fullscreen over Chromium)
        self.player.play(video_url)
```

## Testing WebGL Performance

To test if WebGL works well on your Pi:

```bash
# Test full WebGL version
chromium-browser --kiosk http://localhost:5000/splash.html

# Test lite CSS version
chromium-browser --kiosk http://localhost:5000/splash_lite.html
```

Monitor GPU usage:
```bash
vcgencmd measure_temp
vcgencmd get_mem gpu
```

## Recommendations by Pi Model

| Model | Recommended Version | Notes |
|-------|-------------------|-------|
| **Pi 5** | Full WebGL | Plenty of GPU power |
| **Pi 4** | Full WebGL | Should run smoothly |
| **Pi 3** | Lite CSS | WebGL may lag, stick to CSS |
| **Pi Zero 2** | Lite CSS | Limited GPU, CSS only |

## Fallback Strategy

The WebGL versions automatically fall back to CSS gradients if WebGL is unavailable. Check browser console for errors.

## Alternative: Static Video File

If HTML display proves difficult, you could generate a simple MP4 animation:

```bash
# Create a 10-second "All Done" video with ffmpeg
ffmpeg -f lavfi -i color=c=purple:s=1920x1080:d=10 \
  -vf "drawtext=text='All Done for Today!':fontsize=100:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  -c:v libx264 all_done.mp4
```

This would work with MPV but loses the interactive animation.
