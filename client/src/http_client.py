"""
HTTP client for communicating with the media server.

This module provides an API client that fetches video information
from the FastAPI server's /api/next endpoint.
"""
import httpx
from typing import Dict, Any


class ApiClient:
    """Client for communicating with the media server API."""

    def __init__(self, server_url: str, client_id: str, timeout: int = 10):
        """
        Initialize the API client.

        Args:
            server_url: Base URL of the media server (e.g., "http://localhost:8000")
            client_id: Unique identifier for this client device
            timeout: Request timeout in seconds (default: 10)
        """
        # Remove trailing slash from server URL
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.timeout = timeout

    def get_next_video(self) -> Dict[str, Any]:
        """
        Fetch the next video to play from the server.

        Returns:
            dict: Video information containing:
                - url: Relative path to the video file
                - title: Video title
                - placeholder: Boolean indicating if this is a placeholder video
                - full_url: Complete URL to the video (server_url + url)

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If HTTP request fails
            ValueError: If response contains invalid JSON
            Exception: For other network/connection errors
        """
        # Build the API endpoint URL
        endpoint = f"{self.server_url}/api/next?client_id={self.client_id}"

        # Make HTTP GET request
        response = httpx.get(endpoint, timeout=self.timeout)

        # Raise exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()

        # Parse JSON response
        video_data = response.json()

        # Add full URL to video data
        video_data["full_url"] = f"{self.server_url}{video_data['url']}"

        return video_data

    def check_server_health(self) -> bool:
        """
        Check if the server is reachable and responding.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            response = httpx.get(f"{self.server_url}/", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
