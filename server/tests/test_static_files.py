"""Tests for static file serving.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


def test_media_files_are_served(sample_videos):
    """Test that video files can be accessed via /media/library/ URLs.

    RED phase: This will fail because static file serving isn't configured yet.
    """
    # Arrange
    from src.main import app, set_media_directory
    set_media_directory(str(sample_videos))

    client = TestClient(app)

    # Act - Try to access a video file
    response = client.get("/media/library/video1.mp4")

    # Assert - Should return the file
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/")
    assert len(response.content) > 0


def test_media_files_return_404_for_nonexistent():
    """Test that accessing non-existent video returns 404."""
    # Arrange
    from src.main import app, set_media_directory
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        set_media_directory(tmp)
        client = TestClient(app)

        # Act - Try to access non-existent file
        response = client.get("/media/library/nonexistent.mp4")

        # Assert - Should return 404
        assert response.status_code == 404


def test_media_files_serve_nested_paths(sample_videos):
    """Test that videos in subdirectories can be accessed."""
    # Arrange
    from src.main import app, set_media_directory

    # Create nested directory structure
    subdir = sample_videos / "shows" / "episode1"
    subdir.mkdir(parents=True)
    (subdir / "video.mp4").write_text("nested video content")

    set_media_directory(str(sample_videos))
    client = TestClient(app)

    # Act - Access nested file
    response = client.get("/media/library/shows/episode1/video.mp4")

    # Assert
    assert response.status_code == 200
    assert response.content == b"nested video content"


def test_media_endpoint_prevents_directory_traversal():
    """Test that directory traversal attacks are prevented."""
    # Arrange
    from src.main import app
    client = TestClient(app)

    # Act - Try directory traversal
    response = client.get("/media/library/../../etc/passwd")

    # Assert - Should either return 404 or sanitized path
    assert response.status_code in [404, 403, 400]
