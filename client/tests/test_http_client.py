"""Tests for HTTP client that communicates with the media server."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.http_client import ApiClient


class TestApiClientInitialization:
    """Test API client initialization."""

    def test_api_client_initializes_with_server_url_and_client_id(self):
        """Test that ApiClient stores server URL and client ID."""
        # Arrange & Act
        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Assert
        assert client.server_url == "http://localhost:8000"
        assert client.client_id == "test_client"

    def test_api_client_removes_trailing_slash_from_url(self):
        """Test that trailing slash is removed from server URL."""
        # Arrange & Act
        client = ApiClient(
            server_url="http://localhost:8000/",
            client_id="test_client"
        )

        # Assert
        assert client.server_url == "http://localhost:8000"


class TestGetNextVideo:
    """Test getting next video from server."""

    @patch('httpx.get')
    def test_get_next_video_makes_correct_api_call(self, mock_get):
        """Test that get_next_video makes correct HTTP request."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "/media/library/test.mp4",
            "title": "Test Video",
            "placeholder": False
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act
        result = client.get_next_video()

        # Assert
        mock_get.assert_called_once_with(
            "http://localhost:8000/api/next?client_id=test_client",
            timeout=10
        )
        assert result["url"] == "/media/library/test.mp4"
        assert result["title"] == "Test Video"
        assert result["placeholder"] is False

    @patch('httpx.get')
    def test_get_next_video_returns_full_url(self, mock_get):
        """Test that get_next_video returns full URL."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "/media/library/test.mp4",
            "title": "Test Video",
            "placeholder": False
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act
        result = client.get_next_video()

        # Assert
        assert result["full_url"] == "http://localhost:8000/media/library/test.mp4"

    @patch('httpx.get')
    def test_get_next_video_handles_placeholder_flag(self, mock_get):
        """Test that placeholder flag is correctly handled."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "/media/library/placeholder.mp4",
            "title": "All Done",
            "placeholder": True
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act
        result = client.get_next_video()

        # Assert
        assert result["placeholder"] is True


class TestErrorHandling:
    """Test error handling in API client."""

    @patch('httpx.get')
    def test_get_next_video_handles_connection_error(self, mock_get):
        """Test graceful handling of connection errors."""
        # Arrange
        mock_get.side_effect = Exception("Connection refused")
        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            client.get_next_video()
        assert "Connection refused" in str(exc_info.value)

    @patch('httpx.get')
    def test_get_next_video_handles_http_error(self, mock_get):
        """Test handling of HTTP errors (404, 500, etc.)."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act & Assert
        with pytest.raises(Exception):
            client.get_next_video()

    @patch('httpx.get')
    def test_get_next_video_handles_timeout(self, mock_get):
        """Test handling of request timeout."""
        # Arrange
        import httpx
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act & Assert
        with pytest.raises(Exception):
            client.get_next_video()

    @patch('httpx.get')
    def test_get_next_video_handles_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client"
        )

        # Act & Assert
        with pytest.raises(ValueError):
            client.get_next_video()


class TestNetworkResilience:
    """Test network resilience features."""

    @patch('httpx.get')
    def test_get_next_video_with_custom_timeout(self, mock_get):
        """Test that custom timeout can be specified."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "url": "/media/library/test.mp4",
            "title": "Test Video",
            "placeholder": False
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = ApiClient(
            server_url="http://localhost:8000",
            client_id="test_client",
            timeout=30
        )

        # Act
        result = client.get_next_video()

        # Assert
        mock_get.assert_called_once_with(
            "http://localhost:8000/api/next?client_id=test_client",
            timeout=30
        )
