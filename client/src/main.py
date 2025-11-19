"""
Main client application that integrates all components.

This module orchestrates the button handler, state machine, API client,
video player, and web server to create a complete kid-friendly media player.
"""
import logging
import threading
import time
from typing import Optional

from src.web_server import WebServer
from src.http_client import ApiClient
from src.player import Player
from src.button import ButtonHandler
from src.state_machine import StateMachine, State

logger = logging.getLogger(__name__)


class ClientApp:
    """
    Main client application that coordinates all components.

    This class integrates:
    - Web server for serving UI assets
    - API client for communicating with the server
    - Video player for playback
    - Button handler for physical button input
    - State machine for managing application state
    """

    def __init__(
        self,
        server_url: str,
        client_id: str,
        web_server_port: int = 5000,
        gpio_pin: int = 17
    ):
        """
        Initialize the client application.

        Args:
            server_url: URL of the media server (e.g., "http://localhost:8000")
            client_id: Unique identifier for this client
            web_server_port: Port for the local web server (default: 5000)
            gpio_pin: GPIO pin number for the button (default: 17)
        """
        self.server_url = server_url
        self.client_id = client_id
        self.running = False

        # Initialize components
        self.web_server = WebServer(port=web_server_port)
        self.api_client = ApiClient(server_url=server_url, client_id=client_id)
        self.player = Player(fullscreen=True, no_osc=True)
        self.button_handler = ButtonHandler(callback=self._on_button_press, gpio_pin=gpio_pin)
        self.state_machine = StateMachine(on_state_change=self._on_state_change)

        # Thread for monitoring video playback
        self.monitor_thread: Optional[threading.Thread] = None

        # Browser process for displaying HTML pages
        self.browser_process = None

        logger.info(
            f"ClientApp initialized: server={server_url}, "
            f"client_id={client_id}, web_port={web_server_port}"
        )

    def start(self):
        """
        Start the client application.

        This starts the web server and makes the application ready to respond
        to button presses.
        """
        if self.running:
            logger.warning("ClientApp is already running")
            return

        logger.info("Starting ClientApp...")
        self.running = True

        # Start web server
        self.web_server.start()

        logger.info("ClientApp started successfully")

    def stop(self):
        """
        Stop the client application.

        This shuts down all components gracefully.
        """
        if not self.running:
            logger.warning("ClientApp is not running")
            return

        logger.info("Stopping ClientApp...")
        self.running = False

        # Stop all components
        self.player.stop()
        self.web_server.stop()
        self.button_handler.close()

        # Clean up browser process if running
        if self.browser_process:
            if hasattr(self.browser_process, 'terminate'):
                try:
                    self.browser_process.terminate()
                    self.browser_process.wait(timeout=2)
                except Exception as e:
                    logger.warning(f"Error terminating browser process: {e}")
            self.browser_process = None

        logger.info("ClientApp stopped successfully")

    def _on_button_press(self):
        """
        Handle button press events.

        This is called when the physical button is pressed.
        """
        logger.info(f"Button pressed (current state: {self.state_machine.current_state.name})")

        # Update state machine
        new_state = self.state_machine.on_button_press()

        # If transitioning to LOADING, fetch and play next video
        if new_state == State.LOADING:
            self._fetch_and_play_video()

    def _fetch_and_play_video(self):
        """
        Fetch the next video from the server and start playback.

        This runs in a separate thread to avoid blocking the button handler.
        """
        def fetch_and_play():
            try:
                # Fetch next video from server
                logger.info("Fetching next video from server...")
                video_data = self.api_client.get_next_video()

                video_url = video_data["full_url"]
                video_title = video_data.get("title", "Unknown")
                is_placeholder = video_data.get("placeholder", False)

                logger.info(
                    f"Got video: {video_title} "
                    f"(placeholder={is_placeholder}, url={video_url})"
                )

                # Check if this is an HTML page (UI screen) vs actual video
                if video_url.endswith('.html'):
                    logger.info(f"Detected HTML page, opening in browser: {video_url}")
                    self._display_html_page(video_url)
                else:
                    # Start video playback with MPV
                    self.player.play(video_url)

                # Transition to PLAYING state
                self.state_machine.on_video_ready()

                # Start monitoring for completion
                self._start_video_monitor()

            except Exception as e:
                logger.error(f"Error fetching/playing video: {e}", exc_info=True)
                self.state_machine.on_error(str(e))

                # Schedule error recovery
                self._schedule_error_recovery()

        # Run in background thread
        thread = threading.Thread(target=fetch_and_play, daemon=True)
        thread.start()

    def _display_html_page(self, url: str):
        """
        Display an HTML page in a browser (for UI screens like limit reached).

        Args:
            url: URL of the HTML page to display
        """
        import subprocess
        import shutil
        import webbrowser
        import platform
        import os

        # Try to find a suitable browser
        # Priority: chromium (Pi) > chrome (Mac/Linux) > default browser
        browser_path = None
        browser_args = []

        # Check for Chromium (Raspberry Pi)
        chromium = shutil.which('chromium-browser') or shutil.which('chromium')
        if chromium:
            browser_path = chromium
            browser_args = [
                '--kiosk',
                '--noerrdialogs',
                '--disable-infobars',
                '--no-first-run',
            ]
            logger.info(f"Found Chromium at: {chromium}")

        # Check for Chrome (Mac/Linux/Windows)
        elif shutil.which('google-chrome'):
            browser_path = shutil.which('google-chrome')
            browser_args = ['--kiosk']
            logger.info(f"Found Chrome at: {browser_path}")

        # Check for Chrome on Mac (Application bundle)
        elif platform.system() == 'Darwin':
            chrome_mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            if os.path.exists(chrome_mac):
                browser_path = chrome_mac
                browser_args = ['--kiosk']
                logger.info(f"Found Chrome on Mac at: {chrome_mac}")

        if browser_path:
            logger.info(f"Opening HTML page in browser: {url}")
            try:
                self.browser_process = subprocess.Popen(
                    [browser_path] + browser_args + [url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return
            except Exception as e:
                logger.warning(f"Failed to launch browser: {e}")

        # Ultimate fallback: use system default browser
        logger.info(f"Using default browser to open: {url}")
        try:
            webbrowser.open(url)
            # Since we can't track the browser process, just set a flag
            self.browser_process = True  # Flag to indicate browser was opened
        except Exception as e:
            logger.error(f"Failed to open URL in browser: {e}")
            # Last resort: try MPV (will likely fail but better than nothing)
            self.player.play(url)

    def _start_video_monitor(self):
        """
        Start a thread to monitor video playback and detect completion.
        """
        def monitor():
            logger.info("Starting video monitor...")

            # Check if we're displaying HTML or playing video
            if hasattr(self, 'browser_process') and self.browser_process:
                # Monitor browser process
                logger.info("Monitoring browser process...")
                # For HTML pages (like limit reached), auto-close after 5 seconds
                import time
                time.sleep(5)

                # If browser_process is an actual process, terminate it
                if hasattr(self.browser_process, 'terminate'):
                    try:
                        self.browser_process.terminate()
                        self.browser_process.wait()
                    except Exception as e:
                        logger.warning(f"Error terminating browser: {e}")
                # Otherwise it's just a flag (webbrowser.open case)
                # and we can't close it programmatically
                logger.warning("Browser opened via webbrowser.open(); cannot be closed programmatically. User must close the browser manually.")

                self.browser_process = None
            else:
                # Monitor MPV video playback
                self.player.wait_for_completion()

            logger.info("Playback completed")

            # Transition back to IDLE
            self._on_video_complete()

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def _on_video_complete(self):
        """
        Handle video completion.

        Transitions the state machine back to IDLE.
        """
        logger.info("Video completed, returning to IDLE state")
        self.state_machine.on_video_end()

    def _on_state_change(self, old_state: State, new_state: State):
        """
        Handle state changes.

        This callback is called by the state machine whenever the state changes.

        Args:
            old_state: The previous state
            new_state: The new current state
        """
        logger.info(f"State changed: {old_state.name} → {new_state.name}")

        # TODO: Update UI via WebSocket to reflect new state
        # For now, this is a placeholder for future WebSocket integration

    def _schedule_error_recovery(self, delay: int = 5):
        """
        Schedule automatic recovery from error state.

        Args:
            delay: Delay in seconds before attempting recovery (default: 5)
        """
        def recovery():
            logger.info(f"Waiting {delay} seconds before error recovery...")
            time.sleep(delay)
            self._recover_from_error()

        thread = threading.Thread(target=recovery, daemon=True)
        thread.start()

    def _recover_from_error(self):
        """
        Attempt to recover from error state.

        Transitions back to IDLE state.
        """
        logger.info("Recovering from error state...")
        self.state_machine.on_error_recovery()

    def run(self):
        """
        Run the client application in the foreground.

        This starts the application and blocks until interrupted (Ctrl+C).
        """
        self.start()

        logger.info("ClientApp running. Press Ctrl+C to stop.")

        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            self.stop()


def main():
    """
    Entry point for the client application.

    Reads configuration from environment variables and starts the app.
    """
    import os

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Read configuration from environment
    server_url = os.getenv("BOBAVISION_SERVER_URL", "http://localhost:8000")
    client_id = os.getenv("BOBAVISION_CLIENT_ID", "default-client")
    web_server_port = int(os.getenv("BOBAVISION_WEB_PORT", "5000"))
    gpio_pin = int(os.getenv("BOBAVISION_GPIO_PIN", "17"))

    logger.info(f"Starting BobaVision Client...")
    logger.info(f"  Server URL: {server_url}")
    logger.info(f"  Client ID: {client_id}")
    logger.info(f"  Web Port: {web_server_port}")
    logger.info(f"  GPIO Pin: {gpio_pin}")

    # Create and run the application
    app = ClientApp(
        server_url=server_url,
        client_id=client_id,
        web_server_port=web_server_port,
        gpio_pin=gpio_pin
    )

    app.run()


if __name__ == "__main__":
    main()
