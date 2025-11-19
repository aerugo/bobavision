"""Shared test fixtures for all tests.

Provides common setup like test client, mock data, etc.
"""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def sample_videos(tmp_path):
    """Create sample video files for testing.

    Returns:
        Path: Directory containing sample video files
    """
    # Create test video files
    (tmp_path / "video1.mp4").write_text("fake video content 1")
    (tmp_path / "video2.mp4").write_text("fake video content 2")
    (tmp_path / "video3.mp4").write_text("fake video content 3")

    return tmp_path


@pytest.fixture
def empty_media_dir(tmp_path):
    """Create empty media directory.

    Returns:
        Path: Empty directory
    """
    return tmp_path


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing.

    Uses a shared in-memory database that persists across connections.
    This is required for FastAPI TestClient which uses multiple threads.

    Returns:
        Session: SQLAlchemy database session
    """
    # Import all models to ensure they're registered with Base
    from src.db.models import Base, Video, ClientSettings, PlayLog, Queue
    from sqlalchemy import event

    # Use a shared in-memory database that persists across connections
    # The "file::memory:?cache=shared" URI creates a shared in-memory database
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # Use StaticPool to keep single connection
    )

    # Enable foreign key constraints for SQLite (required for CASCADE deletes)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()
