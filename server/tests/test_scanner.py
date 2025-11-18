"""Tests for media scanner module.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from pathlib import Path


def test_scanner_finds_mp4_files(tmp_path):
    """Test that scanner finds .mp4 files in directory."""
    # Arrange - Create test video files
    (tmp_path / "video1.mp4").touch()
    (tmp_path / "video2.mp4").touch()
    (tmp_path / "readme.txt").touch()  # Should be ignored

    # Import will fail initially (RED phase)
    from src.media.scanner import VideoScanner

    # Act
    scanner = VideoScanner(str(tmp_path))
    videos = scanner.scan()

    # Assert
    assert len(videos) == 2
    assert all(v.endswith(".mp4") for v in videos)


def test_scanner_returns_empty_list_for_empty_directory(tmp_path):
    """Test that scanner returns empty list when no videos found."""
    # Arrange - Empty directory
    from src.media.scanner import VideoScanner

    # Act
    scanner = VideoScanner(str(tmp_path))
    videos = scanner.scan()

    # Assert
    assert videos == []
    assert isinstance(videos, list)


def test_scanner_ignores_non_video_files(tmp_path):
    """Test that scanner only returns video files."""
    # Arrange - Create mixed files
    (tmp_path / "video.mp4").touch()
    (tmp_path / "video.mkv").touch()
    (tmp_path / "image.jpg").touch()
    (tmp_path / "document.pdf").touch()
    (tmp_path / "readme.txt").touch()

    from src.media.scanner import VideoScanner

    # Act
    scanner = VideoScanner(str(tmp_path))
    videos = scanner.scan()

    # Assert
    assert len(videos) == 2  # Only .mp4 and .mkv
    assert all(v.endswith((".mp4", ".mkv")) for v in videos)


def test_scanner_handles_nested_directories(tmp_path):
    """Test that scanner finds videos in subdirectories."""
    # Arrange - Create nested structure
    (tmp_path / "video1.mp4").touch()
    subdir = tmp_path / "shows" / "episode1"
    subdir.mkdir(parents=True)
    (subdir / "video2.mp4").touch()

    from src.media.scanner import VideoScanner

    # Act
    scanner = VideoScanner(str(tmp_path))
    videos = scanner.scan()

    # Assert
    assert len(videos) == 2
    # Should return relative paths
    assert any("shows" in v for v in videos)
