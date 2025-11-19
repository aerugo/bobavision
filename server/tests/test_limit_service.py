"""Tests for limit service.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import date, datetime, timedelta
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
def setup_client(db_session):
    """Setup a test client with videos."""
    from src.db.repositories import ClientRepository, VideoRepository
    from src.db.models import Video

    # Create client
    client_repo = ClientRepository(db_session)
    client_repo.create(client_id="test_client", friendly_name="Test", daily_limit=3)

    # Create videos
    video_repo = VideoRepository(db_session)
    video_repo.create(path="video1.mp4", title="Video 1")
    video_repo.create(path="video2.mp4", title="Video 2")

    return db_session


def test_limit_service_is_limit_reached_false_when_under_limit(setup_client):
    """Test that is_limit_reached returns False when under limit.

    RED phase: LimitService doesn't exist yet.
    """
    from src.services.limit_service import LimitService

    # Arrange
    service = LimitService(setup_client)
    today = date.today()

    # Client has limit of 3, but has played 0 videos
    # Act
    is_reached = service.is_limit_reached("test_client", today)

    # Assert
    assert is_reached is False


def test_limit_service_is_limit_reached_false_at_limit_minus_one(setup_client):
    """Test that limit is not reached at N-1 plays."""
    from src.services.limit_service import LimitService
    from src.db.repositories import PlayLogRepository, VideoRepository

    # Arrange
    service = LimitService(setup_client)
    play_repo = PlayLogRepository(setup_client)
    video_repo = VideoRepository(setup_client)

    videos = video_repo.get_all()
    today = date.today()

    # Log 2 plays (limit is 3, so 2 is under)
    play_repo.log_play("test_client", videos[0].id)
    play_repo.log_play("test_client", videos[1].id)

    # Act
    is_reached = service.is_limit_reached("test_client", today)

    # Assert
    assert is_reached is False


def test_limit_service_is_limit_reached_true_at_exact_limit(setup_client):
    """Test that limit is reached at exactly N plays."""
    from src.services.limit_service import LimitService
    from src.db.repositories import PlayLogRepository, VideoRepository

    # Arrange
    service = LimitService(setup_client)
    play_repo = PlayLogRepository(setup_client)
    video_repo = VideoRepository(setup_client)

    videos = video_repo.get_all()
    today = date.today()

    # Log 3 plays (exactly at limit)
    for i in range(3):
        play_repo.log_play("test_client", videos[i % 2].id)

    # Act
    is_reached = service.is_limit_reached("test_client", today)

    # Assert
    assert is_reached is True


def test_limit_service_is_limit_reached_true_beyond_limit(setup_client):
    """Test that limit is reached beyond N plays."""
    from src.services.limit_service import LimitService
    from src.db.repositories import PlayLogRepository, VideoRepository

    # Arrange
    service = LimitService(setup_client)
    play_repo = PlayLogRepository(setup_client)
    video_repo = VideoRepository(setup_client)

    videos = video_repo.get_all()
    today = date.today()

    # Log 5 plays (beyond limit of 3)
    for i in range(5):
        play_repo.log_play("test_client", videos[i % 2].id)

    # Act
    is_reached = service.is_limit_reached("test_client", today)

    # Assert
    assert is_reached is True




def test_limit_service_get_daily_limit_returns_client_limit(setup_client):
    """Test getting client's configured daily limit."""
    from src.services.limit_service import LimitService

    # Arrange
    service = LimitService(setup_client)

    # Act
    limit = service.get_daily_limit("test_client")

    # Assert
    assert limit == 3  # Client was created with limit of 3


def test_limit_service_get_daily_limit_returns_default_for_new_client(db_session):
    """Test that new clients get default limit."""
    from src.services.limit_service import LimitService

    # Arrange
    service = LimitService(db_session)

    # Act - Client doesn't exist, should get default
    limit = service.get_daily_limit("nonexistent_client")

    # Assert
    assert limit == 3  # Default limit


def test_limit_service_count_plays_today_returns_correct_count(setup_client):
    """Test counting plays for today."""
    from src.services.limit_service import LimitService
    from src.db.repositories import PlayLogRepository, VideoRepository

    # Arrange
    service = LimitService(setup_client)
    play_repo = PlayLogRepository(setup_client)
    video_repo = VideoRepository(setup_client)

    videos = video_repo.get_all()
    today = date.today()

    # Log 3 plays
    for i in range(3):
        play_repo.log_play("test_client", videos[i % 2].id)

    # Act
    count = service.count_plays_today("test_client", today)

    # Assert
    assert count == 3


def test_limit_service_excludes_previous_days(setup_client):
    """Test that plays from previous days don't count."""
    from src.services.limit_service import LimitService
    from src.db.repositories import PlayLogRepository, VideoRepository
    from src.db.models import PlayLog

    # Arrange
    service = LimitService(setup_client)
    video_repo = VideoRepository(setup_client)

    videos = video_repo.get_all()
    today = date.today()

    # Create play from yesterday
    yesterday = datetime.now() - timedelta(days=1)
    old_play = PlayLog(
        client_id="test_client",
        video_id=videos[0].id,
        played_at=yesterday
    )
    setup_client.add(old_play)
    setup_client.commit()

    # Act
    count = service.count_plays_today("test_client", today)

    # Assert - Should not count yesterday's play
    assert count == 0


def test_limit_service_different_clients_independent_limits(db_session):
    """Test that different clients have independent limits."""
    from src.services.limit_service import LimitService
    from src.db.repositories import ClientRepository, VideoRepository, PlayLogRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    video_repo = VideoRepository(db_session)
    play_repo = PlayLogRepository(db_session)

    # Create two clients with different limits
    client_repo.create(client_id="client1", friendly_name="Client 1", daily_limit=2)
    client_repo.create(client_id="client2", friendly_name="Client 2", daily_limit=5)

    video = video_repo.create(path="video.mp4", title="Video")
    today = date.today()

    # Client 1 plays 2 videos (at limit)
    for _ in range(2):
        play_repo.log_play("client1", video.id)

    # Client 2 plays 2 videos (under limit)
    for _ in range(2):
        play_repo.log_play("client2", video.id)

    service = LimitService(db_session)

    # Act
    client1_reached = service.is_limit_reached("client1", today)
    client2_reached = service.is_limit_reached("client2", today)

    # Assert
    assert client1_reached is True  # At limit of 2
    assert client2_reached is False  # Under limit of 5


def test_limit_service_custom_client_limit(db_session):
    """Test client with custom (non-default) limit."""
    from src.services.limit_service import LimitService
    from src.db.repositories import ClientRepository, VideoRepository, PlayLogRepository

    # Arrange
    client_repo = ClientRepository(db_session)
    video_repo = VideoRepository(db_session)
    play_repo = PlayLogRepository(db_session)

    # Create client with limit of 10
    client_repo.create(client_id="power_user", friendly_name="Power User", daily_limit=10)
    video = video_repo.create(path="video.mp4", title="Video")
    today = date.today()

    # Play 9 videos
    for _ in range(9):
        play_repo.log_play("power_user", video.id)

    service = LimitService(db_session)

    # Act
    is_reached = service.is_limit_reached("power_user", today)

    # Assert - Should not be reached (9 < 10)
    assert is_reached is False
