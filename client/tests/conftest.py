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


# Playwright configuration for headless testing

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Configure browser context for headless testing in containerized environments.

    Adds args needed for Chromium to run in Docker/sandboxed environments
    without a display server.
    """
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    Configure browser launch arguments for headless mode.

    These arguments help Chromium run in environments without a display server,
    which is common in CI/CD and containerized environments.

    Note: Uses --single-process for containerized environments which limits
    to one test at a time but avoids crashes.
    """
    return {
        **browser_type_launch_args,
        "headless": True,
        "chromium_sandbox": False,
        "args": [
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1920,1080",
            "--single-process",  # Required for containerized environments
        ]
    }
