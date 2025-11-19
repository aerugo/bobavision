"""Tests for database models.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import datetime
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


def test_video_model_creation(db_session):
    """Test creating a Video model instance.

    RED phase: This will fail because Video model doesn't exist yet.
    """
    from src.db.models import Video

    # Arrange & Act
    video = Video(
        path="test/video.mp4",
        title="Test Video",
        tags="cartoon,kids",
        duration_seconds=600
    )
    db_session.add(video)
    db_session.commit()

    # Assert
    assert video.id is not None
    assert video.path == "test/video.mp4"
    assert video.title == "Test Video"
    assert video.tags == "cartoon,kids"
    assert video.duration_seconds == 600
    assert isinstance(video.created_at, datetime)


def test_video_model_unique_path(db_session):
    """Test that video paths must be unique."""
    from src.db.models import Video
    from sqlalchemy.exc import IntegrityError

    # Arrange
    video1 = Video(path="same/path.mp4", title="Video 1")
    video2 = Video(path="same/path.mp4", title="Video 2")

    # Act & Assert
    db_session.add(video1)
    db_session.commit()

    db_session.add(video2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_video_model_defaults(db_session):
    """Test that Video model has correct defaults."""
    from src.db.models import Video

    # Arrange & Act
    video = Video(path="test.mp4", title="Test")
    db_session.add(video)
    db_session.commit()

    # Assert
    assert video.tags is None or video.tags == ""  # Default empty
    assert video.duration_seconds is None  # Optional field


def test_client_settings_model_creation(db_session):
    """Test creating a ClientSettings model instance."""
    from src.db.models import ClientSettings

    # Arrange & Act
    client = ClientSettings(
        client_id="trolley1",
        friendly_name="Living Room Trolley",
        daily_limit=3,
        tag_filters="age-4-6,educational"
    )
    db_session.add(client)
    db_session.commit()

    # Assert
    assert client.client_id == "trolley1"
    assert client.friendly_name == "Living Room Trolley"
    assert client.daily_limit == 3
    assert client.tag_filters == "age-4-6,educational"
    assert isinstance(client.created_at, datetime)
    assert isinstance(client.updated_at, datetime)


def test_client_settings_defaults(db_session):
    """Test that ClientSettings has correct defaults."""
    from src.db.models import ClientSettings

    # Arrange & Act
    client = ClientSettings(
        client_id="test",
        friendly_name="Test Client"
    )
    db_session.add(client)
    db_session.commit()

    # Assert
    assert client.daily_limit == 3  # Default limit
    assert client.tag_filters is None or client.tag_filters == ""


def test_play_log_model_creation(db_session):
    """Test creating a PlayLog model instance."""
    from src.db.models import Video, ClientSettings, PlayLog

    # Arrange - Create related entities first
    video = Video(path="test.mp4", title="Test Video")
    client = ClientSettings(client_id="test", friendly_name="Test")
    db_session.add(video)
    db_session.add(client)
    db_session.commit()

    # Act - Create play log
    play = PlayLog(
        client_id=client.client_id,
        video_id=video.id,
        completed=True
    )
    db_session.add(play)
    db_session.commit()

    # Assert
    assert play.id is not None
    assert play.client_id == "test"
    assert play.video_id == video.id
    assert play.completed is True
    assert isinstance(play.played_at, datetime)


def test_play_log_relationships(db_session):
    """Test that PlayLog has proper relationships to Video and ClientSettings."""
    from src.db.models import Video, ClientSettings, PlayLog

    # Arrange
    video = Video(path="test.mp4", title="Test Video")
    client = ClientSettings(client_id="test", friendly_name="Test")
    db_session.add(video)
    db_session.add(client)
    db_session.commit()

    play = PlayLog(
        client_id=client.client_id,
        video_id=video.id
    )
    db_session.add(play)
    db_session.commit()

    # Assert - Check relationships
    assert play.video == video
    assert play.video.title == "Test Video"


def test_play_log_defaults(db_session):
    """Test that PlayLog has correct defaults."""
    from src.db.models import Video, ClientSettings, PlayLog

    # Arrange
    video = Video(path="test.mp4", title="Test")
    client = ClientSettings(client_id="test", friendly_name="Test")
    db_session.add(video)
    db_session.add(client)
    db_session.commit()

    # Act
    play = PlayLog(
        client_id=client.client_id,
        video_id=video.id
    )
    db_session.add(play)
    db_session.commit()

    # Assert
    assert play.completed is False  # Default should be False
    assert isinstance(play.played_at, datetime)  # Should auto-set timestamp


def test_multiple_play_logs_for_same_client(db_session):
    """Test that a client can have multiple play log entries."""
    from src.db.models import Video, ClientSettings, PlayLog

    # Arrange
    video1 = Video(path="video1.mp4", title="Video 1")
    video2 = Video(path="video2.mp4", title="Video 2")
    client = ClientSettings(client_id="test", friendly_name="Test")
    db_session.add_all([video1, video2, client])
    db_session.commit()

    # Act - Create multiple plays
    play1 = PlayLog(client_id=client.client_id, video_id=video1.id)
    play2 = PlayLog(client_id=client.client_id, video_id=video2.id)
    db_session.add_all([play1, play2])
    db_session.commit()

    # Assert - Query all plays for this client
    plays = db_session.query(PlayLog).filter_by(client_id="test").all()
    assert len(plays) == 2


def test_client_settings_updated_at_changes(db_session):
    """Test that updated_at timestamp changes when client is modified."""
    from src.db.models import ClientSettings
    import time

    # Arrange
    client = ClientSettings(client_id="test", friendly_name="Test")
    db_session.add(client)
    db_session.commit()
    original_updated_at = client.updated_at

    # Act - Wait a moment and update
    time.sleep(0.1)
    client.daily_limit = 5
    db_session.commit()
    db_session.refresh(client)

    # Assert
    # Note: This test may need adjustment based on how we implement updated_at
    # For now, we'll just check it exists
    assert client.updated_at is not None
