"""Tests for video management and scanning API endpoints.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_db(db_session, monkeypatch):
    """Create test client with database override."""
    from src.main import app
    from src.db.database import get_db

    # Mock init_db to prevent startup event from initializing wrong database
    import src.db.database
    monkeypatch.setattr(src.db.database, "init_db", lambda: None)

    # Override database dependency to use test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close test session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_videos_in_db(db_session):
    """Create sample videos in database."""
    from src.db.repositories import VideoRepository

    repo = VideoRepository(db_session)
    videos = [
        repo.create(path="cartoons/video1.mp4", title="Cartoon 1", is_placeholder=False, tags="cartoons"),
        repo.create(path="educational/video2.mp4", title="Educational 2", is_placeholder=False, tags="educational"),
        repo.create(path="placeholder.mp4", title="All Done!", is_placeholder=True),
        repo.create(path="bedtime/story.mp4", title="Bedtime Story", is_placeholder=False, tags="bedtime"),
    ]
    return videos


@pytest.fixture
def media_directory_with_files(tmp_path):
    """Create a temporary media directory with video files."""
    # Create directory structure
    (tmp_path / "cartoons").mkdir()
    (tmp_path / "educational").mkdir()
    (tmp_path / "placeholders").mkdir()

    # Create fake video files
    (tmp_path / "cartoons" / "peppa.mp4").write_text("fake video")
    (tmp_path / "cartoons" / "bluey.mp4").write_text("fake video")
    (tmp_path / "educational" / "numbers.mp4").write_text("fake video")
    (tmp_path / "educational" / "letters.mkv").write_text("fake video")
    (tmp_path / "placeholders" / "alldone.mp4").write_text("fake video")
    (tmp_path / "movie.mp4").write_text("fake video")

    # Create non-video files that should be ignored
    (tmp_path / "readme.txt").write_text("not a video")
    (tmp_path / "cartoons" / "thumbnail.jpg").write_text("image")

    return tmp_path


# GET /api/videos - List all videos
def test_get_videos_returns_empty_list_when_no_videos(client_with_db):
    """Test that GET /api/videos returns empty list when no videos in database.

    RED phase: Endpoint doesn't exist yet.
    """
    # Act
    response = client_with_db.get("/api/videos")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_videos_returns_all_videos(client_with_db, sample_videos_in_db):
    """Test that GET /api/videos returns all videos from database."""
    # Act
    response = client_with_db.get("/api/videos")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 4

    # Check structure of first video
    video = data[0]
    assert "id" in video
    assert "path" in video
    assert "title" in video
    assert "tags" in video
    assert "is_placeholder" in video
    assert "duration_seconds" in video
    assert "created_at" in video


def test_get_videos_filters_by_is_placeholder_false(client_with_db, sample_videos_in_db):
    """Test that GET /api/videos?is_placeholder=false returns only non-placeholder videos."""
    # Act
    response = client_with_db.get("/api/videos?is_placeholder=false")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3  # Should exclude the placeholder
    for video in data:
        assert video["is_placeholder"] is False


def test_get_videos_filters_by_is_placeholder_true(client_with_db, sample_videos_in_db):
    """Test that GET /api/videos?is_placeholder=true returns only placeholder videos."""
    # Act
    response = client_with_db.get("/api/videos?is_placeholder=true")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1  # Should only return the placeholder
    assert data[0]["is_placeholder"] is True
    assert data[0]["title"] == "All Done!"


def test_get_videos_filters_by_tags(client_with_db, sample_videos_in_db):
    """Test that GET /api/videos?tags=cartoons returns videos with matching tags."""
    # Act
    response = client_with_db.get("/api/videos?tags=cartoons")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["tags"] == "cartoons"


def test_get_videos_returns_videos_sorted_by_title(client_with_db, sample_videos_in_db):
    """Test that videos are returned sorted by title."""
    # Act
    response = client_with_db.get("/api/videos")

    # Assert
    assert response.status_code == 200
    data = response.json()

    titles = [v["title"] for v in data]
    assert titles == sorted(titles)


# POST /api/videos/scan - Scan filesystem and populate database
def test_scan_videos_returns_scan_results(client_with_db, media_directory_with_files, monkeypatch):
    """Test that POST /api/videos/scan scans filesystem and returns results.

    RED phase: Endpoint doesn't exist yet.
    """
    # Arrange - Mock the media directory
    from src import main
    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "added" in data
    assert "skipped" in data
    assert "total_found" in data
    assert data["total_found"] > 0


def test_scan_videos_adds_new_videos_to_database(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning adds video files to database."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)

    # Verify database is empty
    assert len(video_repo.get_all()) == 0

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Check that videos were added
    videos = video_repo.get_all()
    assert len(videos) == data["added"]
    assert len(videos) > 0


def test_scan_videos_finds_all_video_extensions(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning finds .mp4, .mkv, .avi, .mov files."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    video_repo = VideoRepository(db_session)
    videos = video_repo.get_all()

    # Should find mp4 and mkv files from our test directory
    paths = [v.path for v in videos]
    assert any(".mp4" in p for p in paths)
    assert any(".mkv" in p for p in paths)


def test_scan_videos_skips_existing_videos(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning skips videos already in database."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)

    # Pre-populate with one video
    video_repo.create(path="cartoons/peppa.mp4", title="Peppa Pig", is_placeholder=False)

    # Act - First scan
    response1 = client_with_db.post("/api/videos/scan")
    assert response1.status_code == 200
    data1 = response1.json()

    # Act - Second scan
    response2 = client_with_db.post("/api/videos/scan")
    assert response2.status_code == 200
    data2 = response2.json()

    # Assert
    # Second scan should skip all videos (they're already in DB)
    assert data2["added"] == 0
    assert data2["skipped"] == data2["total_found"]


def test_scan_videos_generates_title_from_filename(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning generates readable titles from filenames."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    video_repo = VideoRepository(db_session)
    videos = video_repo.get_all()

    # Find a specific video and check its title
    peppa = next((v for v in videos if "peppa" in v.path.lower()), None)
    assert peppa is not None
    assert peppa.title != "peppa.mp4"  # Should be formatted
    # Title should be capitalized and without extension
    assert ".mp4" not in peppa.title


def test_scan_videos_detects_placeholders(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning detects placeholder videos by path."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    video_repo = VideoRepository(db_session)
    videos = video_repo.get_all()

    # Find placeholder video
    placeholders = [v for v in videos if v.is_placeholder]
    assert len(placeholders) > 0

    # Check that it's from the placeholders directory
    placeholder = placeholders[0]
    assert "placeholder" in placeholder.path.lower()


def test_scan_videos_extracts_tags_from_directory(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning extracts tags from parent directory name."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    video_repo = VideoRepository(db_session)
    videos = video_repo.get_all()

    # Find video in cartoons directory
    cartoon_video = next((v for v in videos if "cartoons/" in v.path), None)
    assert cartoon_video is not None
    assert cartoon_video.tags == "cartoons"

    # Find video in educational directory
    edu_video = next((v for v in videos if "educational/" in v.path), None)
    assert edu_video is not None
    assert edu_video.tags == "educational"


def test_scan_videos_handles_empty_directory(client_with_db, tmp_path, monkeypatch):
    """Test that scanning empty directory returns zero results."""
    # Arrange
    from src import main
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(empty_dir))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["total_found"] == 0
    assert data["added"] == 0
    assert data["skipped"] == 0


def test_scan_videos_handles_nonexistent_directory(client_with_db, tmp_path, monkeypatch):
    """Test that scanning nonexistent directory returns appropriate error."""
    # Arrange
    from src import main
    nonexistent = tmp_path / "does_not_exist"

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(nonexistent))

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    # Could be 404, 400, or 200 with zero results depending on implementation
    assert response.status_code in [200, 400, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["total_found"] == 0
