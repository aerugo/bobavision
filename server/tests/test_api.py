"""Tests for API endpoints.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


def test_api_next_returns_video_url(db_session):
    """Test that /api/next returns a video URL from database.

    Updated for Phase 2: Uses database instead of filesystem.
    """
    # Arrange - Set up test database with videos
    from src.db.repositories import VideoRepository
    from src.main import app
    from src.db.database import get_db

    # Populate database with test videos
    video_repo = VideoRepository(db_session)
    video_repo.create(path="video1.mp4", title="Video 1", is_placeholder=False)
    video_repo.create(path="video2.mp4", title="Video 2", is_placeholder=False)

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable startup init_db
    import src.db.database
    original_init_db = src.db.database.init_db
    src.db.database.init_db = lambda: None

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
    # Placeholder should be False when under limit
    assert data["placeholder"] is False

    # Clean up
    app.dependency_overrides.clear()
    src.db.database.init_db = original_init_db


def test_api_next_returns_different_videos_on_consecutive_calls(db_session):
    """Test that consecutive calls can return different videos (random selection).

    Updated for Phase 2: Uses database instead of filesystem.
    """
    # Arrange - Set up test database with videos
    from src.db.repositories import VideoRepository, ClientRepository
    from src.main import app
    from src.db.database import get_db

    # Populate database with test videos
    video_repo = VideoRepository(db_session)
    video_repo.create(path="video1.mp4", title="Video 1", is_placeholder=False)
    video_repo.create(path="video2.mp4", title="Video 2", is_placeholder=False)
    video_repo.create(path="video3.mp4", title="Video 3", is_placeholder=False)

    # Create client with high limit so we don't hit placeholders
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=100)

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable startup init_db
    import src.db.database
    original_init_db = src.db.database.init_db
    src.db.database.init_db = lambda: None

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

    # Clean up
    app.dependency_overrides.clear()
    src.db.database.init_db = original_init_db


def test_api_next_requires_client_id():
    """Test that /api/next requires client_id parameter."""
    # Arrange
    from src.main import app
    client = TestClient(app)

    # Act - Call without client_id
    response = client.get("/api/next")

    # Assert - Should return 422 (validation error)
    assert response.status_code == 422


def test_api_next_returns_valid_json(db_session):
    """Test that /api/next returns valid JSON response.

    Updated for Phase 2: Uses database instead of filesystem.
    """
    # Arrange - Set up test database with videos
    from src.db.repositories import VideoRepository
    from src.main import app
    from src.db.database import get_db

    # Populate database with test videos
    video_repo = VideoRepository(db_session)
    video_repo.create(path="test.mp4", title="Test Video", is_placeholder=False)

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable startup init_db
    import src.db.database
    original_init_db = src.db.database.init_db
    src.db.database.init_db = lambda: None

    client = TestClient(app)

    # Act
    response = client.get("/api/next?client_id=test")

    # Assert
    assert response.headers["content-type"] == "application/json"
    # Should not raise exception
    data = response.json()
    assert isinstance(data, dict)

    # Clean up
    app.dependency_overrides.clear()
    src.db.database.init_db = original_init_db


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
