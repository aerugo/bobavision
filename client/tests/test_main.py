"""Tests for main client application."""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from src.main import ClientApp
from src.state_machine import State


class TestClientAppInitialization:
    """Test client application initialization."""

    def test_client_app_initializes_with_required_config(self):
        """Test that ClientApp requires server_url and client_id."""
        # Arrange & Act
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")

        # Assert
        assert app.server_url == "http://localhost:8000"
        assert app.client_id == "test-client"

    def test_client_app_initializes_components(self):
        """Test that ClientApp initializes all required components."""
        # Arrange & Act
        with patch('src.main.WebServer'), \
             patch('src.main.ApiClient'), \
             patch('src.main.Player'), \
             patch('src.main.ButtonHandler'), \
             patch('src.main.StateMachine'):
            app = ClientApp(server_url="http://localhost:8000", client_id="test-client")

            # Assert
            assert app.web_server is not None
            assert app.api_client is not None
            assert app.player is not None
            assert app.button_handler is not None
            assert app.state_machine is not None

    def test_client_app_uses_custom_port_for_web_server(self):
        """Test that ClientApp can use custom port for web server."""
        # Arrange & Act
        with patch('src.main.WebServer') as mock_web_server:
            app = ClientApp(
                server_url="http://localhost:8000",
                client_id="test-client",
                web_server_port=5555
            )

            # Assert
            mock_web_server.assert_called_once_with(port=5555)


class TestClientAppLifecycle:
    """Test client application lifecycle."""

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_start_initializes_all_components(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that start() initializes all components."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")

        # Act
        app.start()

        # Assert
        app.web_server.start.assert_called_once()

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_stop_shuts_down_all_components(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that stop() shuts down all components."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.start()

        # Act
        app.stop()

        # Assert
        app.web_server.stop.assert_called_once()
        app.player.stop.assert_called_once()
        app.button_handler.close.assert_called_once()


class TestButtonPressFlow:
    """Test the flow when button is pressed."""

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_button_press_in_idle_state_fetches_video(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that button press in IDLE state fetches next video."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.state_machine.current_state = State.IDLE
        app.state_machine.on_button_press.return_value = State.LOADING
        app.api_client.get_next_video.return_value = {
            "full_url": "http://localhost:8000/media/test.mp4",
            "title": "Test Video",
            "placeholder": False
        }

        # Act
        app._on_button_press()

        # Assert
        app.state_machine.on_button_press.assert_called_once()
        app.api_client.get_next_video.assert_called_once()

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_button_press_starts_video_playback(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that video playback starts after fetching."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.state_machine.current_state = State.IDLE
        app.state_machine.on_button_press.return_value = State.LOADING
        app.api_client.get_next_video.return_value = {
            "full_url": "http://localhost:8000/media/test.mp4",
            "title": "Test Video",
            "placeholder": False
        }

        # Act
        app._on_button_press()

        # Assert
        app.player.play.assert_called_once_with("http://localhost:8000/media/test.mp4")
        app.state_machine.on_video_ready.assert_called_once()

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_button_press_handles_api_error(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that API errors transition to ERROR state."""
        import time

        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.state_machine.current_state = State.IDLE
        app.state_machine.on_button_press.return_value = State.LOADING
        app.api_client.get_next_video.side_effect = Exception("Network error")

        # Act
        app._on_button_press()

        # Wait for background thread to execute
        time.sleep(0.1)

        # Assert
        app.state_machine.on_error.assert_called_once()
        app.player.play.assert_not_called()


class TestVideoCompletion:
    """Test handling of video completion."""

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_video_completion_transitions_to_idle(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that video completion transitions back to IDLE."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.state_machine.current_state = State.PLAYING

        # Act
        app._on_video_complete()

        # Assert
        app.state_machine.on_video_end.assert_called_once()


class TestErrorRecovery:
    """Test error recovery mechanism."""

    @patch('src.main.StateMachine')
    @patch('src.main.ButtonHandler')
    @patch('src.main.Player')
    @patch('src.main.ApiClient')
    @patch('src.main.WebServer')
    def test_error_state_auto_recovers_after_timeout(
        self, mock_web_server, mock_api_client, mock_player,
        mock_button_handler, mock_state_machine
    ):
        """Test that error state recovers to IDLE after timeout."""
        # Arrange
        app = ClientApp(server_url="http://localhost:8000", client_id="test-client")
        app.state_machine.current_state = State.ERROR

        # Act
        app._recover_from_error()

        # Assert
        app.state_machine.on_error_recovery.assert_called_once()
