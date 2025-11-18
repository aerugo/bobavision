"""Tests for queue management API endpoints.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
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
    """Create sample videos and clients for testing."""
    from src.db.repositories import VideoRepository, ClientRepository

    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    # Create videos
    videos = [
        video_repo.create(path="video1.mp4", title="Video 1", is_placeholder=False),
        video_repo.create(path="video2.mp4", title="Video 2", is_placeholder=False),
        video_repo.create(path="video3.mp4", title="Video 3", is_placeholder=False),
    ]

    # Create client
    client = client_repo.create(client_id="test_client", friendly_name="Test Client", daily_limit=3)

    return {"videos": videos, "client": client}


# GET /api/queue/{client_id} - Get queue
def test_get_queue_returns_empty_list_when_no_items(client_with_db, sample_data):
    """Test that GET /api/queue/{client_id} returns empty list when queue is empty.

    RED phase: Endpoint doesn't exist yet.
    """
    # Act
    response = client_with_db.get("/api/queue/test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_queue_returns_queue_items(client_with_db, db_session, sample_data):
    """Test that GET /api/queue/{client_id} returns all queue items."""
    from src.db.repositories import QueueRepository

    # Arrange - Add items to queue
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][1].id)

    # Act
    response = client_with_db.get("/api/queue/test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    # Check structure
    assert "id" in data[0]
    assert "video_id" in data[0]
    assert "position" in data[0]
    assert "video" in data[0]
    assert "created_at" in data[0]


def test_get_queue_returns_items_sorted_by_position(client_with_db, db_session, sample_data):
    """Test that queue items are returned in correct order."""
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id, position=1)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][1].id, position=2)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][2].id, position=3)

    # Act
    response = client_with_db.get("/api/queue/test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data[0]["position"] == 1
    assert data[1]["position"] == 2
    assert data[2]["position"] == 3


def test_get_queue_includes_video_details(client_with_db, db_session, sample_data):
    """Test that queue response includes video details."""
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)

    # Act
    response = client_with_db.get("/api/queue/test_client")

    # Assert
    assert response.status_code == 200
    data = response.json()

    video_data = data[0]["video"]
    assert video_data["title"] == "Video 1"
    assert video_data["path"] == "video1.mp4"


# POST /api/queue/{client_id} - Add to queue
def test_add_to_queue_single_video(client_with_db, sample_data):
    """Test that POST /api/queue/{client_id} adds a video to queue.

    RED phase: Endpoint doesn't exist yet.
    """
    # Arrange
    request_data = {
        "video_ids": [sample_data["videos"][0].id]
    }

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["added"] == 1
    assert data["total_in_queue"] == 1


def test_add_to_queue_multiple_videos(client_with_db, sample_data):
    """Test adding multiple videos to queue at once."""
    # Arrange
    request_data = {
        "video_ids": [
            sample_data["videos"][0].id,
            sample_data["videos"][1].id,
            sample_data["videos"][2].id
        ]
    }

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["added"] == 3
    assert data["total_in_queue"] == 3


def test_add_to_queue_appends_to_existing_queue(client_with_db, db_session, sample_data):
    """Test that adding videos appends to existing queue."""
    from src.db.repositories import QueueRepository

    # Arrange - Add first video directly
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)

    request_data = {
        "video_ids": [sample_data["videos"][1].id]
    }

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["added"] == 1
    assert data["total_in_queue"] == 2


def test_add_to_queue_validates_video_exists(client_with_db, sample_data):
    """Test that adding non-existent video returns error."""
    # Arrange
    request_data = {
        "video_ids": [99999]  # Non-existent video ID
    }

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code in [400, 404]


def test_add_to_queue_requires_video_ids(client_with_db, sample_data):
    """Test that video_ids field is required."""
    # Arrange
    request_data = {}  # Missing video_ids

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code == 422  # Validation error


# DELETE /api/queue/{client_id}/{queue_id} - Remove from queue
def test_remove_from_queue_deletes_item(client_with_db, db_session, sample_data):
    """Test that DELETE /api/queue/{client_id}/{queue_id} removes item.

    RED phase: Endpoint doesn't exist yet.
    """
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    item = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)

    # Act
    response = client_with_db.delete(f"/api/queue/test_client/{item.id}")

    # Assert
    assert response.status_code == 200

    # Verify it was removed
    queue = queue_repo.get_by_client("test_client")
    assert len(queue) == 0


def test_remove_from_queue_returns_404_for_nonexistent_item(client_with_db, sample_data):
    """Test that removing non-existent item returns 404."""
    # Act
    response = client_with_db.delete("/api/queue/test_client/99999")

    # Assert
    assert response.status_code == 404


def test_remove_from_queue_only_removes_for_correct_client(client_with_db, db_session, sample_data):
    """Test that delete only works for items belonging to the specified client."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange - Create second client
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="other_client", friendly_name="Other", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    test_item = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    other_item = queue_repo.add(client_id="other_client", video_id=sample_data["videos"][1].id)

    # Act - Try to delete other client's item
    response = client_with_db.delete(f"/api/queue/test_client/{other_item.id}")

    # Assert - Should fail or return 404
    assert response.status_code in [403, 404]

    # Verify other_client's item is still there
    other_queue = queue_repo.get_by_client("other_client")
    assert len(other_queue) == 1


# POST /api/queue/{client_id}/clear - Clear queue
def test_clear_queue_removes_all_items(client_with_db, db_session, sample_data):
    """Test that POST /api/queue/{client_id}/clear removes all items.

    RED phase: Endpoint doesn't exist yet.
    """
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][1].id)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][2].id)

    # Act
    response = client_with_db.post("/api/queue/test_client/clear")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["removed"] == 3

    # Verify queue is empty
    queue = queue_repo.get_by_client("test_client")
    assert len(queue) == 0


def test_clear_queue_returns_zero_for_empty_queue(client_with_db, sample_data):
    """Test that clearing empty queue returns 0 removed."""
    # Act
    response = client_with_db.post("/api/queue/test_client/clear")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["removed"] == 0


def test_clear_queue_only_affects_specified_client(client_with_db, db_session, sample_data):
    """Test that clear only removes items for the specified client."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="other_client", friendly_name="Other", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    queue_repo.add(client_id="other_client", video_id=sample_data["videos"][1].id)

    # Act
    response = client_with_db.post("/api/queue/test_client/clear")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["removed"] == 1

    # Verify other_client's queue is intact
    other_queue = queue_repo.get_by_client("other_client")
    assert len(other_queue) == 1


# PUT /api/queue/{client_id}/reorder - Reorder queue
def test_reorder_queue_updates_positions(client_with_db, db_session, sample_data):
    """Test that PUT /api/queue/{client_id}/reorder updates positions.

    RED phase: Endpoint doesn't exist yet.
    """
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    item1 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    item2 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][1].id)
    item3 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][2].id)

    # Act - Reverse order
    request_data = {
        "queue_ids": [item3.id, item2.id, item1.id]
    }
    response = client_with_db.put("/api/queue/test_client/reorder", json=request_data)

    # Assert
    assert response.status_code == 200

    # Verify new order
    queue = queue_repo.get_by_client("test_client")
    assert queue[0].id == item3.id
    assert queue[1].id == item2.id
    assert queue[2].id == item1.id


def test_reorder_queue_requires_queue_ids(client_with_db, sample_data):
    """Test that queue_ids field is required."""
    # Arrange
    request_data = {}  # Missing queue_ids

    # Act
    response = client_with_db.put("/api/queue/test_client/reorder", json=request_data)

    # Assert
    assert response.status_code == 422  # Validation error


def test_reorder_queue_validates_all_ids_exist(client_with_db, db_session, sample_data):
    """Test that reorder validates all queue IDs exist."""
    from src.db.repositories import QueueRepository

    # Arrange
    queue_repo = QueueRepository(db_session)
    item1 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)

    # Act - Include non-existent ID
    request_data = {
        "queue_ids": [item1.id, 99999]
    }
    response = client_with_db.put("/api/queue/test_client/reorder", json=request_data)

    # Assert - Should fail
    assert response.status_code in [400, 404]


def test_reorder_queue_only_reorders_for_specified_client(client_with_db, db_session, sample_data):
    """Test that reorder only affects items for the specified client."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="other_client", friendly_name="Other", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    test_item1 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][0].id)
    test_item2 = queue_repo.add(client_id="test_client", video_id=sample_data["videos"][1].id)
    other_item = queue_repo.add(client_id="other_client", video_id=sample_data["videos"][2].id)

    # Act - Try to include other client's item
    request_data = {
        "queue_ids": [test_item2.id, test_item1.id, other_item.id]
    }
    response = client_with_db.put("/api/queue/test_client/reorder", json=request_data)

    # Assert - Should fail or ignore other client's item
    assert response.status_code in [200, 400, 403, 404]

    if response.status_code == 200:
        # If it succeeds, verify it only reordered test_client's items
        queue = queue_repo.get_by_client("test_client")
        assert len(queue) == 2
        assert queue[0].id == test_item2.id
        assert queue[1].id == test_item1.id


# Edge cases
def test_queue_endpoints_handle_nonexistent_client(client_with_db):
    """Test that queue endpoints handle non-existent client gracefully."""
    # GET /api/queue/{nonexistent}
    response = client_with_db.get("/api/queue/nonexistent_client")
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        # Should return empty list
        assert response.json() == []


def test_add_to_queue_with_empty_video_ids_list(client_with_db, sample_data):
    """Test that adding empty video_ids list returns appropriate error."""
    # Arrange
    request_data = {
        "video_ids": []
    }

    # Act
    response = client_with_db.post("/api/queue/test_client", json=request_data)

    # Assert
    assert response.status_code in [200, 400, 422]

    if response.status_code == 200:
        data = response.json()
        assert data["added"] == 0
