"""SQLAlchemy database models.

GREEN phase: Implement models to pass tests.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


# Create declarative base for all models
Base = declarative_base()


class Video(Base):
    """Video model representing a media file in the library."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    tags = Column(String, nullable=True)  # Comma-separated tags
    is_placeholder = Column(Boolean, default=False, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        """String representation of Video."""
        return f"<Video(id={self.id}, title='{self.title}', path='{self.path}')>"


class ClientSettings(Base):
    """Client settings model representing a device's configuration."""

    __tablename__ = "client_settings"

    client_id = Column(String, primary_key=True)
    friendly_name = Column(String, nullable=False)
    daily_limit = Column(Integer, default=3, nullable=False)
    tag_filters = Column(String, nullable=True)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        """String representation of ClientSettings."""
        return f"<ClientSettings(client_id='{self.client_id}', name='{self.friendly_name}')>"


class PlayLog(Base):
    """Play log model tracking video plays per client."""

    __tablename__ = "play_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        String,
        ForeignKey("client_settings.client_id"),
        nullable=False
    )
    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False
    )
    played_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_placeholder = Column(Boolean, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    # Relationships
    video = relationship("Video")

    def __repr__(self):
        """String representation of PlayLog."""
        return f"<PlayLog(id={self.id}, client='{self.client_id}', video_id={self.video_id})>"
