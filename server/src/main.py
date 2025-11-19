"""FastAPI application entry point.

Phase 2: Updated with database integration and daily limits.
"""
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from src.db.database import get_db, init_db
from src.db.repositories import VideoRepository, ClientRepository, PlayLogRepository, QueueRepository
from src.services.limit_service import LimitService


# Response model for /api/next endpoint
class NextVideoResponse(BaseModel):
    """Response schema for next video endpoint."""
    url: str
    title: str
    placeholder: bool


# Client management schemas
class ClientResponse(BaseModel):
    """Response schema for client data."""
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    friendly_name: str
    daily_limit: int
    tag_filters: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClientCreate(BaseModel):
    """Request schema for creating a new client."""
    client_id: str = Field(..., min_length=1, description="Unique client identifier")
    friendly_name: str = Field(..., min_length=1, description="Human-readable client name")
    daily_limit: int = Field(default=3, gt=0, description="Daily video limit")
    tag_filters: Optional[str] = Field(default=None, description="Comma-separated tags for filtering")


class ClientUpdate(BaseModel):
    """Request schema for updating a client."""
    friendly_name: Optional[str] = Field(None, min_length=1, description="Human-readable client name")
    daily_limit: Optional[int] = Field(None, gt=0, description="Daily video limit")
    tag_filters: Optional[str] = Field(None, description="Comma-separated tags for filtering")


class BonusPlaysRequest(BaseModel):
    """Request schema for adding bonus plays."""
    count: int = Field(..., gt=0, le=100, description="Number of bonus plays to add (1-100)")


class BonusPlaysResponse(BaseModel):
    """Response schema for bonus plays operation."""
    client_id: str = Field(..., description="Client identifier")
    bonus_plays_count: int = Field(..., description="Total bonus plays for today")
    bonus_plays_date: str = Field(..., description="Date bonus plays apply to (YYYY-MM-DD)")
    new_effective_limit: int = Field(..., description="New effective daily limit including bonus")


# Video management schemas
class VideoResponse(BaseModel):
    """Response schema for video data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    title: str
    tags: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: datetime


class ScanResponse(BaseModel):
    """Response schema for video scan operation."""
    added: int = Field(..., description="Number of videos added to database")
    skipped: int = Field(..., description="Number of videos skipped (already in DB)")
    removed: int = Field(..., description="Number of videos removed from database (no longer in library)")
    total_found: int = Field(..., description="Total video files found")


# Queue management schemas
class QueueItemResponse(BaseModel):
    """Response schema for queue item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    position: int
    created_at: datetime
    video: VideoResponse  # Nested video details


class QueueAddRequest(BaseModel):
    """Request schema for adding videos to queue."""
    video_ids: List[int] = Field(..., min_length=1, description="List of video IDs to add to queue")


class QueueAddResponse(BaseModel):
    """Response schema for add to queue operation."""
    added: int = Field(..., description="Number of videos added")
    total_in_queue: int = Field(..., description="Total items in queue after adding")


class QueueClearResponse(BaseModel):
    """Response schema for clear queue operation."""
    removed: int = Field(..., description="Number of items removed from queue")


class QueueReorderRequest(BaseModel):
    """Request schema for reordering queue."""
    queue_ids: List[int] = Field(..., min_length=1, description="List of queue item IDs in new order")


# Statistics schemas
class SystemStatsResponse(BaseModel):
    """Response schema for system-wide statistics."""
    total_videos: int = Field(..., description="Total number of videos in library")
    total_clients: int = Field(..., description="Total number of registered clients")
    total_plays: int = Field(..., description="Total plays across all clients (all time)")
    plays_today: int = Field(..., description="Total plays today across all clients")


class RecentPlayResponse(BaseModel):
    """Response schema for a recent play in history."""
    model_config = ConfigDict(from_attributes=True)

    video_id: int
    video_title: str
    played_at: datetime


class ClientStatsResponse(BaseModel):
    """Response schema for per-client statistics."""
    client_id: str = Field(..., description="Client identifier")
    friendly_name: str = Field(..., description="Client's friendly name")
    daily_limit: int = Field(..., description="Daily video limit")
    plays_today: int = Field(..., description="Number of non-placeholder plays today")
    plays_remaining: int = Field(..., description="Plays remaining before limit (max 0)")
    total_plays: int = Field(..., description="Total plays all-time")
    queue_size: int = Field(..., description="Current number of items in queue")
    recent_plays: List[RecentPlayResponse] = Field(..., description="Recent play history (up to 10)")


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed (currently none)


# Create FastAPI app
app = FastAPI(
    title="Kids Media Station API",
    description="API for kids single-button media station",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS to allow admin UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files for limit reached animation
static_path = Path(__file__).parent.parent / "static"
if static_path.exists() and static_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Global media directory (can be set for testing)
MEDIA_DIRECTORY = "../media/library"


def set_media_directory(path: str):
    """Set the media directory path and mount for static file serving.

    Args:
        path: Path to media directory
    """
    global MEDIA_DIRECTORY
    MEDIA_DIRECTORY = path

    # Remove existing media mount if present
    app.routes[:] = [
        r for r in app.routes
        if not (hasattr(r, 'path') and '/media/library' in str(getattr(r, 'path', '')))
    ]

    # Mount new directory for static file serving
    media_path = Path(path)
    if media_path.exists() and media_path.is_dir():
        app.mount(
            "/media/library",
            StaticFiles(directory=str(media_path)),
            name="media"
        )


@app.get("/")
def root():
    """Root endpoint - basic API info."""
    return {
        "message": "Kids Media Station API",
        "version": "0.2.0",
        "status": "running"
    }


@app.get("/api/next", response_model=NextVideoResponse)
def get_next_video(
    client_id: str = Query(..., description="Client identifier"),
    db: Session = Depends(get_db)
):
    """Get the next video for a client.

    Phase 3: Queue-first logic - checks queue before limit enforcement.
    - If queue has items, serve from queue (bypasses daily limit)
    - If queue is empty, use limit-based logic (random or placeholder)

    Args:
        client_id: Unique identifier for the client device
        db: Database session (injected)

    Returns:
        NextVideoResponse with video URL, title, and placeholder flag
    """
    # Initialize repositories and services
    video_repo = VideoRepository(db)
    client_repo = ClientRepository(db)
    play_log_repo = PlayLogRepository(db)
    limit_service = LimitService(db)
    queue_repo = QueueRepository(db)

    # Get or create client
    client = client_repo.get_or_create(
        client_id=client_id,
        friendly_name=f"Client {client_id}"
    )

    # PHASE 3: Check queue first
    queue_item = queue_repo.get_next(client_id)

    if queue_item:
        # Queue has items - serve from queue (bypasses limit)
        video = video_repo.get_by_id(queue_item.video_id)

        if video is None:
            # Video in queue doesn't exist - remove queue item and fallback
            queue_repo.remove(queue_item.id)
        else:
            # Remove from queue and serve
            queue_repo.remove(queue_item.id)

            # Log the play (non-blocking - video will be served even if logging fails)
            play_log_repo.log_play_safe(
                client_id=client_id,
                video_id=video.id
            )

            # Build URL path
            url = f"/media/library/{video.path}"

            return NextVideoResponse(
                url=url,
                title=video.title,
                placeholder=False
            )

    # Queue is empty - use limit-based logic
    # Check if daily limit reached
    today = date.today()
    limit_reached = limit_service.is_limit_reached(client_id, today)

    # Select video based on limit status
    if limit_reached:
        # Limit reached - return shader animation
        return NextVideoResponse(
            url="/static/limit_reached.html",
            title="All Done for Today!",
            placeholder=True
        )
    else:
        # Under limit - return random video
        video = video_repo.get_random()

        if video is None:
            # No videos available - return error message
            return NextVideoResponse(
                url="/media/library/none.mp4",
                title="No videos available",
                placeholder=True
            )

        # Log the play (non-blocking - video will be served even if logging fails)
        play_log_repo.log_play_safe(
            client_id=client_id,
            video_id=video.id
        )

        # Build URL path
        url = f"/media/library/{video.path}"

        return NextVideoResponse(
            url=url,
            title=video.title,
            placeholder=False
        )


# Client management endpoints
@app.get("/api/clients", response_model=List[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    """Get all clients.

    Returns:
        List of all registered clients sorted by client_id
    """
    client_repo = ClientRepository(db)
    clients = client_repo.get_all()
    # Sort by client_id for consistent ordering
    return sorted(clients, key=lambda c: c.client_id)


@app.get("/api/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get a specific client by ID.

    Args:
        client_id: Unique client identifier

    Returns:
        Client details

    Raises:
        HTTPException: 404 if client not found
    """
    client_repo = ClientRepository(db)
    client = client_repo.get_by_id(client_id)

    if client is None:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")

    return client


@app.post("/api/clients", response_model=ClientResponse, status_code=201)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client.

    Args:
        client_data: Client creation data

    Returns:
        Created client details

    Raises:
        HTTPException: 409 if client_id already exists
    """
    client_repo = ClientRepository(db)

    # Check if client already exists
    existing_client = client_repo.get_by_id(client_data.client_id)
    if existing_client is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Client '{client_data.client_id}' already exists"
        )

    # Create new client
    client = client_repo.create(
        client_id=client_data.client_id,
        friendly_name=client_data.friendly_name,
        daily_limit=client_data.daily_limit,
        tag_filters=client_data.tag_filters
    )

    return client


@app.patch("/api/clients/{client_id}", response_model=ClientResponse)
@app.put("/api/clients/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing client.

    Supports both PATCH and PUT methods for partial updates.

    Args:
        client_id: Unique client identifier
        client_data: Fields to update

    Returns:
        Updated client details

    Raises:
        HTTPException: 404 if client not found
    """
    client_repo = ClientRepository(db)

    # Check if client exists
    existing_client = client_repo.get_by_id(client_id)
    if existing_client is None:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")

    # Build update dict with only provided fields
    update_data = {}
    if client_data.friendly_name is not None:
        update_data["friendly_name"] = client_data.friendly_name
    if client_data.daily_limit is not None:
        update_data["daily_limit"] = client_data.daily_limit
    if client_data.tag_filters is not None:
        update_data["tag_filters"] = client_data.tag_filters

    # Update client
    updated_client = client_repo.update(client_id, **update_data)

    return updated_client


@app.post("/api/clients/{client_id}/add-bonus-plays", response_model=BonusPlaysResponse)
def add_bonus_plays(
    client_id: str,
    bonus_data: BonusPlaysRequest,
    db: Session = Depends(get_db)
):
    """Add bonus plays to a client for today.

    Bonus plays are extra videos that can be watched today only,
    without affecting the base daily limit for future days.

    Args:
        client_id: Unique client identifier
        bonus_data: Number of bonus plays to add

    Returns:
        Updated bonus plays information

    Raises:
        HTTPException: 404 if client not found
    """
    client_repo = ClientRepository(db)
    limit_service = LimitService(db)

    # Check if client exists
    client = client_repo.get_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")

    # Add bonus plays for today
    today = date.today()
    updated_client = client_repo.add_bonus_plays(
        client_id=client_id,
        bonus_count=bonus_data.count,
        bonus_date=today
    )

    # Get effective limit with bonus
    effective_limit = limit_service.get_effective_daily_limit(client_id, today)

    return BonusPlaysResponse(
        client_id=updated_client.client_id,
        bonus_plays_count=updated_client.bonus_plays_count,
        bonus_plays_date=updated_client.bonus_plays_date.isoformat(),
        new_effective_limit=effective_limit
    )


# Video management endpoints
@app.get("/api/videos", response_model=List[VideoResponse])
def get_videos(
    tags: Optional[str] = Query(None, description="Filter by tags"),
    db: Session = Depends(get_db)
):
    """Get all videos from database.

    Args:
        tags: Optional filter for videos with specific tags
        db: Database session

    Returns:
        List of all videos sorted by title
    """
    video_repo = VideoRepository(db)

    # Get all videos
    videos = video_repo.get_all()

    # Apply filters if provided
    if tags is not None:
        videos = [v for v in videos if v.tags and tags in v.tags]

    # Sort by title for consistent ordering
    return sorted(videos, key=lambda v: v.title)


@app.post("/api/videos/scan", response_model=ScanResponse)
def scan_videos(db: Session = Depends(get_db)):
    """Scan media directory and sync videos with database.

    Adds new videos, skips existing ones, and removes videos that are no longer in the library.

    Returns:
        Scan results with counts of added, skipped, removed, and total files
    """
    from src.media.scanner import VideoScanner

    # Get media directory
    media_dir = Path(MEDIA_DIRECTORY)

    # Check if directory exists
    if not media_dir.exists():
        # If directory doesn't exist, remove all videos from DB
        video_repo = VideoRepository(db)
        all_videos = video_repo.get_all()
        removed = len(all_videos)
        for video in all_videos:
            video_repo.delete(video.id)
        return ScanResponse(added=0, skipped=0, removed=removed, total_found=0)

    # Scan for videos
    scanner = VideoScanner(str(media_dir))
    video_paths = scanner.scan()
    video_paths_set = set(video_paths)

    # Process each video
    video_repo = VideoRepository(db)
    added = 0
    skipped = 0

    for video_path in video_paths:
        # Check if video already exists
        existing = video_repo.get_by_path(video_path)
        if existing is not None:
            skipped += 1
            continue

        # Generate title from filename
        title = _generate_title_from_path(video_path)

        # Extract tags from directory
        tags = _extract_tags_from_path(video_path)

        # Create video record
        video_repo.create(
            path=video_path,
            title=title,
            tags=tags
        )
        added += 1

    # Remove videos from DB that are no longer in the filesystem
    all_videos = video_repo.get_all()
    removed = 0

    for video in all_videos:
        if video.path not in video_paths_set:
            # Video no longer exists in library - remove it
            video_repo.delete(video.id)
            removed += 1

    return ScanResponse(
        added=added,
        skipped=skipped,
        removed=removed,
        total_found=len(video_paths)
    )


def _generate_title_from_path(path: str) -> str:
    """Generate a readable title from video file path.

    Args:
        path: Video file path (e.g. "cartoons/peppa.mp4")

    Returns:
        Formatted title (e.g. "Peppa")
    """
    # Get filename without extension
    filename = Path(path).stem

    # Replace underscores and hyphens with spaces
    title = filename.replace("_", " ").replace("-", " ")

    # Capitalize first letter of each word
    title = title.title()

    return title


def _extract_tags_from_path(path: str) -> Optional[str]:
    """Extract tags from directory name in path.

    Args:
        path: Video file path (e.g. "cartoons/peppa.mp4")

    Returns:
        Tag string (e.g. "cartoons") or None if in root
    """
    # Get parent directory name
    parent = Path(path).parent

    if parent == Path("."):
        return None

    # Use directory name as tag
    return str(parent).split("/")[0]


# Queue management endpoints
@app.get("/api/queue/{client_id}", response_model=List[QueueItemResponse])
def get_queue(client_id: str, db: Session = Depends(get_db)):
    """Get client's queue.

    Args:
        client_id: Client identifier
        db: Database session

    Returns:
        List of queue items sorted by position
    """
    from src.db.repositories import QueueRepository

    queue_repo = QueueRepository(db)
    queue = queue_repo.get_by_client(client_id)

    return queue


@app.post("/api/queue/{client_id}", response_model=QueueAddResponse, status_code=201)
def add_to_queue(
    client_id: str,
    request: QueueAddRequest,
    db: Session = Depends(get_db)
):
    """Add videos to client's queue.

    Args:
        client_id: Client identifier
        request: Add request with video IDs
        db: Database session

    Returns:
        Add operation results

    Raises:
        HTTPException: 404 if video not found
    """
    from src.db.repositories import QueueRepository, VideoRepository

    video_repo = VideoRepository(db)
    queue_repo = QueueRepository(db)

    added = 0

    for video_id in request.video_ids:
        # Verify video exists
        video = video_repo.get_by_id(video_id)
        if video is None:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        # Add to queue
        queue_repo.add(client_id=client_id, video_id=video_id)
        added += 1

    # Get total count after adding
    total = queue_repo.count(client_id)

    return QueueAddResponse(added=added, total_in_queue=total)


@app.delete("/api/queue/{client_id}/{queue_id}")
def remove_from_queue(
    client_id: str,
    queue_id: int,
    db: Session = Depends(get_db)
):
    """Remove an item from client's queue.

    Args:
        client_id: Client identifier
        queue_id: Queue item ID to remove
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 404 if queue item not found or doesn't belong to client
    """
    from src.db.models import Queue

    # Verify queue item exists and belongs to client
    queue_item = db.query(Queue).filter(
        Queue.id == queue_id,
        Queue.client_id == client_id
    ).first()

    if queue_item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Queue item {queue_id} not found for client {client_id}"
        )

    # Remove item
    db.delete(queue_item)
    db.commit()

    return {"message": "Queue item removed"}


@app.post("/api/queue/{client_id}/clear", response_model=QueueClearResponse)
def clear_queue(client_id: str, db: Session = Depends(get_db)):
    """Clear all items from client's queue.

    Args:
        client_id: Client identifier
        db: Database session

    Returns:
        Number of items removed
    """
    from src.db.repositories import QueueRepository

    queue_repo = QueueRepository(db)

    # Count items before clearing
    count = queue_repo.count(client_id)

    # Clear queue
    queue_repo.clear(client_id)

    return QueueClearResponse(removed=count)


@app.put("/api/queue/{client_id}/reorder")
def reorder_queue(
    client_id: str,
    request: QueueReorderRequest,
    db: Session = Depends(get_db)
):
    """Reorder client's queue.

    Args:
        client_id: Client identifier
        request: Reorder request with queue IDs in new order
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 404 if any queue item not found or doesn't belong to client
    """
    from src.db.models import Queue

    # Verify all queue items exist and belong to client
    for queue_id in request.queue_ids:
        queue_item = db.query(Queue).filter(
            Queue.id == queue_id,
            Queue.client_id == client_id
        ).first()

        if queue_item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Queue item {queue_id} not found for client {client_id}"
            )

    # Reorder
    from src.db.repositories import QueueRepository
    queue_repo = QueueRepository(db)
    queue_repo.reorder(client_id, request.queue_ids)

    return {"message": "Queue reordered"}


# Statistics endpoints
@app.get("/api/stats", response_model=SystemStatsResponse)
def get_system_stats(db: Session = Depends(get_db)):
    """Get system-wide statistics.

    Returns:
        SystemStatsResponse with overall system metrics
    """
    video_repo = VideoRepository(db)
    client_repo = ClientRepository(db)

    # Count videos
    all_videos = video_repo.get_all()

    # Count clients
    all_clients = client_repo.get_all()

    # Count plays
    from src.db.models import PlayLog
    total_plays = db.query(PlayLog).count()

    # Count today's plays
    from datetime import datetime, time
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    plays_today = db.query(PlayLog).filter(
        PlayLog.played_at >= start_of_day,
        PlayLog.played_at <= end_of_day
    ).count()

    return SystemStatsResponse(
        total_videos=len(all_videos),
        total_clients=len(all_clients),
        total_plays=total_plays,
        plays_today=plays_today
    )


@app.get("/api/stats/client/{client_id}", response_model=ClientStatsResponse)
def get_client_stats(client_id: str, db: Session = Depends(get_db)):
    """Get statistics for a specific client.

    Args:
        client_id: Client identifier

    Returns:
        ClientStatsResponse with client-specific metrics

    Raises:
        HTTPException: 404 if client not found
    """
    client_repo = ClientRepository(db)
    play_log_repo = PlayLogRepository(db)
    queue_repo = QueueRepository(db)

    # Get client
    client = client_repo.get_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    # Get play counts
    today = date.today()
    plays_today = play_log_repo.count_plays_today(client_id, today)
    plays_remaining = max(0, client.daily_limit - plays_today)

    # Get total plays (all time)
    from src.db.models import PlayLog
    total_plays = db.query(PlayLog).filter(
        PlayLog.client_id == client_id
    ).count()

    # Get queue size
    queue_size = queue_repo.count(client_id)

    # Get recent plays
    recent_plays_data = play_log_repo.get_recent_plays(client_id, limit=10)

    # Convert to response format
    recent_plays = [
        RecentPlayResponse(
            video_id=play.video_id,
            video_title=play.video.title,
            played_at=play.played_at
        )
        for play in recent_plays_data
    ]

    return ClientStatsResponse(
        client_id=client.client_id,
        friendly_name=client.friendly_name,
        daily_limit=client.daily_limit,
        plays_today=plays_today,
        plays_remaining=plays_remaining,
        total_plays=total_plays,
        queue_size=queue_size,
        recent_plays=recent_plays
    )


# Mount static files for media serving
# This must be done after defining routes to avoid conflicts
try:
    media_path = Path(MEDIA_DIRECTORY)
    if media_path.exists() and media_path.is_dir():
        app.mount(
            "/media/library",
            StaticFiles(directory=str(media_path)),
            name="media"
        )
except Exception:
    # If media directory doesn't exist yet, skip mounting
    # It will be mounted when set_media_directory is called
    pass
