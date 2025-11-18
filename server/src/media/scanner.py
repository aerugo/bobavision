"""Media scanner module for discovering video files.

GREEN phase: Implement minimum code to pass tests.
"""
import os
from pathlib import Path
from typing import List


class VideoScanner:
    """Scans directories for video files."""

    # Supported video file extensions
    VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov")

    def __init__(self, path: str):
        """Initialize scanner with directory path.

        Args:
            path: Directory path to scan for videos
        """
        self.path = Path(path)

    def scan(self) -> List[str]:
        """Scan directory for video files.

        Returns:
            List of relative paths to video files
        """
        videos = []

        # Walk through directory tree
        for root, dirs, files in os.walk(self.path):
            for file in files:
                # Check if file has video extension
                if file.lower().endswith(self.VIDEO_EXTENSIONS):
                    # Get full path
                    full_path = Path(root) / file
                    # Convert to relative path from scan directory
                    relative_path = full_path.relative_to(self.path)
                    videos.append(str(relative_path))

        return videos
