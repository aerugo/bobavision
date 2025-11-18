"""
GPIO button handler for Raspberry Pi.

This module provides a button handler that listens for GPIO button presses
and triggers a callback function when the button is pressed.
"""
import logging
from typing import Callable, Optional
from gpiozero import Button

logger = logging.getLogger(__name__)


class ButtonHandler:
    """Handler for physical button connected to GPIO pin."""

    def __init__(
        self,
        callback: Callable[[], None],
        gpio_pin: int = 17,
        pull_up: bool = True,
        bounce_time: float = 0.1
    ):
        """
        Initialize the button handler.

        Args:
            callback: Function to call when button is pressed
            gpio_pin: GPIO pin number (BCM numbering, default: 17)
            pull_up: Use internal pull-up resistor (default: True)
            bounce_time: Debounce time in seconds (default: 0.1)
        """
        self.callback = callback
        self.gpio_pin = gpio_pin
        self.pull_up = pull_up
        self.bounce_time = bounce_time
        self.button: Optional[Button] = None
        self.gpio_available = False

        try:
            # Initialize GPIO button
            self.button = Button(
                gpio_pin,
                pull_up=pull_up,
                bounce_time=bounce_time
            )

            # Register button press handler
            self.button.when_pressed = self._on_press

            self.gpio_available = True
            logger.info(f"Button handler initialized on GPIO pin {gpio_pin}")

        except Exception as e:
            logger.warning(
                f"GPIO not available (running without hardware?): {e}. "
                "Button handler will not function."
            )
            self.button = None
            self.gpio_available = False

    def _on_press(self):
        """
        Internal handler called when button is pressed.

        This wraps the user callback to catch and log any exceptions.
        """
        try:
            self.callback()
        except Exception as e:
            logger.error(f"Error in button callback: {e}", exc_info=True)

    def close(self):
        """
        Release GPIO resources.

        Should be called when the button handler is no longer needed
        to properly release the GPIO pin.
        """
        if self.button is not None:
            try:
                self.button.close()
                logger.info(f"Released GPIO pin {self.gpio_pin}")
            except Exception as e:
                logger.error(f"Error closing button: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up resources."""
        self.close()
        return False
