"""FastAPI application entry point.

Phase 2: Updated with database integration and daily limits.
"""
from datetime import date
from pathlib import Path
from fastapi import FastAPI, Query, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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
