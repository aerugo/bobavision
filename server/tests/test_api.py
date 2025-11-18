"""Tests for API endpoints.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


def test_api_next_returns_video_url(sample_videos):
    """Test that /api/next returns a video URL.

    RED phase: This will fail because the API doesn't exist yet.
    """
    # Arrange - Import app and create test client
    from src.main import app, set_media_directory

    # Set media directory to our test fixtures
    set_media_directory(str(sample_videos))

    client = TestClient(app)

    # Act - Call the /api/next endpoint
    response = client.get("/api/next?client_id=test_client")

    # Assert - Check response structure
    assert response.status_code == 200
    data = response.json()

    # Response should have these fields
    assert "url" in data
    assert "title" in data
    assert "placeholder" in data

    # URL should point to a video file
    assert data["url"].endswith(".mp4")
    # Placeholder should be False in Phase 1 (no limits yet)
    assert data["placeholder"] is False


def test_api_next_returns_different_videos_on_consecutive_calls(sample_videos):
    """Test that consecutive calls can return different videos (random selection)."""
    # Arrange
    from src.main import app, set_media_directory
    set_media_directory(str(sample_videos))
    client = TestClient(app)

    # Act - Make multiple calls
    responses = [
        client.get("/api/next?client_id=test_client").json()
        for _ in range(10)
    ]

    # Assert - With 3 videos and 10 calls, we should get variety
    # (statistically very unlikely to get the same video 10 times)
    urls = [r["url"] for r in responses]
    unique_urls = set(urls)

    # Should have at least 2 different videos
    assert len(unique_urls) >= 2


def test_api_next_requires_client_id():
    """Test that /api/next requires client_id parameter."""
    # Arrange
    from src.main import app
    client = TestClient(app)

    # Act - Call without client_id
    response = client.get("/api/next")

    # Assert - Should return 422 (validation error)
    assert response.status_code == 422


def test_api_next_returns_valid_json():
    """Test that /api/next returns valid JSON response."""
    # Arrange
    from src.main import app, set_media_directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        # Create at least one video
        Path(tmp) / "test.mp4"
        (Path(tmp) / "test.mp4").write_text("test")
        set_media_directory(tmp)

    client = TestClient(app)

    # Act
    response = client.get("/api/next?client_id=test")

    # Assert
    assert response.headers["content-type"] == "application/json"
    # Should not raise exception
    data = response.json()
    assert isinstance(data, dict)


def test_api_root_endpoint_exists():
    """Test that root endpoint exists and returns basic info."""
    # Arrange
    from src.main import app
    client = TestClient(app)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
