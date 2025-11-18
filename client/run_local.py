#!/usr/bin/env python3
"""
Local test runner for the BobaVision client.

This script runs the client with keyboard support for testing without GPIO hardware.
Press SPACE to simulate button presses.
"""
import logging
import os
import sys
import threading
from typing import Optional

from pynput import keyboard

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import ClientApp

logger = logging.getLogger(__name__)


class KeyboardButtonSimulator:
    """
    Simulates GPIO button presses using keyboard input.

    Listens for SPACE key presses and triggers the callback.
    """

    def __init__(self, callback):
        """
        Initialize the keyboard simulator.

        Args:
            callback: Function to call when SPACE is pressed
        """
        self.callback = callback
        self.listener: Optional[keyboard.Listener] = None
        logger.info("Keyboard button simulator initialized (press SPACE to simulate button)")

    def start(self):
        """Start listening for keyboard input."""
        self.listener = keyboard.Listener(on_press=self._on_key_press)
        self.listener.start()
        logger.info("Keyboard listener started")

    def stop(self):
        """Stop listening for keyboard input."""
        if self.listener:
            self.listener.stop()
            logger.info("Keyboard listener stopped")

    def _on_key_press(self, key):
        """
        Handle key press events.

        Args:
            key: The key that was pressed
        """
        try:
            # Check if SPACE was pressed
            if key == keyboard.Key.space:
                logger.info("SPACE pressed - triggering button callback")
                self.callback()
        except Exception as e:
            logger.error(f"Error in keyboard handler: {e}", exc_info=True)

    def close(self):
        """Alias for stop() to match ButtonHandler interface."""
        self.stop()


class LocalClientApp(ClientApp):
    """
    Modified client app that uses keyboard input instead of GPIO.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the local client app.

        This replaces the GPIO button handler with a keyboard simulator.
        """
        # Initialize parent (this will create a non-functional ButtonHandler)
        super().__init__(*args, **kwargs)

        # Replace the button handler with keyboard simulator
        original_callback = self.button_handler.callback
        self.button_handler.close()  # Clean up GPIO attempt

        self.keyboard_simulator = KeyboardButtonSimulator(callback=original_callback)

        logger.info("LocalClientApp initialized with keyboard input")

    def start(self):
        """Start the client app and keyboard listener."""
        super().start()
        self.keyboard_simulator.start()
        logger.info("Press SPACE to simulate button presses")

    def stop(self):
        """Stop the client app and keyboard listener."""
        self.keyboard_simulator.stop()
        super().stop()


def main():
    """
    Entry point for local testing.

    Reads configuration from environment variables and starts the app.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Read configuration from environment
    server_url = os.getenv("BOBAVISION_SERVER_URL", "http://localhost:8000")
    client_id = os.getenv("BOBAVISION_CLIENT_ID", "local-test-client")
    web_server_port = int(os.getenv("BOBAVISION_WEB_PORT", "5000"))
    gpio_pin = int(os.getenv("BOBAVISION_GPIO_PIN", "17"))

    print("=" * 70)
    print("BobaVision Local Test Client")
    print("=" * 70)
    print(f"Server URL:    {server_url}")
    print(f"Client ID:     {client_id}")
    print(f"Web Port:      {web_server_port}")
    print(f"GPIO Pin:      {gpio_pin} (simulated with keyboard)")
    print()
    print("Controls:")
    print("  SPACE - Simulate button press")
    print("  Ctrl+C - Quit")
    print("=" * 70)
    print()

    # Create and run the application
    app = LocalClientApp(
        server_url=server_url,
        client_id=client_id,
        web_server_port=web_server_port,
        gpio_pin=gpio_pin
    )

    app.run()


if __name__ == "__main__":
    main()
