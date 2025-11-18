"""Tests for updated /api/next endpoint with database integration.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_db(db_session, monkeypatch):
    """Create test client with database override."""
    from src.main import app
    from src.db.database import get_db

    # Mock init_db to prevent startup event from initializing wrong database
    import src.db.database
    monkeypatch.setattr(src.db.database, "init_db", lambda: None)

    # Override database dependency to use test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close test session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # Clean up
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


# Queue-first behavior tests
def test_api_next_returns_queued_video_when_queue_not_empty(client_with_db, db_session, setup_videos):
    """Test that /api/next returns queued video when queue has items.

    RED phase: Queue-first logic not implemented yet.
    This is the core queue behavior - queued videos should be served first.
    """
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange - Create client and add video to queue
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queued_video = setup_videos[0]  # video1.mp4
    queue_repo.add(client_id="test_client", video_id=queued_video.id)

    # Act
    response = client_with_db.get("/api/next?client_id=test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Should return the queued video
    assert data["title"] == queued_video.title
    assert queued_video.path in data["url"]
    assert data["placeholder"] is False


def test_api_next_removes_video_from_queue_after_serving(client_with_db, db_session, setup_videos):
    """Test that video is removed from queue after being served."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=setup_videos[0].id)

    # Act
    client_with_db.get("/api/next?client_id=test_client")

    # Assert - Queue should be empty
    queue = queue_repo.get_by_client("test_client")
    assert len(queue) == 0


def test_api_next_returns_queued_videos_in_order(client_with_db, db_session, setup_videos):
    """Test that queued videos are returned in the correct order."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange - Add 3 videos to queue in specific order
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=10)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=setup_videos[0].id)  # video1.mp4
    queue_repo.add(client_id="test_client", video_id=setup_videos[1].id)  # video2.mp4
    queue_repo.add(client_id="test_client", video_id=setup_videos[2].id)  # video3.mp4

    # Act - Make 3 requests
    response1 = client_with_db.get("/api/next?client_id=test_client")
    response2 = client_with_db.get("/api/next?client_id=test_client")
    response3 = client_with_db.get("/api/next?client_id=test_client")

    # Assert - Should get videos in queue order
    assert setup_videos[0].title in response1.json()["title"]
    assert setup_videos[1].title in response2.json()["title"]
    assert setup_videos[2].title in response3.json()["title"]


def test_api_next_ignores_limit_for_queued_videos(client_with_db, db_session, setup_videos):
    """Test that queued videos bypass daily limit.

    This is important - parents should be able to queue videos even if
    the child has reached their daily limit.
    """
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange - Create client with limit of 1
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=1)

    # Exhaust the limit with a regular video
    client_with_db.get("/api/next?client_id=test_client")

    # Now add videos to queue
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=setup_videos[0].id)
    queue_repo.add(client_id="test_client", video_id=setup_videos[1].id)

    # Act - Request more videos (should serve from queue, not placeholder)
    response1 = client_with_db.get("/api/next?client_id=test_client")
    response2 = client_with_db.get("/api/next?client_id=test_client")

    # Assert - Should get queued videos, not placeholders
    assert response1.json()["placeholder"] is False
    assert response2.json()["placeholder"] is False
    assert setup_videos[0].title in response1.json()["title"]
    assert setup_videos[1].title in response2.json()["title"]


def test_api_next_falls_back_to_limit_logic_when_queue_empty(client_with_db, db_session, setup_videos):
    """Test that normal limit logic applies after queue is exhausted."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange - Create client with limit of 2
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=2)

    # Add one video to queue
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=setup_videos[0].id)

    # Act - First request serves from queue (counts as 1/2)
    response1 = client_with_db.get("/api/next?client_id=test_client")

    # Second request should serve random video (counts as 2/2, reaching limit)
    response2 = client_with_db.get("/api/next?client_id=test_client")

    # Third request should serve placeholder (at limit)
    response3 = client_with_db.get("/api/next?client_id=test_client")

    # Assert
    assert response1.json()["placeholder"] is False  # Queued video (1/2)
    assert response2.json()["placeholder"] is False  # Random video (2/2, at limit now)
    assert response3.json()["placeholder"] is True   # Placeholder (still at limit)


def test_api_next_logs_queued_video_plays(client_with_db, db_session, setup_videos):
    """Test that queued video plays are logged in play_log."""
    from src.db.repositories import QueueRepository, ClientRepository, PlayLogRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queued_video = setup_videos[0]
    queue_repo.add(client_id="test_client", video_id=queued_video.id)

    # Act
    client_with_db.get("/api/next?client_id=test_client")

    # Assert - Play should be logged
    play_repo = PlayLogRepository(db_session)
    plays = play_repo.get_recent_plays("test_client", limit=1)

    assert len(plays) == 1
    assert plays[0].video_id == queued_video.id
    assert plays[0].is_placeholder is False


def test_api_next_queued_videos_count_toward_limit(client_with_db, db_session, setup_videos):
    """Test that queued video plays count toward daily limit.

    Even though queued videos bypass the limit check, they should still
    count as plays for the day. This ensures proper tracking.
    """
    from src.db.repositories import QueueRepository, ClientRepository, PlayLogRepository

    # Arrange - Client with limit of 2
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=2)

    # Add one video to queue
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=setup_videos[0].id)

    # Act - Play queued video (counts as 1)
    client_with_db.get("/api/next?client_id=test_client")

    # Play random video (counts as 2, reaching limit)
    client_with_db.get("/api/next?client_id=test_client")

    # Next request should be placeholder
    response = client_with_db.get("/api/next?client_id=test_client")

    # Assert - Should get placeholder since limit reached
    assert response.json()["placeholder"] is True

    # Verify 2 non-placeholder plays logged
    play_repo = PlayLogRepository(db_session)
    today = date.today()
    count = play_repo.count_non_placeholder_plays_today("test_client", today)
    assert count == 2
