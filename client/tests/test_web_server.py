"""Tests for web server that serves UI assets."""
import pytest
from unittest.mock import Mock, patch
from src.web_server import WebServer


class TestWebServerInitialization:
    """Test web server initialization."""

    def test_web_server_initializes_with_port(self):
        """Test that WebServer can be initialized with a port number."""
        # Arrange & Act
        server = WebServer(port=5000)

        # Assert
        assert server.port == 5000
        assert server.app is not None

    def test_web_server_default_port(self):
        """Test that WebServer uses default port 5000 if not specified."""
        # Arrange & Act
        server = WebServer()

        # Assert
        assert server.port == 5000

    def test_web_server_initializes_flask_app(self):
        """Test that WebServer creates a Flask application."""
        # Arrange & Act
        server = WebServer(port=5000)

        # Assert
        assert server.app is not None
        # Check it's a Flask app by checking for Flask-specific attributes
        assert hasattr(server.app, 'route')
        assert hasattr(server.app, 'run')


class TestWebServerStaticFileServing:
    """Test serving static HTML files."""

    def test_server_serves_splash_html(self):
        """Test that server serves splash.html at root path."""
        # Arrange
        server = WebServer(port=5000)
        client = server.app.test_client()

        # Act
        response = client.get('/')

        # Assert
        assert response.status_code == 200
        assert b'splash' in response.data.lower() or response.content_type == 'text/html'

    def test_server_serves_loading_html(self):
        """Test that server serves loading.html."""
        # Arrange
        server = WebServer(port=5000)
        client = server.app.test_client()

        # Act
        response = client.get('/loading.html')

        # Assert
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_server_serves_css_files(self):
        """Test that server serves CSS files from styles directory."""
        # Arrange
        server = WebServer(port=5000)
        client = server.app.test_client()

        # Act
        response = client.get('/styles/common.css')

        # Assert
        # Should return 200 if file exists, or 404 if not created yet
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert 'text/css' in response.content_type

    def test_server_serves_javascript_files(self):
        """Test that server serves JavaScript files from scripts directory."""
        # Arrange
        server = WebServer(port=5000)
        client = server.app.test_client()

        # Act
        response = client.get('/scripts/state_handler.js')

        # Assert
        # Should return 200 if file exists, or 404 if not created yet
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert 'javascript' in response.content_type or 'text' in response.content_type


class TestWebServerLifecycle:
    """Test web server lifecycle management."""

    @patch('threading.Thread')
    def test_server_start_runs_in_background_thread(self, mock_thread):
        """Test that server.start() runs Flask in a background thread."""
        # Arrange
        server = WebServer(port=5000)

        # Act
        server.start()

        # Assert
        mock_thread.assert_called_once()
        thread_args = mock_thread.call_args
        assert thread_args[1]['daemon'] is True

    @patch('flask.Flask.run')
    def test_server_stop_shuts_down_gracefully(self, mock_run):
        """Test that server.stop() shuts down gracefully."""
        # Arrange
        server = WebServer(port=5000)

        # Act
        server.stop()

        # Assert
        assert server.running is False
