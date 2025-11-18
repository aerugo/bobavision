"""Database setup and connection management.

GREEN phase: Implement database connection to pass tests.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


def get_database_url() -> str:
    """Get database URL from environment or use default.

    Returns:
        Database URL string
    """
    # Allow override via environment variable for testing/production
    return os.getenv("DATABASE_URL", "sqlite:///./bobavision.db")


# Create database engine
# For SQLite, we use check_same_thread=False to allow usage across threads
# This is safe for our use case with FastAPI
DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database by creating all tables.

    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session dependency for FastAPI.

    Yields:
        Database session

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
