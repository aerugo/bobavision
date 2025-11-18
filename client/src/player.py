"""
Video player wrapper for mpv.

This module provides a simple interface to control mpv video playback
on the Raspberry Pi client.
"""
import logging
import subprocess
import time
from typing import Optional

logger = logging.getLogger(__name__)


class Player:
    """Wrapper for mpv video player."""

    def __init__(self, fullscreen: bool = True, no_osc: bool = True):
        """
        Initialize the video player.

        Args:
            fullscreen: Whether to play videos in fullscreen mode (default: True)
            no_osc: Whether to disable on-screen controls (default: True)
        """
        self.fullscreen = fullscreen
        self.no_osc = no_osc
        self.process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.current_url: Optional[str] = None

    def play(self, url: str):
        """
        Play a video from the given URL or file path.

        Args:
            url: HTTP URL or local file path to the video

        Raises:
            FileNotFoundError: If mpv is not installed
        """
        # Stop any existing video first
        if self.is_running():
            self.stop()

        # Build mpv command arguments
        args = ["mpv"]

        if self.fullscreen:
            args.append("--fs")

        if self.no_osc:
            args.append("--no-osc")

        # Disable on-screen display bar
        args.append("--no-osd-bar")

        # Disable input from terminal
        args.append("--no-input-terminal")

        # Add the video URL/path
        args.append(url)

        # Start mpv process with logging
        logger.info(f"Starting mpv with command: {' '.join(args)}")
        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Check if process started successfully
            time.sleep(0.1)  # Give it a moment to fail if it's going to
            if self.process.poll() is not None:
                # Process already exited - capture error output
                stdout, stderr = self.process.communicate()
                logger.error(
                    f"mpv exited immediately with code {self.process.returncode}\n"
                    f"stdout: {stdout.decode() if stdout else '(empty)'}\n"
                    f"stderr: {stderr.decode() if stderr else '(empty)'}"
                )
                raise RuntimeError(f"mpv failed to start (exit code {self.process.returncode})")

            self.is_playing = True
            self.current_url = url
            logger.info(f"mpv started successfully for: {url}")

        except FileNotFoundError:
            logger.error("mpv is not installed or not in PATH")
            raise
        except Exception as e:
            logger.error(f"Failed to start mpv: {e}", exc_info=True)
            raise

    def is_running(self) -> bool:
        """
        Check if a video is currently playing.

        Returns:
            bool: True if video is playing, False otherwise
        """
        if self.process is None:
            return False

        # Check if process has ended
        return_code = self.process.poll()
        return return_code is None

    def wait_for_completion(self):
        """
        Block until the video finishes playing.

        This method will wait indefinitely until the mpv process exits.
        """
        if self.process is not None:
            exit_code = self.process.wait()
            self.is_playing = False

            if exit_code != 0:
                # Capture any error output
                stdout, stderr = self.process.communicate()
                logger.warning(
                    f"mpv exited with code {exit_code}\n"
                    f"stdout: {stdout.decode() if stdout else '(empty)'}\n"
                    f"stderr: {stderr.decode() if stderr else '(empty)'}"
                )
            else:
                logger.info(f"Video playback completed successfully (exit code 0)")

    def get_exit_code(self) -> Optional[int]:
        """
        Get the exit code of the mpv process.

        Returns:
            int or None: Exit code if process finished, None if still running
        """
        if self.process is None:
            return None

        return self.process.poll()

    def stop(self):
        """
        Stop the currently playing video.

        This sends a terminate signal to mpv and waits briefly
        for it to shut down gracefully.
        """
        if self.process is None:
            return

        # Send terminate signal
        self.process.terminate()

        # Wait up to 2 seconds for graceful shutdown
        for _ in range(20):
            if self.process.poll() is not None:
                break
            time.sleep(0.1)

        # If still running, force kill
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait()

        self.is_playing = False
        self.process = None
        self.current_url = None
