"""FastAPI application entry point.

GREEN phase: Implement minimal API to pass tests.
"""
import random
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.media.scanner import VideoScanner


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
    version="0.1.0"
)


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
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/api/next", response_model=NextVideoResponse)
def get_next_video(client_id: str = Query(..., description="Client identifier")):
    """Get the next video for a client.

    In Phase 1: Returns random video from library.
    Phase 2 will add daily limits and placeholder logic.
    Phase 3 will add queue support.

    Args:
        client_id: Unique identifier for the client device

    Returns:
        NextVideoResponse with video URL, title, and placeholder flag
    """
    # Scan media directory for videos
    scanner = VideoScanner(MEDIA_DIRECTORY)
    videos = scanner.scan()

    # For Phase 1: just pick a random video
    # (Phase 2 will add limit checking and placeholder logic)
    if not videos:
        # No videos available - this is an edge case
        # In Phase 2, we'll return a placeholder
        # For now, return a simple error indicator
        return NextVideoResponse(
            url="/media/library/none.mp4",
            title="No videos available",
            placeholder=True
        )

    # Select random video
    selected_video = random.choice(videos)

    # Extract title from filename
    title = Path(selected_video).stem.replace("_", " ").replace("-", " ").title()

    # Build URL path
    # In Phase 1, we assume videos will be served from /media/library/
    url = f"/media/library/{selected_video}"

    return NextVideoResponse(
        url=url,
        title=title,
        placeholder=False
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
