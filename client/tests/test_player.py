"""Tests for mpv video player wrapper."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.player import Player


class TestPlayerInitialization:
    """Test player initialization."""

    def test_player_initializes_with_no_process(self):
        """Test that Player initializes with no active process."""
        # Arrange & Act
        player = Player()

        # Assert
        assert player.process is None
        assert player.is_playing is False

    def test_player_initializes_with_custom_config(self):
        """Test that Player can initialize with custom configuration."""
        # Arrange & Act
        player = Player(fullscreen=False, no_osc=False)

        # Assert
        assert player.fullscreen is False
        assert player.no_osc is False


class TestPlayVideo:
    """Test video playback."""

    @patch('subprocess.Popen')
    def test_play_starts_mpv_process(self, mock_popen):
        """Test that play() starts mpv process."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        player = Player()

        # Act
        player.play("http://localhost:8000/media/test.mp4")

        # Assert
        mock_popen.assert_called_once()
        assert player.process is not None
        assert player.is_playing is True

    @patch('subprocess.Popen')
    def test_play_uses_correct_mpv_arguments(self, mock_popen):
        """Test that play() uses correct mpv command arguments."""
        # Arrange
        mock_process = Mock()
        mock_popen.return_value = mock_process
        player = Player()

        # Act
        player.play("http://localhost:8000/media/test.mp4")

        # Assert
        args = mock_popen.call_args[0][0]
        assert "mpv" in args
        assert "--fs" in args or "--fullscreen" in args
        assert "--no-osc" in args
        assert "http://localhost:8000/media/test.mp4" in args

    @patch('subprocess.Popen')
    def test_play_with_local_file_path(self, mock_popen):
        """Test playing a local file path."""
        # Arrange
        mock_process = Mock()
        mock_popen.return_value = mock_process
        player = Player()

        # Act
        player.play("/home/user/video.mp4")

        # Assert
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert "/home/user/video.mp4" in args

    @patch('subprocess.Popen')
    def test_play_stops_existing_video_before_starting_new_one(self, mock_popen):
        """Test that playing new video stops existing one."""
        # Arrange
        mock_process1 = Mock()
        mock_process1.poll.return_value = None
        mock_process2 = Mock()
        mock_popen.side_effect = [mock_process1, mock_process2]
        player = Player()

        # Act
        player.play("http://localhost:8000/media/video1.mp4")
        player.play("http://localhost:8000/media/video2.mp4")

        # Assert
        mock_process1.terminate.assert_called_once()
        assert player.process == mock_process2

    @patch('subprocess.Popen')
    def test_play_sets_video_url(self, mock_popen):
        """Test that play() stores the current video URL."""
        # Arrange
        mock_process = Mock()
        mock_popen.return_value = mock_process
        player = Player()

        # Act
        player.play("http://localhost:8000/media/test.mp4")

        # Assert
        assert player.current_url == "http://localhost:8000/media/test.mp4"


class TestVideoStatus:
    """Test video playback status checks."""

    @patch('subprocess.Popen')
    def test_is_running_returns_true_when_playing(self, mock_popen):
        """Test that is_running() returns True when video is playing."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = None  # None means still running
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        result = player.is_running()

        # Assert
        assert result is True

    @patch('subprocess.Popen')
    def test_is_running_returns_false_when_finished(self, mock_popen):
        """Test that is_running() returns False when video finished."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = 0  # 0 means process finished
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        result = player.is_running()

        # Assert
        assert result is False

    def test_is_running_returns_false_when_no_process(self):
        """Test that is_running() returns False when no process exists."""
        # Arrange
        player = Player()

        # Act
        result = player.is_running()

        # Assert
        assert result is False

    @patch('subprocess.Popen')
    def test_wait_for_completion_blocks_until_video_ends(self, mock_popen):
        """Test that wait_for_completion() waits for process to end."""
        # Arrange
        mock_process = Mock()
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        player.wait_for_completion()

        # Assert
        mock_process.wait.assert_called_once()

    @patch('subprocess.Popen')
    def test_get_exit_code_returns_process_exit_code(self, mock_popen):
        """Test that get_exit_code() returns the process exit code."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        exit_code = player.get_exit_code()

        # Assert
        assert exit_code == 0


class TestStopVideo:
    """Test stopping video playback."""

    @patch('subprocess.Popen')
    def test_stop_terminates_process(self, mock_popen):
        """Test that stop() terminates the mpv process."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        player.stop()

        # Assert
        mock_process.terminate.assert_called_once()
        assert player.is_playing is False

    @patch('subprocess.Popen')
    def test_stop_does_nothing_when_no_process(self, mock_popen):
        """Test that stop() handles no active process gracefully."""
        # Arrange
        player = Player()

        # Act & Assert (should not raise exception)
        player.stop()
        assert player.process is None

    @patch('subprocess.Popen')
    def test_stop_waits_for_graceful_shutdown(self, mock_popen):
        """Test that stop() waits briefly for graceful shutdown."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, 0]  # Takes 3 polls to finish
        mock_popen.return_value = mock_process
        player = Player()
        player.play("http://localhost:8000/media/test.mp4")

        # Act
        player.stop()

        # Assert
        mock_process.terminate.assert_called_once()
        # Should have polled to check if terminated
        assert mock_process.poll.call_count >= 1


class TestErrorHandling:
    """Test error handling in video player."""

    @patch('subprocess.Popen')
    def test_play_handles_mpv_not_found(self, mock_popen):
        """Test handling when mpv is not installed."""
        # Arrange
        mock_popen.side_effect = FileNotFoundError("mpv not found")
        player = Player()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            player.play("http://localhost:8000/media/test.mp4")

    @patch('subprocess.Popen')
    def test_play_handles_invalid_url(self, mock_popen):
        """Test handling of invalid video URL."""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Non-zero exit = error
        mock_popen.return_value = mock_process
        player = Player()

        # Act
        player.play("http://localhost:8000/media/nonexistent.mp4")

        # Assert
        # Should still create process (mpv will handle the error)
        assert player.process is not None
