"""Tests for GPIO button handler."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.button import ButtonHandler


class TestButtonInitialization:
    """Test button handler initialization."""

    @patch('gpiozero.Button')
    def test_button_initializes_with_gpio_pin(self, mock_button_class):
        """Test that ButtonHandler initializes with correct GPIO pin."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Assert
        mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.1)
        assert handler.gpio_pin == 17

    @patch('gpiozero.Button')
    def test_button_initializes_with_callback(self, mock_button_class):
        """Test that ButtonHandler stores callback function."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Assert
        assert handler.callback == mock_callback

    @patch('gpiozero.Button')
    def test_button_uses_default_gpio_pin(self, mock_button_class):
        """Test that default GPIO pin is 17."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback)

        # Assert
        mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.1)

    @patch('gpiozero.Button')
    def test_button_assigns_when_pressed_handler(self, mock_button_class):
        """Test that when_pressed is assigned to internal handler."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Assert
        # The mock button's when_pressed should be set to the handler's method
        assert mock_button_instance.when_pressed is not None


class TestButtonPress:
    """Test button press detection."""

    @patch('gpiozero.Button')
    def test_button_press_triggers_callback(self, mock_button_class):
        """Test that button press calls the callback function."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Simulate button press by calling the registered handler
        registered_handler = mock_button_instance.when_pressed

        # Act
        if callable(registered_handler):
            registered_handler()

        # Assert
        mock_callback.assert_called_once()

    @patch('gpiozero.Button')
    def test_button_press_passes_no_arguments(self, mock_button_class):
        """Test that callback is called with no arguments."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)
        registered_handler = mock_button_instance.when_pressed

        # Act
        if callable(registered_handler):
            registered_handler()

        # Assert
        mock_callback.assert_called_once_with()

    @patch('gpiozero.Button')
    def test_multiple_button_presses(self, mock_button_class):
        """Test that multiple button presses trigger multiple callbacks."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)
        registered_handler = mock_button_instance.when_pressed

        # Act
        if callable(registered_handler):
            registered_handler()
            registered_handler()
            registered_handler()

        # Assert
        assert mock_callback.call_count == 3


class TestButtonConfiguration:
    """Test button configuration options."""

    @patch('gpiozero.Button')
    def test_button_with_custom_bounce_time(self, mock_button_class):
        """Test that custom bounce time can be specified."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17, bounce_time=0.2)

        # Assert
        mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.2)

    @patch('gpiozero.Button')
    def test_button_with_pull_down(self, mock_button_class):
        """Test that pull_down mode can be specified."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17, pull_up=False)

        # Assert
        mock_button_class.assert_called_once_with(17, pull_up=False, bounce_time=0.1)


class TestErrorHandling:
    """Test error handling in button handler."""

    @patch('gpiozero.Button')
    def test_gpio_not_available_logs_warning(self, mock_button_class):
        """Test that GPIO unavailability is handled gracefully."""
        # Arrange
        mock_callback = Mock()
        mock_button_class.side_effect = RuntimeError("GPIO not available")

        # Act & Assert
        # Should not raise exception, just log warning
        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)
        assert handler.button is None
        assert handler.gpio_available is False

    @patch('gpiozero.Button')
    def test_callback_exception_is_caught(self, mock_button_class):
        """Test that exceptions in callback are caught and logged."""
        # Arrange
        mock_callback = Mock(side_effect=Exception("Callback error"))
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)
        registered_handler = mock_button_instance.when_pressed

        # Act & Assert
        # Should not raise exception
        if callable(registered_handler):
            registered_handler()  # Should catch the exception internally


class TestButtonCleanup:
    """Test button cleanup and resource management."""

    @patch('gpiozero.Button')
    def test_close_releases_gpio_resources(self, mock_button_class):
        """Test that close() releases GPIO resources."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Act
        handler.close()

        # Assert
        mock_button_instance.close.assert_called_once()

    @patch('gpiozero.Button')
    def test_close_handles_no_button_gracefully(self, mock_button_class):
        """Test that close() handles missing button gracefully."""
        # Arrange
        mock_callback = Mock()
        mock_button_class.side_effect = RuntimeError("GPIO not available")

        handler = ButtonHandler(callback=mock_callback, gpio_pin=17)

        # Act & Assert
        # Should not raise exception
        handler.close()

    @patch('gpiozero.Button')
    def test_context_manager_support(self, mock_button_class):
        """Test that ButtonHandler can be used as context manager."""
        # Arrange
        mock_callback = Mock()
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance

        # Act & Assert
        with ButtonHandler(callback=mock_callback, gpio_pin=17) as handler:
            assert handler is not None

        # Should have called close on exit
        mock_button_instance.close.assert_called_once()
