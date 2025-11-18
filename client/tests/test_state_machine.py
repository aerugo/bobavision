"""Tests for client state machine."""
import pytest
from unittest.mock import Mock
from src.state_machine import StateMachine, State


class TestStateMachineInitialization:
    """Test state machine initialization."""

    def test_state_machine_initializes_in_idle_state(self):
        """Test that state machine starts in IDLE state."""
        # Arrange & Act
        sm = StateMachine()

        # Assert
        assert sm.current_state == State.IDLE

    def test_state_machine_has_state_enum(self):
        """Test that State enum has expected values."""
        # Assert
        assert hasattr(State, 'IDLE')
        assert hasattr(State, 'LOADING')
        assert hasattr(State, 'PLAYING')
        assert hasattr(State, 'ERROR')


class TestIdleState:
    """Test transitions from IDLE state."""

    def test_button_press_in_idle_transitions_to_loading(self):
        """Test IDLE → LOADING transition on button press."""
        # Arrange
        sm = StateMachine()

        # Act
        new_state = sm.on_button_press()

        # Assert
        assert sm.current_state == State.LOADING
        assert new_state == State.LOADING

    def test_button_press_in_idle_returns_loading_state(self):
        """Test that button press returns the new state."""
        # Arrange
        sm = StateMachine()

        # Act
        new_state = sm.on_button_press()

        # Assert
        assert new_state == State.LOADING


class TestLoadingState:
    """Test transitions from LOADING state."""

    def test_video_ready_in_loading_transitions_to_playing(self):
        """Test LOADING → PLAYING transition when video ready."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()  # Move to LOADING

        # Act
        new_state = sm.on_video_ready()

        # Assert
        assert sm.current_state == State.PLAYING
        assert new_state == State.PLAYING

    def test_button_press_in_loading_stays_in_loading(self):
        """Test that button press in LOADING state is ignored."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()  # Move to LOADING

        # Act
        new_state = sm.on_button_press()

        # Assert
        assert sm.current_state == State.LOADING
        assert new_state == State.LOADING

    def test_error_in_loading_transitions_to_error(self):
        """Test LOADING → ERROR transition on error."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()  # Move to LOADING

        # Act
        new_state = sm.on_error("Network error")

        # Assert
        assert sm.current_state == State.ERROR
        assert new_state == State.ERROR


class TestPlayingState:
    """Test transitions from PLAYING state."""

    def test_video_end_in_playing_transitions_to_idle(self):
        """Test PLAYING → IDLE transition when video ends."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()  # IDLE → LOADING
        sm.on_video_ready()    # LOADING → PLAYING

        # Act
        new_state = sm.on_video_end()

        # Assert
        assert sm.current_state == State.IDLE
        assert new_state == State.IDLE

    def test_button_press_in_playing_stays_in_playing(self):
        """Test that button press during playback is ignored."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()  # IDLE → LOADING
        sm.on_video_ready()    # LOADING → PLAYING

        # Act
        new_state = sm.on_button_press()

        # Assert
        assert sm.current_state == State.PLAYING
        assert new_state == State.PLAYING

    def test_error_in_playing_transitions_to_error(self):
        """Test PLAYING → ERROR transition on error."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_video_ready()

        # Act
        new_state = sm.on_error("Playback error")

        # Assert
        assert sm.current_state == State.ERROR


class TestErrorState:
    """Test transitions from ERROR state."""

    def test_error_auto_recovers_to_idle_after_timeout(self):
        """Test ERROR → IDLE transition after recovery."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_error("Test error")

        # Act
        new_state = sm.on_error_recovery()

        # Assert
        assert sm.current_state == State.IDLE
        assert new_state == State.IDLE

    def test_button_press_in_error_stays_in_error(self):
        """Test that button press in ERROR state is ignored."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_error("Test error")

        # Act
        new_state = sm.on_button_press()

        # Assert
        assert sm.current_state == State.ERROR


class TestStateHistory:
    """Test state history tracking."""

    def test_state_machine_tracks_previous_state(self):
        """Test that state machine remembers previous state."""
        # Arrange
        sm = StateMachine()

        # Act
        sm.on_button_press()  # IDLE → LOADING

        # Assert
        assert sm.previous_state == State.IDLE
        assert sm.current_state == State.LOADING

    def test_state_transitions_update_previous_state(self):
        """Test that previous state is updated on transition."""
        # Arrange
        sm = StateMachine()

        # Act
        sm.on_button_press()   # IDLE → LOADING
        sm.on_video_ready()     # LOADING → PLAYING

        # Assert
        assert sm.previous_state == State.LOADING
        assert sm.current_state == State.PLAYING


class TestStateCallbacks:
    """Test state change callbacks."""

    def test_state_machine_accepts_callback_on_init(self):
        """Test that state machine can register callback."""
        # Arrange
        mock_callback = Mock()

        # Act
        sm = StateMachine(on_state_change=mock_callback)

        # Assert
        assert sm.on_state_change == mock_callback

    def test_state_change_triggers_callback(self):
        """Test that callback is called on state change."""
        # Arrange
        mock_callback = Mock()
        sm = StateMachine(on_state_change=mock_callback)

        # Act
        sm.on_button_press()  # IDLE → LOADING

        # Assert
        mock_callback.assert_called_once_with(State.IDLE, State.LOADING)

    def test_multiple_state_changes_trigger_multiple_callbacks(self):
        """Test that callback is called for each transition."""
        # Arrange
        mock_callback = Mock()
        sm = StateMachine(on_state_change=mock_callback)

        # Act
        sm.on_button_press()   # IDLE → LOADING
        sm.on_video_ready()     # LOADING → PLAYING
        sm.on_video_end()       # PLAYING → IDLE

        # Assert
        assert mock_callback.call_count == 3
        mock_callback.assert_any_call(State.IDLE, State.LOADING)
        mock_callback.assert_any_call(State.LOADING, State.PLAYING)
        mock_callback.assert_any_call(State.PLAYING, State.IDLE)

    def test_same_state_transition_does_not_trigger_callback(self):
        """Test that staying in same state doesn't trigger callback."""
        # Arrange
        mock_callback = Mock()
        sm = StateMachine(on_state_change=mock_callback)
        sm.on_button_press()  # IDLE → LOADING
        mock_callback.reset_mock()

        # Act
        sm.on_button_press()  # LOADING → LOADING (no change)

        # Assert
        mock_callback.assert_not_called()


class TestStateReset:
    """Test state machine reset functionality."""

    def test_reset_returns_to_idle_state(self):
        """Test that reset() returns to IDLE state."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_video_ready()

        # Act
        sm.reset()

        # Assert
        assert sm.current_state == State.IDLE

    def test_reset_clears_previous_state(self):
        """Test that reset() clears previous state."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_video_ready()

        # Act
        sm.reset()

        # Assert
        assert sm.previous_state is None


class TestGetState:
    """Test state query methods."""

    def test_is_idle_returns_true_in_idle_state(self):
        """Test is_idle() helper method."""
        # Arrange
        sm = StateMachine()

        # Assert
        assert sm.is_idle() is True
        assert sm.is_loading() is False
        assert sm.is_playing() is False
        assert sm.is_error() is False

    def test_is_loading_returns_true_in_loading_state(self):
        """Test is_loading() helper method."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()

        # Assert
        assert sm.is_idle() is False
        assert sm.is_loading() is True
        assert sm.is_playing() is False

    def test_is_playing_returns_true_in_playing_state(self):
        """Test is_playing() helper method."""
        # Arrange
        sm = StateMachine()
        sm.on_button_press()
        sm.on_video_ready()

        # Assert
        assert sm.is_idle() is False
        assert sm.is_loading() is False
        assert sm.is_playing() is True
