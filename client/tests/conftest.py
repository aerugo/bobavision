"""Shared test fixtures for client tests."""
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_gpio():
    """Mock gpiozero.Button for testing without hardware."""
    with patch('gpiozero.Button') as mock_button_class:
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance
        yield mock_button_instance


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing without server."""
    mock = Mock()
    mock.get_next_video.return_value = {
        "url": "http://server:8000/media/test.mp4",
        "title": "Test Video",
        "placeholder": False
    }
    return mock


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing mpv without actual process."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        yield mock_popen
