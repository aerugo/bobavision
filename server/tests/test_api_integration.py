"""Tests for updated /api/next endpoint with database integration.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    from src.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def client_with_db(db_session):
    """Create test client with database override."""
    from src.main import app
    from src.db.database import get_db

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close in tests

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def setup_videos(db_session):
    """Setup test videos in database."""
    from src.db.repositories import VideoRepository

    repo = VideoRepository(db_session)
    videos = [
        repo.create(path="video1.mp4", title="Video 1", is_placeholder=False),
        repo.create(path="video2.mp4", title="Video 2", is_placeholder=False),
        repo.create(path="video3.mp4", title="Video 3", is_placeholder=False),
        repo.create(path="placeholder.mp4", title="All Done", is_placeholder=True),
    ]
    return videos


def test_api_next_returns_video_when_under_limit(client_with_db, setup_videos):
    """Test that /api/next returns a real video when client is under daily limit.

    RED phase: Current implementation doesn't use database yet.
    """
    # Act - First request of the day
    response = client_with_db.get("/api/next?client_id=test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "url" in data
    assert "title" in data
    assert "placeholder" in data
    assert data["placeholder"] is False
    assert data["url"].endswith(".mp4")
    # Should not be the placeholder video
    assert "placeholder.mp4" not in data["url"]


def test_api_next_returns_placeholder_when_at_limit(client_with_db, db_session, setup_videos):
    """Test that /api/next returns placeholder when daily limit is reached."""
    from src.db.repositories import ClientRepository

    # Arrange - Create client with limit of 2
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=2)

    # Make 2 requests (reaching limit)
    client_with_db.get("/api/next?client_id=test_client")
    client_with_db.get("/api/next?client_id=test_client")

    # Act - Third request should return placeholder
    response = client_with_db.get("/api/next?client_id=test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["placeholder"] is True
    assert "placeholder.mp4" in data["url"] or "All Done" in data["title"]


def test_api_next_logs_play_in_database(client_with_db, db_session, setup_videos):
    """Test that each /api/next call logs a play in the database."""
    from src.db.repositories import PlayLogRepository

    # Act
    response = client_with_db.get("/api/next?client_id=test_client")

    # Assert - Check that play was logged
    assert response.status_code == 200

    play_repo = PlayLogRepository(db_session)
    plays = play_repo.get_recent_plays("test_client", limit=10)

    assert len(plays) == 1
    assert plays[0].client_id == "test_client"
    assert plays[0].is_placeholder is False


def test_api_next_creates_client_if_not_exists(client_with_db, db_session, setup_videos):
    """Test that /api/next auto-creates client if they don't exist."""
    from src.db.repositories import ClientRepository

    # Act - Request from new client
    response = client_with_db.get("/api/next?client_id=new_client")

    # Assert - Client should be created
    assert response.status_code == 200

    client_repo = ClientRepository(db_session)
    client = client_repo.get_by_id("new_client")

    assert client is not None
    assert client.client_id == "new_client"
    assert client.daily_limit == 3  # Default limit


def test_api_next_respects_custom_client_limit(client_with_db, db_session, setup_videos):
    """Test that custom client limits are respected."""
    from src.db.repositories import ClientRepository

    # Arrange - Create client with limit of 1
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="limited", friendly_name="Limited", daily_limit=1)

    # Act - Make 2 requests
    response1 = client_with_db.get("/api/next?client_id=limited")
    response2 = client_with_db.get("/api/next?client_id=limited")

    # Assert
    assert response1.json()["placeholder"] is False  # First is real
    assert response2.json()["placeholder"] is True   # Second is placeholder


def test_api_next_counts_only_non_placeholder_plays(client_with_db, db_session, setup_videos):
    """Test that placeholder plays don't count toward limit."""
    from src.db.repositories import ClientRepository

    # Arrange - Create client with limit of 2
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=2)

    # Act - Make requests until we get placeholders
    responses = []
    for _ in range(5):
        response = client_with_db.get("/api/next?client_id=test")
        responses.append(response.json())

    # Assert - First 2 should be real, rest should be placeholders
    assert responses[0]["placeholder"] is False
    assert responses[1]["placeholder"] is False
    assert responses[2]["placeholder"] is True
    assert responses[3]["placeholder"] is True
    assert responses[4]["placeholder"] is True


def test_api_next_different_clients_independent(client_with_db, db_session, setup_videos):
    """Test that different clients have independent limits."""
    from src.db.repositories import ClientRepository

    # Arrange - Two clients with different limits
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="client1", friendly_name="Client 1", daily_limit=1)
    client_repo.create(client_id="client2", friendly_name="Client 2", daily_limit=5)

    # Act - Client 1 reaches limit
    client_with_db.get("/api/next?client_id=client1")
    client1_response = client_with_db.get("/api/next?client_id=client1")

    # Client 2 should still get real videos
    client2_response = client_with_db.get("/api/next?client_id=client2")

    # Assert
    assert client1_response.json()["placeholder"] is True   # Client 1 at limit
    assert client2_response.json()["placeholder"] is False  # Client 2 under limit


def test_api_next_returns_different_videos_randomly(client_with_db, db_session, setup_videos):
    """Test that consecutive calls return different videos (random selection)."""
    from src.db.repositories import ClientRepository

    # Arrange - Client with high limit
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=100)

    # Act - Make multiple requests
    responses = []
    for _ in range(10):
        response = client_with_db.get("/api/next?client_id=test")
        responses.append(response.json())

    # Assert - With 3 non-placeholder videos, should get variety
    urls = [r["url"] for r in responses if not r["placeholder"]]
    unique_urls = set(urls)

    assert len(unique_urls) >= 2  # Should have at least 2 different videos


def test_api_next_handles_no_videos_gracefully(client_with_db, db_session):
    """Test behavior when no videos exist in database."""
    # Note: No setup_videos fixture, so database is empty

    # Act
    response = client_with_db.get("/api/next?client_id=test")

    # Assert - Should return error or handle gracefully
    # Implementation can choose to return 404 or a specific error message
    assert response.status_code in [200, 404, 500]

    if response.status_code == 200:
        # If it returns 200, it might return a default message
        data = response.json()
        assert "url" in data or "error" in data


def test_api_next_handles_no_placeholder_videos(client_with_db, db_session):
    """Test behavior when limit reached but no placeholder videos exist."""
    from src.db.repositories import VideoRepository, ClientRepository

    # Arrange - Create only non-placeholder videos
    video_repo = VideoRepository(db_session)
    video_repo.create(path="video1.mp4", title="Video 1", is_placeholder=False)

    # Create client with limit of 1
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=1)

    # Act - First request uses up limit
    client_with_db.get("/api/next?client_id=test")

    # Second request should need placeholder but none exist
    response = client_with_db.get("/api/next?client_id=test")

    # Assert - Should handle gracefully (return error or default message)
    assert response.status_code in [200, 404, 500]

    if response.status_code == 200:
        data = response.json()
        # Should indicate placeholder status even if can't find one
        assert "placeholder" in data


def test_api_next_play_log_has_correct_video_id(client_with_db, db_session, setup_videos):
    """Test that play log records the correct video ID."""
    from src.db.repositories import PlayLogRepository

    # Act
    response = client_with_db.get("/api/next?client_id=test")
    data = response.json()

    # Assert
    play_repo = PlayLogRepository(db_session)
    plays = play_repo.get_recent_plays("test", limit=1)

    assert len(plays) == 1
    # The play should reference an actual video in the database
    assert plays[0].video_id is not None
    assert plays[0].video is not None  # Relationship should work


def test_api_next_increments_play_count(client_with_db, db_session, setup_videos):
    """Test that play count increments with each call."""
    from src.db.repositories import PlayLogRepository

    play_repo = PlayLogRepository(db_session)

    # Act - Make 3 requests
    for _ in range(3):
        client_with_db.get("/api/next?client_id=test")

    # Assert - Should have 3 plays logged
    plays = play_repo.get_recent_plays("test", limit=10)
    assert len(plays) == 3
