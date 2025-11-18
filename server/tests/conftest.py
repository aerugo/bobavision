"""Shared test fixtures for all tests.

Provides common setup like test client, mock data, etc.
"""
import pytest
from pathlib import Path


@pytest.fixture
def sample_videos(tmp_path):
    """Create sample video files for testing.

    Returns:
        Path: Directory containing sample video files
    """
    # Create test video files
    (tmp_path / "video1.mp4").write_text("fake video content 1")
    (tmp_path / "video2.mp4").write_text("fake video content 2")
    (tmp_path / "video3.mp4").write_text("fake video content 3")

    return tmp_path


@pytest.fixture
def empty_media_dir(tmp_path):
    """Create empty media directory.

    Returns:
        Path: Empty directory
    """
    return tmp_path
