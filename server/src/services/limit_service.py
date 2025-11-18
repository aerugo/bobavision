"""Limit service for daily video limit enforcement.

GREEN phase: Implement limit service to pass tests.

This service encapsulates the business logic for checking if a client
has reached their daily video limit.
"""
from datetime import date
from sqlalchemy.orm import Session

from src.db.repositories import ClientRepository, PlayLogRepository


# Default daily limit for new clients
DEFAULT_DAILY_LIMIT = 3


class LimitService:
    """Service for managing and enforcing daily video limits."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.client_repo = ClientRepository(db)
        self.play_log_repo = PlayLogRepository(db)

    def is_limit_reached(self, client_id: str, today: date) -> bool:
        """Check if client has reached their daily video limit.

        Args:
            client_id: Client identifier
            today: Date to check limit for

        Returns:
            True if limit reached or exceeded, False otherwise
        """
        daily_limit = self.get_daily_limit(client_id)
        plays_today = self.count_plays_today(client_id, today)

        return plays_today >= daily_limit

    def get_daily_limit(self, client_id: str) -> int:
        """Get daily limit for a client.

        Args:
            client_id: Client identifier

        Returns:
            Daily video limit (default if client doesn't exist)
        """
        client = self.client_repo.get_by_id(client_id)

        if client is None:
            return DEFAULT_DAILY_LIMIT

        return client.daily_limit

    def count_plays_today(self, client_id: str, today: date) -> int:
        """Count non-placeholder plays for client today.

        Placeholder plays don't count toward the limit.

        Args:
            client_id: Client identifier
            today: Date to count plays for

        Returns:
            Number of non-placeholder plays today
        """
        return self.play_log_repo.count_non_placeholder_plays_today(
            client_id,
            today
        )
