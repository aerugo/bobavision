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
        repo.create(path="cartoons/video1.mp4", title="Cartoon 1", tags="cartoons"),
        repo.create(path="educational/video2.mp4", title="Educational 2", tags="educational"),
        repo.create(path="bedtime/story.mp4", title="Bedtime Story", tags="bedtime"),
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
    assert len(data) == 3

    # Check structure of first video
    video = data[0]
    assert "id" in video
    assert "path" in video
    assert "title" in video
    assert "tags" in video
    assert "duration_seconds" in video
    assert "created_at" in video




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
    video_repo.create(path="cartoons/peppa.mp4", title="Peppa Pig")

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


# Tests for removing videos that are no longer in library folder
def test_scan_videos_removes_videos_not_in_library(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scanning removes videos from DB that are no longer in library folder.

    RED phase: This functionality doesn't exist yet.
    """
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)

    # Add a video to DB that doesn't exist in filesystem
    deleted_video = video_repo.create(
        path="deleted/video.mp4",
        title="Deleted Video",
        tags="deleted"
    )

    # Also add a video that does exist
    video_repo.create(
        path="cartoons/peppa.mp4",
        title="Peppa",
        tags="cartoons"
    )

    # Verify we have 2 videos before scan
    assert len(video_repo.get_all()) == 2

    # Act - Scan should remove the deleted video
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    # The deleted video should be removed
    videos = video_repo.get_all()
    video_paths = [v.path for v in videos]

    assert "deleted/video.mp4" not in video_paths
    assert "cartoons/peppa.mp4" in video_paths


def test_scan_videos_returns_removed_count(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that scan response includes count of removed videos.

    RED phase: Response schema doesn't include 'removed' field yet.
    """
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)

    # Add multiple videos that don't exist in filesystem
    video_repo.create(path="deleted1.mp4", title="Deleted 1")
    video_repo.create(path="deleted2.mp4", title="Deleted 2")
    video_repo.create(path="deleted3.mp4", title="Deleted 3")

    # Act
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "removed" in data
    assert data["removed"] == 3


def test_scan_videos_removes_queue_items_for_deleted_videos(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that queue items are removed when their video is deleted from library.

    RED phase: Queue items for deleted videos are not removed yet.
    """
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository, QueueRepository, ClientRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)
    queue_repo = QueueRepository(db_session)
    client_repo = ClientRepository(db_session)

    # Create a client
    client = client_repo.create(client_id="test-client", friendly_name="Test Client")

    # Add a video that doesn't exist in filesystem
    deleted_video = video_repo.create(
        path="deleted/video.mp4",
        title="Deleted Video"
    )

    # Add this video to the queue
    queue_item = queue_repo.add(client_id=client.client_id, video_id=deleted_video.id)

    # Verify queue has the item
    assert queue_repo.count(client.client_id) == 1

    # Act - Scan should remove the video and its queue items
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    # The queue should now be empty
    assert queue_repo.count(client.client_id) == 0


def test_scan_videos_preserves_play_logs_for_deleted_videos(client_with_db, db_session, media_directory_with_files, monkeypatch):
    """Test that play logs are preserved even when video is deleted from library.

    This is important for historical statistics.

    RED phase: Play logs might be deleted due to cascade, need to verify they're preserved.
    """
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository, PlayLogRepository, ClientRepository

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(media_directory_with_files))

    video_repo = VideoRepository(db_session)
    play_log_repo = PlayLogRepository(db_session)
    client_repo = ClientRepository(db_session)

    # Create a client
    client = client_repo.create(client_id="test-client", friendly_name="Test Client")

    # Add a video that doesn't exist in filesystem
    deleted_video = video_repo.create(
        path="deleted/video.mp4",
        title="Deleted Video"
    )

    deleted_video_id = deleted_video.id

    # Log a play for this video
    play_log = play_log_repo.log_play(
        client_id=client.client_id,
        video_id=deleted_video_id
    )
    play_log_id = play_log.id

    # Verify play log exists
    from src.db.models import PlayLog
    play_count_before = db_session.query(PlayLog).filter(
        PlayLog.id == play_log_id
    ).count()
    assert play_count_before == 1

    # Act - Scan should remove the video but preserve play logs
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200

    # The video should be removed
    assert video_repo.get_by_id(deleted_video_id) is None

    # But the play log should still exist (with video_id set to NULL)
    preserved_play_log = db_session.query(PlayLog).filter(
        PlayLog.id == play_log_id
    ).first()
    assert preserved_play_log is not None
    assert preserved_play_log.video_id is None  # Foreign key set to NULL


def test_scan_videos_handles_all_videos_deleted(client_with_db, db_session, tmp_path, monkeypatch):
    """Test that scanning handles the case where all videos have been deleted from library."""
    # Arrange
    from src import main
    from src.db.repositories import VideoRepository

    # Create empty media directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    monkeypatch.setattr(main, "MEDIA_DIRECTORY", str(empty_dir))

    video_repo = VideoRepository(db_session)

    # Add some videos to DB that don't exist in filesystem
    video_repo.create(path="video1.mp4", title="Video 1")
    video_repo.create(path="video2.mp4", title="Video 2")
    video_repo.create(path="video3.mp4", title="Video 3")

    assert len(video_repo.get_all()) == 3

    # Act - Scan empty directory should remove all videos
    response = client_with_db.post("/api/videos/scan")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["removed"] == 3
    assert data["total_found"] == 0
    assert len(video_repo.get_all()) == 0
