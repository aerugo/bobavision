"""Tests for repository classes.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import datetime, date, timedelta
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
def sample_videos(db_session):
    """Create sample videos in database."""
    from src.db.models import Video

    videos = [
        Video(path="cartoon/video1.mp4", title="Fun Cartoon 1", is_placeholder=False),
        Video(path="cartoon/video2.mp4", title="Fun Cartoon 2", is_placeholder=False),
        Video(path="educational/video3.mp4", title="Learning Time", is_placeholder=False),
        Video(path="placeholders/all_done.mp4", title="All Done for Today", is_placeholder=True),
    ]

    for video in videos:
        db_session.add(video)
    db_session.commit()

    return videos


# ===== VideoRepository Tests =====

def test_video_repository_get_all(db_session, sample_videos):
    """Test getting all videos from repository.

    RED phase: VideoRepository doesn't exist yet.
    """
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    videos = repo.get_all()

    # Assert
    assert len(videos) == 4
    assert all(hasattr(v, 'title') for v in videos)


def test_video_repository_get_by_id(db_session, sample_videos):
    """Test getting video by ID."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)
    video_id = sample_videos[0].id

    # Act
    video = repo.get_by_id(video_id)

    # Assert
    assert video is not None
    assert video.id == video_id
    assert video.title == "Fun Cartoon 1"


def test_video_repository_get_by_id_not_found(db_session):
    """Test getting non-existent video returns None."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.get_by_id(9999)

    # Assert
    assert video is None


def test_video_repository_get_by_path(db_session, sample_videos):
    """Test getting video by path."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.get_by_path("cartoon/video1.mp4")

    # Assert
    assert video is not None
    assert video.path == "cartoon/video1.mp4"


def test_video_repository_create(db_session):
    """Test creating a new video."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.create(
        path="new/video.mp4",
        title="New Video",
        tags="kids,fun",
        is_placeholder=False
    )

    # Assert
    assert video.id is not None
    assert video.path == "new/video.mp4"
    assert video.title == "New Video"
    assert video.tags == "kids,fun"


def test_video_repository_get_non_placeholders(db_session, sample_videos):
    """Test getting only non-placeholder videos."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    videos = repo.get_non_placeholders()

    # Assert
    assert len(videos) == 3  # Should exclude the placeholder
    assert all(not v.is_placeholder for v in videos)


def test_video_repository_get_placeholders(db_session, sample_videos):
    """Test getting only placeholder videos."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    videos = repo.get_placeholders()

    # Assert
    assert len(videos) == 1
    assert all(v.is_placeholder for v in videos)
    assert videos[0].title == "All Done for Today"


def test_video_repository_get_random_non_placeholder(db_session, sample_videos):
    """Test getting a random non-placeholder video."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.get_random_non_placeholder()

    # Assert
    assert video is not None
    assert video.is_placeholder is False
    assert video.title in ["Fun Cartoon 1", "Fun Cartoon 2", "Learning Time"]


def test_video_repository_get_random_placeholder(db_session, sample_videos):
    """Test getting a random placeholder video."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.get_random_placeholder()

    # Assert
    assert video is not None
    assert video.is_placeholder is True


def test_video_repository_get_random_non_placeholder_empty(db_session):
    """Test getting random video when none exist returns None."""
    from src.db.repositories import VideoRepository

    # Arrange
    repo = VideoRepository(db_session)

    # Act
    video = repo.get_random_non_placeholder()

    # Assert
    assert video is None


# ===== ClientRepository Tests =====

def test_client_repository_get_by_id(db_session):
    """Test getting client by ID."""
    from src.db.repositories import ClientRepository
    from src.db.models import ClientSettings

    # Arrange
    client = ClientSettings(client_id="trolley1", friendly_name="Trolley 1")
    db_session.add(client)
    db_session.commit()

    repo = ClientRepository(db_session)

    # Act
    result = repo.get_by_id("trolley1")

    # Assert
    assert result is not None
    assert result.client_id == "trolley1"
    assert result.friendly_name == "Trolley 1"


def test_client_repository_get_by_id_not_found(db_session):
    """Test getting non-existent client returns None."""
    from src.db.repositories import ClientRepository

    # Arrange
    repo = ClientRepository(db_session)

    # Act
    result = repo.get_by_id("nonexistent")

    # Assert
    assert result is None


def test_client_repository_create(db_session):
    """Test creating a new client."""
    from src.db.repositories import ClientRepository

    # Arrange
    repo = ClientRepository(db_session)

    # Act
    client = repo.create(
        client_id="new_client",
        friendly_name="New Client",
        daily_limit=5
    )

    # Assert
    assert client.client_id == "new_client"
    assert client.friendly_name == "New Client"
    assert client.daily_limit == 5


def test_client_repository_get_or_create_existing(db_session):
    """Test get_or_create with existing client."""
    from src.db.repositories import ClientRepository
    from src.db.models import ClientSettings

    # Arrange
    existing = ClientSettings(client_id="existing", friendly_name="Existing")
    db_session.add(existing)
    db_session.commit()

    repo = ClientRepository(db_session)

    # Act
    client = repo.get_or_create("existing", friendly_name="Should Not Change")

    # Assert
    assert client.client_id == "existing"
    assert client.friendly_name == "Existing"  # Should keep original


def test_client_repository_get_or_create_new(db_session):
    """Test get_or_create with new client."""
    from src.db.repositories import ClientRepository

    # Arrange
    repo = ClientRepository(db_session)

    # Act
    client = repo.get_or_create("new", friendly_name="New Client")

    # Assert
    assert client.client_id == "new"
    assert client.friendly_name == "New Client"
    assert client.daily_limit == 3  # Default


def test_client_repository_update(db_session):
    """Test updating client settings."""
    from src.db.repositories import ClientRepository
    from src.db.models import ClientSettings

    # Arrange
    client = ClientSettings(client_id="test", friendly_name="Test", daily_limit=3)
    db_session.add(client)
    db_session.commit()

    repo = ClientRepository(db_session)

    # Act
    updated = repo.update("test", daily_limit=5, friendly_name="Updated")

    # Assert
    assert updated.daily_limit == 5
    assert updated.friendly_name == "Updated"


# ===== PlayLogRepository Tests =====

def test_playlog_repository_log_play(db_session, sample_videos):
    """Test logging a play."""
    from src.db.repositories import PlayLogRepository, ClientRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test")

    repo = PlayLogRepository(db_session)

    # Act
    play = repo.log_play(
        client_id="test",
        video_id=sample_videos[0].id,
        is_placeholder=False
    )

    # Assert
    assert play.id is not None
    assert play.client_id == "test"
    assert play.video_id == sample_videos[0].id
    assert play.is_placeholder is False


def test_playlog_repository_count_plays_today(db_session, sample_videos):
    """Test counting plays for today."""
    from src.db.repositories import PlayLogRepository, ClientRepository
    from src.db.models import PlayLog

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test")

    # Create some plays for today
    today = datetime.utcnow()
    for i in range(3):
        play = PlayLog(
            client_id="test",
            video_id=sample_videos[i].id,
            is_placeholder=False,
            played_at=today
        )
        db_session.add(play)
    db_session.commit()

    repo = PlayLogRepository(db_session)

    # Act
    count = repo.count_plays_today("test", date.today())

    # Assert
    assert count == 3


def test_playlog_repository_count_non_placeholder_plays_today(db_session, sample_videos):
    """Test counting only non-placeholder plays for today."""
    from src.db.repositories import PlayLogRepository, ClientRepository
    from src.db.models import PlayLog

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test")

    # Create 2 real plays and 1 placeholder
    today = datetime.utcnow()
    plays = [
        PlayLog(client_id="test", video_id=sample_videos[0].id, is_placeholder=False, played_at=today),
        PlayLog(client_id="test", video_id=sample_videos[1].id, is_placeholder=False, played_at=today),
        PlayLog(client_id="test", video_id=sample_videos[3].id, is_placeholder=True, played_at=today),
    ]
    for play in plays:
        db_session.add(play)
    db_session.commit()

    repo = PlayLogRepository(db_session)

    # Act
    count = repo.count_non_placeholder_plays_today("test", date.today())

    # Assert
    assert count == 2  # Only non-placeholder plays


def test_playlog_repository_excludes_previous_days(db_session, sample_videos):
    """Test that count only includes today's plays."""
    from src.db.repositories import PlayLogRepository, ClientRepository
    from src.db.models import PlayLog

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test")

    # Create play from yesterday
    yesterday = datetime.utcnow() - timedelta(days=1)
    old_play = PlayLog(
        client_id="test",
        video_id=sample_videos[0].id,
        is_placeholder=False,
        played_at=yesterday
    )
    db_session.add(old_play)

    # Create play from today
    today = datetime.utcnow()
    new_play = PlayLog(
        client_id="test",
        video_id=sample_videos[1].id,
        is_placeholder=False,
        played_at=today
    )
    db_session.add(new_play)
    db_session.commit()

    repo = PlayLogRepository(db_session)

    # Act
    count = repo.count_non_placeholder_plays_today("test", date.today())

    # Assert
    assert count == 1  # Only today's play


def test_playlog_repository_get_recent_plays(db_session, sample_videos):
    """Test getting recent plays for a client."""
    from src.db.repositories import PlayLogRepository, ClientRepository
    from src.db.models import PlayLog

    # Arrange
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test", friendly_name="Test")

    # Create multiple plays
    for i in range(5):
        play = PlayLog(
            client_id="test",
            video_id=sample_videos[i % len(sample_videos)].id,
            is_placeholder=False
        )
        db_session.add(play)
    db_session.commit()

    repo = PlayLogRepository(db_session)

    # Act
    recent = repo.get_recent_plays("test", limit=3)

    # Assert
    assert len(recent) == 3
    # Should be ordered by most recent first
    assert recent[0].id > recent[1].id
