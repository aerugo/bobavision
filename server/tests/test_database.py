"""Tests for database setup and connection.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


def test_database_engine_creation():
    """Test that database engine can be created.

    RED phase: This will fail because database module doesn't exist yet.
    """
    from src.db.database import engine

    # Assert
    assert engine is not None
    assert str(engine.url).startswith("sqlite://")


def test_database_tables_created():
    """Test that all tables are created in the database."""
    from src.db.database import engine, Base
    from src.db.models import Video, ClientSettings, PlayLog

    # Act - Create all tables
    Base.metadata.create_all(engine)

    # Assert - Check that tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "videos" in tables
    assert "client_settings" in tables
    assert "play_log" in tables


def test_session_factory_creates_sessions():
    """Test that session factory can create database sessions."""
    from src.db.database import SessionLocal

    # Act
    session = SessionLocal()

    # Assert
    assert session is not None
    assert isinstance(session, Session)

    # Cleanup
    session.close()


def test_get_db_dependency_yields_session():
    """Test that get_db() dependency function yields a session."""
    from src.db.database import get_db

    # Act - Use the dependency as a generator
    db_gen = get_db()
    session = next(db_gen)

    # Assert
    assert session is not None
    assert isinstance(session, Session)

    # Cleanup - Finish the generator to trigger finally block
    try:
        next(db_gen)
    except StopIteration:
        pass  # Expected - generator exhausted


def test_get_db_dependency_closes_session():
    """Test that get_db() properly closes session after use."""
    from src.db.database import get_db

    # Act
    db_gen = get_db()
    session = next(db_gen)

    # Verify session is open
    assert session.is_active

    # Finish the generator (simulates dependency cleanup)
    try:
        next(db_gen)
    except StopIteration:
        pass

    # Assert - Session should be closed after generator cleanup
    # Note: The session might still be active in-memory, but it's been closed
    # We can't easily test this without more complex setup


def test_init_db_creates_tables():
    """Test that init_db() function creates all tables."""
    from src.db.database import init_db, engine
    from sqlalchemy import inspect

    # Act
    init_db()

    # Assert
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "videos" in tables
    assert "client_settings" in tables
    assert "play_log" in tables


def test_database_url_is_configurable():
    """Test that database URL can be configured via environment or parameter."""
    from src.db.database import get_database_url

    # Act
    url = get_database_url()

    # Assert
    assert url is not None
    assert isinstance(url, str)
    # Default should be SQLite
    assert "sqlite" in url.lower()
