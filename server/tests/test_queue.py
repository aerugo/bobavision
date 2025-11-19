"""Tests for Queue model and QueueRepository.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import datetime


def test_queue_model_creation(db_session):
    """Test that Queue model can be created with required fields.

    RED phase: Queue model doesn't exist yet.
    """
    from src.db.models import Queue, Video, ClientSettings

    # Arrange - Create dependencies
    video = Video(path="test.mp4", title="Test Video")
    client = ClientSettings(client_id="test_client", friendly_name="Test Client", daily_limit=3)

    db_session.add(video)
    db_session.add(client)
    db_session.commit()

    # Act - Create queue item
    queue_item = Queue(
        client_id=client.client_id,
        video_id=video.id,
        position=1
    )
    db_session.add(queue_item)
    db_session.commit()

    # Assert
    assert queue_item.id is not None
    assert queue_item.client_id == "test_client"
    assert queue_item.video_id == video.id
    assert queue_item.position == 1
    assert queue_item.created_at is not None
    assert isinstance(queue_item.created_at, datetime)


def test_queue_model_has_video_relationship(db_session):
    """Test that Queue model has relationship to Video."""
    from src.db.models import Queue, Video, ClientSettings

    # Arrange
    video = Video(path="test.mp4", title="Test Video")
    client = ClientSettings(client_id="test_client", friendly_name="Test", daily_limit=3)
    db_session.add_all([video, client])
    db_session.commit()

    # Act
    queue_item = Queue(client_id=client.client_id, video_id=video.id, position=1)
    db_session.add(queue_item)
    db_session.commit()

    # Assert - Can access video through relationship
    assert queue_item.video is not None
    assert queue_item.video.title == "Test Video"


def test_queue_repository_get_by_client(db_session):
    """Test QueueRepository.get_by_client() returns items for specific client.

    RED phase: QueueRepository doesn't exist yet.
    """
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository
    from src.db.models import Queue

    # Arrange - Create test data
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="client1", friendly_name="Client 1", daily_limit=3)
    client_repo.create(client_id="client2", friendly_name="Client 2", daily_limit=3)

    # Create queue items for client1
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="client1", video_id=v1.id, position=1)
    queue_repo.add(client_id="client1", video_id=v2.id, position=2)

    # Create queue item for client2
    queue_repo.add(client_id="client2", video_id=v3.id, position=1)

    # Act
    client1_queue = queue_repo.get_by_client("client1")

    # Assert
    assert len(client1_queue) == 2
    assert client1_queue[0].video_id == v1.id
    assert client1_queue[1].video_id == v2.id


def test_queue_repository_get_by_client_returns_empty_list(db_session):
    """Test QueueRepository.get_by_client() returns empty list for client with no queue."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="empty_client", friendly_name="Empty", daily_limit=3)

    # Act
    queue_repo = QueueRepository(db_session)
    queue = queue_repo.get_by_client("empty_client")

    # Assert
    assert queue == []


def test_queue_repository_get_by_client_returns_sorted_by_position(db_session):
    """Test that queue items are returned sorted by position."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Add queue items out of order
    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test", video_id=v2.id, position=2)
    queue_repo.add(client_id="test", video_id=v3.id, position=3)
    queue_repo.add(client_id="test", video_id=v1.id, position=1)

    # Act
    queue = queue_repo.get_by_client("test")

    # Assert - Should be sorted by position
    assert len(queue) == 3
    assert queue[0].position == 1
    assert queue[1].position == 2
    assert queue[2].position == 3


def test_queue_repository_add_creates_queue_item(db_session):
    """Test QueueRepository.add() creates a new queue item."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    video = video_repo.create(path="test.mp4", title="Test")
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Act
    queue_repo = QueueRepository(db_session)
    queue_item = queue_repo.add(client_id="test", video_id=video.id, position=1)

    # Assert
    assert queue_item.id is not None
    assert queue_item.client_id == "test"
    assert queue_item.video_id == video.id
    assert queue_item.position == 1


def test_queue_repository_add_auto_increments_position(db_session):
    """Test that add() can auto-calculate next position if not provided."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Act - Add items without specifying position
    queue_repo = QueueRepository(db_session)
    item1 = queue_repo.add(client_id="test", video_id=v1.id)
    item2 = queue_repo.add(client_id="test", video_id=v2.id)
    item3 = queue_repo.add(client_id="test", video_id=v3.id)

    # Assert - Positions should auto-increment
    assert item1.position == 1
    assert item2.position == 2
    assert item3.position == 3


def test_queue_repository_get_next_returns_first_item(db_session):
    """Test QueueRepository.get_next() returns first item in queue."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test", video_id=v1.id, position=1)
    queue_repo.add(client_id="test", video_id=v2.id, position=2)

    # Act
    next_item = queue_repo.get_next("test")

    # Assert
    assert next_item is not None
    assert next_item.video_id == v1.id
    assert next_item.position == 1


def test_queue_repository_get_next_returns_none_for_empty_queue(db_session):
    """Test QueueRepository.get_next() returns None when queue is empty."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Act
    queue_repo = QueueRepository(db_session)
    next_item = queue_repo.get_next("test")

    # Assert
    assert next_item is None


def test_queue_repository_remove_deletes_item(db_session):
    """Test QueueRepository.remove() deletes a queue item."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    video = video_repo.create(path="test.mp4", title="Test")
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    item = queue_repo.add(client_id="test", video_id=video.id, position=1)

    # Act
    queue_repo.remove(item.id)

    # Assert
    queue = queue_repo.get_by_client("test")
    assert len(queue) == 0


def test_queue_repository_remove_nonexistent_item_does_nothing(db_session):
    """Test that removing non-existent item doesn't raise error."""
    from src.db.repositories import QueueRepository

    # Act & Assert - Should not raise
    queue_repo = QueueRepository(db_session)
    queue_repo.remove(99999)  # Non-existent ID


def test_queue_repository_clear_removes_all_items_for_client(db_session):
    """Test QueueRepository.clear() removes all queue items for a client."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test", video_id=v1.id)
    queue_repo.add(client_id="test", video_id=v2.id)
    queue_repo.add(client_id="test", video_id=v3.id)

    # Act
    queue_repo.clear("test")

    # Assert
    queue = queue_repo.get_by_client("test")
    assert len(queue) == 0


def test_queue_repository_clear_only_affects_specified_client(db_session):
    """Test that clear() only removes items for the specified client."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")

    client_repo.create(client_id="client1", friendly_name="Client 1", daily_limit=3)
    client_repo.create(client_id="client2", friendly_name="Client 2", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="client1", video_id=v1.id)
    queue_repo.add(client_id="client2", video_id=v2.id)

    # Act
    queue_repo.clear("client1")

    # Assert
    client1_queue = queue_repo.get_by_client("client1")
    client2_queue = queue_repo.get_by_client("client2")

    assert len(client1_queue) == 0
    assert len(client2_queue) == 1


def test_queue_repository_reorder_updates_positions(db_session):
    """Test QueueRepository.reorder() updates queue item positions."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    item1 = queue_repo.add(client_id="test", video_id=v1.id)
    item2 = queue_repo.add(client_id="test", video_id=v2.id)
    item3 = queue_repo.add(client_id="test", video_id=v3.id)

    # Act - Reorder: move item3 to position 1
    new_order = [item3.id, item1.id, item2.id]
    queue_repo.reorder("test", new_order)

    # Assert
    queue = queue_repo.get_by_client("test")
    assert queue[0].id == item3.id
    assert queue[0].position == 1
    assert queue[1].id == item1.id
    assert queue[1].position == 2
    assert queue[2].id == item2.id
    assert queue[2].position == 3


def test_queue_repository_pop_removes_and_returns_first_item(db_session):
    """Test QueueRepository.pop() removes and returns the first queue item."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test", video_id=v1.id)
    queue_repo.add(client_id="test", video_id=v2.id)

    # Act
    popped_item = queue_repo.pop("test")

    # Assert - Should return first item
    assert popped_item is not None
    assert popped_item.video_id == v1.id

    # Verify it was removed from queue
    remaining_queue = queue_repo.get_by_client("test")
    assert len(remaining_queue) == 1
    assert remaining_queue[0].video_id == v2.id


def test_queue_repository_pop_returns_none_for_empty_queue(db_session):
    """Test that pop() returns None when queue is empty."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Act
    queue_repo = QueueRepository(db_session)
    popped_item = queue_repo.pop("test")

    # Assert
    assert popped_item is None


def test_queue_repository_count_returns_queue_size(db_session):
    """Test QueueRepository.count() returns number of items in queue."""
    from src.db.repositories import QueueRepository, VideoRepository, ClientRepository

    # Arrange
    video_repo = VideoRepository(db_session)
    client_repo = ClientRepository(db_session)

    v1 = video_repo.create(path="video1.mp4", title="Video 1")
    v2 = video_repo.create(path="video2.mp4", title="Video 2")
    v3 = video_repo.create(path="video3.mp4", title="Video 3")

    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    queue_repo = QueueRepository(db_session)
    queue_repo.add(client_id="test", video_id=v1.id)
    queue_repo.add(client_id="test", video_id=v2.id)
    queue_repo.add(client_id="test", video_id=v3.id)

    # Act
    count = queue_repo.count("test")

    # Assert
    assert count == 3


def test_queue_repository_count_returns_zero_for_empty_queue(db_session):
    """Test that count() returns 0 for empty queue."""
    from src.db.repositories import QueueRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test", daily_limit=3)

    # Act
    queue_repo = QueueRepository(db_session)
    count = queue_repo.count("test")

    # Assert
    assert count == 0
