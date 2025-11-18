"""FastAPI application entry point.

Phase 2: Updated with database integration and daily limits.
"""
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.database import get_db, init_db
from src.db.repositories import VideoRepository, ClientRepository, PlayLogRepository
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
    client_id: str
    friendly_name: str
    daily_limit: int
    tag_filters: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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


# Create FastAPI app
app = FastAPI(
    title="Kids Media Station API",
    description="API for kids single-button media station",
    version="0.2.0"
)


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup."""
    init_db()


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

    Phase 2: Enforces daily limits, logs plays, returns placeholders when limit reached.
    Phase 3 will add queue support.

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

    # Get or create client
    client = client_repo.get_or_create(
        client_id=client_id,
        friendly_name=f"Client {client_id}"
    )

    # Check if daily limit reached
    today = date.today()
    limit_reached = limit_service.is_limit_reached(client_id, today)

    # Select video based on limit status
    if limit_reached:
        # Limit reached - return placeholder
        video = video_repo.get_random_placeholder()

        if video is None:
            # No placeholder videos available - return error message
            return NextVideoResponse(
                url="/media/library/none.mp4",
                title="No placeholder videos available",
                placeholder=True
            )

        is_placeholder = True
    else:
        # Under limit - return real video
        video = video_repo.get_random_non_placeholder()

        if video is None:
            # No videos available - return error message
            return NextVideoResponse(
                url="/media/library/none.mp4",
                title="No videos available",
                placeholder=True
            )

        is_placeholder = False

    # Log the play
    play_log_repo.log_play(
        client_id=client_id,
        video_id=video.id,
        is_placeholder=is_placeholder
    )

    # Build URL path
    url = f"/media/library/{video.path}"

    return NextVideoResponse(
        url=url,
        title=video.title,
        placeholder=is_placeholder
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
def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing client.

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
