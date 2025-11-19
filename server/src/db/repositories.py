"""Repository classes for database operations.

GREEN phase: Implement repositories to pass tests.

Repositories provide a data access layer, separating business logic from database queries.
"""
import random
from datetime import date, datetime, time
from typing import List, Optional
from sqlalchemy.orm import Session

from src.db.models import Video, ClientSettings, PlayLog


class VideoRepository:
    """Repository for Video model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_all(self) -> List[Video]:
        """Get all videos.

        Returns:
            List of all Video objects
        """
        return self.db.query(Video).all()

    def get_by_id(self, video_id: int) -> Optional[Video]:
        """Get video by ID.

        Args:
            video_id: Video ID

        Returns:
            Video object or None if not found
        """
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_by_path(self, path: str) -> Optional[Video]:
        """Get video by file path.

        Args:
            path: Video file path

        Returns:
            Video object or None if not found
        """
        return self.db.query(Video).filter(Video.path == path).first()

    def create(
        self,
        path: str,
        title: str,
        tags: Optional[str] = None,
        is_placeholder: bool = False,
        duration_seconds: Optional[int] = None
    ) -> Video:
        """Create a new video.

        Args:
            path: Video file path
            title: Video title
            tags: Comma-separated tags
            is_placeholder: Whether this is a placeholder video
            duration_seconds: Video duration in seconds

        Returns:
            Created Video object
        """
        video = Video(
            path=path,
            title=title,
            tags=tags,
            is_placeholder=is_placeholder,
            duration_seconds=duration_seconds
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def delete(self, video_id: int) -> bool:
        """Delete a video by ID.

        Args:
            video_id: Video ID to delete

        Returns:
            True if video was deleted, False if not found
        """
        video = self.get_by_id(video_id)
        if not video:
            return False

        self.db.delete(video)
        self.db.commit()
        return True

    def get_non_placeholders(self) -> List[Video]:
        """Get all non-placeholder videos.

        Returns:
            List of non-placeholder Video objects
        """
        return self.db.query(Video).filter(Video.is_placeholder == False).all()

    def get_placeholders(self) -> List[Video]:
        """Get all placeholder videos.

        Returns:
            List of placeholder Video objects
        """
        return self.db.query(Video).filter(Video.is_placeholder == True).all()

    def get_random_non_placeholder(self) -> Optional[Video]:
        """Get a random non-placeholder video.

        Returns:
            Random non-placeholder Video object or None if none exist
        """
        videos = self.get_non_placeholders()
        if not videos:
            return None
        return random.choice(videos)

    def get_random_placeholder(self) -> Optional[Video]:
        """Get a random placeholder video.

        Returns:
            Random placeholder Video object or None if none exist
        """
        videos = self.get_placeholders()
        if not videos:
            return None
        return random.choice(videos)


class ClientRepository:
    """Repository for ClientSettings model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_all(self) -> List[ClientSettings]:
        """Get all clients.

        Returns:
            List of all ClientSettings objects
        """
        return self.db.query(ClientSettings).all()

    def get_by_id(self, client_id: str) -> Optional[ClientSettings]:
        """Get client by ID.

        Args:
            client_id: Client identifier

        Returns:
            ClientSettings object or None if not found
        """
        return self.db.query(ClientSettings).filter(
            ClientSettings.client_id == client_id
        ).first()

    def create(
        self,
        client_id: str,
        friendly_name: str,
        daily_limit: int = 3,
        tag_filters: Optional[str] = None
    ) -> ClientSettings:
        """Create a new client.

        Args:
            client_id: Client identifier
            friendly_name: Human-readable name
            daily_limit: Daily video limit
            tag_filters: Comma-separated tag filters

        Returns:
            Created ClientSettings object
        """
        client = ClientSettings(
            client_id=client_id,
            friendly_name=friendly_name,
            daily_limit=daily_limit,
            tag_filters=tag_filters
        )
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_or_create(
        self,
        client_id: str,
        friendly_name: str = None,
        daily_limit: int = 3
    ) -> ClientSettings:
        """Get existing client or create new one.

        Args:
            client_id: Client identifier
            friendly_name: Human-readable name (only used if creating)
            daily_limit: Daily video limit (only used if creating)

        Returns:
            ClientSettings object (existing or new)
        """
        client = self.get_by_id(client_id)
        if client:
            return client

        # Create new client
        if friendly_name is None:
            friendly_name = f"Client {client_id}"

        return self.create(
            client_id=client_id,
            friendly_name=friendly_name,
            daily_limit=daily_limit
        )

    def update(
        self,
        client_id: str,
        friendly_name: Optional[str] = None,
        daily_limit: Optional[int] = None,
        tag_filters: Optional[str] = None
    ) -> Optional[ClientSettings]:
        """Update client settings.

        Args:
            client_id: Client identifier
            friendly_name: New friendly name (if provided)
            daily_limit: New daily limit (if provided)
            tag_filters: New tag filters (if provided)

        Returns:
            Updated ClientSettings object or None if not found
        """
        client = self.get_by_id(client_id)
        if not client:
            return None

        if friendly_name is not None:
            client.friendly_name = friendly_name
        if daily_limit is not None:
            client.daily_limit = daily_limit
        if tag_filters is not None:
            client.tag_filters = tag_filters

        self.db.commit()
        self.db.refresh(client)
        return client


class PlayLogRepository:
    """Repository for PlayLog model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def log_play(
        self,
        client_id: str,
        video_id: int,
        is_placeholder: bool,
        completed: bool = False
    ) -> PlayLog:
        """Log a video play.

        Args:
            client_id: Client identifier
            video_id: Video ID
            is_placeholder: Whether the video is a placeholder
            completed: Whether the video was completed

        Returns:
            Created PlayLog object
        """
        play = PlayLog(
            client_id=client_id,
            video_id=video_id,
            is_placeholder=is_placeholder,
            completed=completed
        )
        self.db.add(play)
        self.db.commit()
        self.db.refresh(play)
        return play

    def count_plays_today(self, client_id: str, today: date) -> int:
        """Count all plays for a client today.

        Args:
            client_id: Client identifier
            today: Date to count plays for

        Returns:
            Number of plays today
        """
        start_of_day = datetime.combine(today, time.min)
        end_of_day = datetime.combine(today, time.max)

        return self.db.query(PlayLog).filter(
            PlayLog.client_id == client_id,
            PlayLog.played_at >= start_of_day,
            PlayLog.played_at <= end_of_day
        ).count()

    def count_non_placeholder_plays_today(self, client_id: str, today: date) -> int:
        """Count non-placeholder plays for a client today.

        Args:
            client_id: Client identifier
            today: Date to count plays for

        Returns:
            Number of non-placeholder plays today
        """
        start_of_day = datetime.combine(today, time.min)
        end_of_day = datetime.combine(today, time.max)

        return self.db.query(PlayLog).filter(
            PlayLog.client_id == client_id,
            PlayLog.is_placeholder == False,
            PlayLog.played_at >= start_of_day,
            PlayLog.played_at <= end_of_day
        ).count()

    def get_recent_plays(self, client_id: str, limit: int = 10) -> List[PlayLog]:
        """Get recent plays for a client.

        Args:
            client_id: Client identifier
            limit: Maximum number of plays to return

        Returns:
            List of recent PlayLog objects (most recent first)
        """
        return self.db.query(PlayLog).filter(
            PlayLog.client_id == client_id
        ).order_by(PlayLog.played_at.desc()).limit(limit).all()


class QueueRepository:
    """Repository for Queue model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_client(self, client_id: str) -> List['Queue']:
        """Get all queue items for a client, sorted by position.

        Args:
            client_id: Client identifier

        Returns:
            List of Queue objects sorted by position
        """
        from src.db.models import Queue

        return self.db.query(Queue).filter(
            Queue.client_id == client_id
        ).order_by(Queue.position).all()

    def add(
        self,
        client_id: str,
        video_id: int,
        position: Optional[int] = None
    ) -> 'Queue':
        """Add a video to client's queue.

        Args:
            client_id: Client identifier
            video_id: Video ID to add
            position: Position in queue (auto-calculated if not provided)

        Returns:
            Created Queue object
        """
        from src.db.models import Queue

        # If position not provided, add to end of queue
        if position is None:
            max_pos = self.db.query(Queue).filter(
                Queue.client_id == client_id
            ).count()
            position = max_pos + 1

        queue_item = Queue(
            client_id=client_id,
            video_id=video_id,
            position=position
        )
        self.db.add(queue_item)
        self.db.commit()
        self.db.refresh(queue_item)
        return queue_item

    def get_next(self, client_id: str) -> Optional['Queue']:
        """Get the next video in queue (first item by position).

        Args:
            client_id: Client identifier

        Returns:
            Queue object or None if queue is empty
        """
        from src.db.models import Queue

        return self.db.query(Queue).filter(
            Queue.client_id == client_id
        ).order_by(Queue.position).first()

    def remove(self, queue_id: int) -> None:
        """Remove a queue item by ID.

        Args:
            queue_id: Queue item ID to remove
        """
        from src.db.models import Queue

        queue_item = self.db.query(Queue).filter(
            Queue.id == queue_id
        ).first()

        if queue_item:
            self.db.delete(queue_item)
            self.db.commit()

    def clear(self, client_id: str) -> None:
        """Remove all queue items for a client.

        Args:
            client_id: Client identifier
        """
        from src.db.models import Queue

        self.db.query(Queue).filter(
            Queue.client_id == client_id
        ).delete()
        self.db.commit()

    def reorder(self, client_id: str, queue_ids: List[int]) -> None:
        """Reorder queue items based on provided ID list.

        Args:
            client_id: Client identifier
            queue_ids: List of queue item IDs in new order
        """
        from src.db.models import Queue

        # Update position for each item
        for new_position, queue_id in enumerate(queue_ids, start=1):
            queue_item = self.db.query(Queue).filter(
                Queue.id == queue_id,
                Queue.client_id == client_id
            ).first()

            if queue_item:
                queue_item.position = new_position

        self.db.commit()

    def pop(self, client_id: str) -> Optional['Queue']:
        """Remove and return the first item in queue.

        Args:
            client_id: Client identifier

        Returns:
            Removed Queue object or None if queue is empty
        """
        from src.db.models import Queue

        # Get first item
        queue_item = self.db.query(Queue).filter(
            Queue.client_id == client_id
        ).order_by(Queue.position).first()

        if queue_item:
            # Store data before deletion
            item_data = queue_item
            self.db.delete(queue_item)
            self.db.commit()
            return item_data

        return None

    def count(self, client_id: str) -> int:
        """Count number of items in client's queue.

        Args:
            client_id: Client identifier

        Returns:
            Number of queue items
        """
        from src.db.models import Queue

        return self.db.query(Queue).filter(
            Queue.client_id == client_id
        ).count()
