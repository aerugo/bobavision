"""Tests for statistics API endpoints.

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
def sample_data(db_session):
    """Create comprehensive test data."""
    from src.db.repositories import VideoRepository, ClientRepository, PlayLogRepository

    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)
    play_repo = PlayLogRepository(db_session)

    # Create videos
    videos = [
        video_repo.create(path="video1.mp4", title="Video 1"),
        video_repo.create(path="video2.mp4", title="Video 2"),
        video_repo.create(path="video3.mp4", title="Video 3"),
    ]

    # Create clients
    client1 = client_repo.create(client_id="client1", friendly_name="Client 1", daily_limit=3)
    client2 = client_repo.create(client_id="client2", friendly_name="Client 2", daily_limit=5)

    # Log some plays for today
    play_repo.log_play("client1", videos[0].id)
    play_repo.log_play("client1", videos[1].id)
    play_repo.log_play("client2", videos[0].id)

    return {
        "videos": videos,
        "clients": [client1, client2],
    }


# GET /api/stats - System-wide statistics
def test_get_stats_returns_system_statistics(client_with_db, sample_data):
    """Test that GET /api/stats returns overall system statistics.

    RED phase: Endpoint doesn't exist yet.
    """
    # Act
    response = client_with_db.get("/api/stats")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "total_videos" in data
    assert "total_clients" in data
    assert "total_plays" in data
    assert "plays_today" in data

    # Check values
    assert data["total_videos"] == 3
    assert data["total_clients"] == 2
    assert data["total_plays"] >= 3  # At least 3 from sample_data
    assert data["plays_today"] >= 3




def test_get_stats_with_no_data(client_with_db):
    """Test that stats endpoint handles empty database gracefully."""
    # Note: No sample_data fixture, so database is empty

    # Act
    response = client_with_db.get("/api/stats")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["total_videos"] == 0
    assert data["total_clients"] == 0
    assert data["total_plays"] == 0
    assert data["plays_today"] == 0


# GET /api/stats/client/{client_id} - Per-client statistics
def test_get_client_stats_returns_client_statistics(client_with_db, sample_data):
    """Test that GET /api/stats/client/{client_id} returns per-client stats.

    RED phase: Endpoint doesn't exist yet.
    """
    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "client_id" in data
    assert "friendly_name" in data
    assert "daily_limit" in data
    assert "plays_today" in data
    assert "plays_remaining" in data
    assert "total_plays" in data
    assert "queue_size" in data

    # Check values
    assert data["client_id"] == "client1"
    assert data["friendly_name"] == "Client 1"
    assert data["daily_limit"] == 3
    assert data["plays_today"] == 2  # From sample_data
    assert data["plays_remaining"] == 1  # 3 - 2 = 1
    assert data["total_plays"] == 2
    assert data["queue_size"] == 0


def test_get_client_stats_includes_recent_plays(client_with_db, sample_data):
    """Test that client stats include recent play history."""
    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "recent_plays" in data
    assert isinstance(data["recent_plays"], list)
    assert len(data["recent_plays"]) == 2  # From sample_data

    # Check play structure
    play = data["recent_plays"][0]
    assert "video_id" in play
    assert "video_title" in play
    assert "played_at" in play


def test_get_client_stats_shows_zero_remaining_when_at_limit(client_with_db, db_session, sample_data):
    """Test that plays_remaining is 0 when limit reached."""
    from src.db.repositories import PlayLogRepository

    play_repo = PlayLogRepository(db_session)
    videos = sample_data["videos"]

    # Add one more play to reach limit (client1 has limit=3, already has 2 plays)
    play_repo.log_play("client1", videos[2].id)

    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["plays_today"] == 3
    assert data["plays_remaining"] == 0


def test_get_client_stats_returns_404_for_nonexistent_client(client_with_db):
    """Test that stats endpoint returns 404 for non-existent client."""
    # Act
    response = client_with_db.get("/api/stats/client/nonexistent")

    # Assert
    assert response.status_code == 404




def test_get_client_stats_includes_queue_size(client_with_db, db_session, sample_data):
    """Test that client stats include current queue size."""
    from src.db.repositories import QueueRepository

    queue_repo = QueueRepository(db_session)
    videos = sample_data["videos"]

    # Add videos to queue
    queue_repo.add("client1", videos[0].id)
    queue_repo.add("client1", videos[1].id)
    queue_repo.add("client1", videos[2].id)

    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["queue_size"] == 3


def test_get_client_stats_limits_recent_plays_to_10(client_with_db, db_session, sample_data):
    """Test that recent_plays is limited to last 10 plays."""
    from src.db.repositories import PlayLogRepository

    play_repo = PlayLogRepository(db_session)
    videos = sample_data["videos"]

    # Add 15 more plays (total 17 with existing 2)
    for _ in range(15):
        play_repo.log_play("client1", videos[0].id)

    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Should only return 10 most recent
    assert len(data["recent_plays"]) == 10


def test_get_client_stats_recent_plays_ordered_by_time_descending(client_with_db, db_session, sample_data):
    """Test that recent plays are ordered newest first."""
    from src.db.repositories import PlayLogRepository

    play_repo = PlayLogRepository(db_session)
    videos = sample_data["videos"]

    # Add more plays
    play_repo.log_play("client1", videos[2].id)

    # Act
    response = client_with_db.get("/api/stats/client/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    plays = data["recent_plays"]
    # Most recent should be first (video 3)
    assert plays[0]["video_title"] == "Video 3"

    # Check that timestamps are descending
    timestamps = [datetime.fromisoformat(p["played_at"]) for p in plays]
    assert timestamps == sorted(timestamps, reverse=True)


def test_get_stats_only_counts_todays_plays(client_with_db, db_session):
    """Test that plays_today only counts plays from today, not previous days."""
    from src.db.repositories import VideoRepository, ClientRepository, PlayLogRepository
    from src.db.models import PlayLog
    from datetime import datetime, timedelta

    # Create test data
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    video = video_repo.create(path="test.mp4", title="Test")
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Add play from yesterday (manual creation to control timestamp)
    yesterday_play = PlayLog(
        client_id="test",
        video_id=video.id,
        played_at=datetime.now() - timedelta(days=1)
    )
    db_session.add(yesterday_play)
    db_session.commit()

    # Add play from today
    play_repo = PlayLogRepository(db_session)
    play_repo.log_play("test", video.id)

    # Act
    response = client_with_db.get("/api/stats/client/test")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Should only count today's play
    assert data["plays_today"] == 1
    assert data["total_plays"] == 2  # Both yesterday and today
