"""
State machine for managing client UI states.

This module provides a state machine to track the current state of the
client application (IDLE, LOADING, PLAYING, ERROR) and manage transitions
between states.
"""
from enum import Enum, auto
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class State(Enum):
    """Possible states for the client application."""
    IDLE = auto()
    LOADING = auto()
    PLAYING = auto()
    ERROR = auto()


class StateMachine:
    """
    State machine for managing client application state.

    State transitions:
    - IDLE → LOADING: Button pressed
    - LOADING → PLAYING: Video ready to play
    - LOADING → ERROR: Error fetching video
    - PLAYING → IDLE: Video finished
    - PLAYING → ERROR: Error during playback
    - ERROR → IDLE: Error recovered
    """

    def __init__(self, on_state_change: Optional[Callable[[State, State], None]] = None):
        """
        Initialize the state machine.

        Args:
            on_state_change: Optional callback function called when state changes.
                            Receives (old_state, new_state) as arguments.
        """
        self.current_state = State.IDLE
        self.previous_state: Optional[State] = None
        self.on_state_change = on_state_change

    def _transition(self, new_state: State) -> State:
        """
        Internal method to handle state transitions.

        Args:
            new_state: The state to transition to

        Returns:
            The new current state
        """
        if new_state != self.current_state:
            old_state = self.current_state
            self.previous_state = old_state
            self.current_state = new_state

            logger.info(f"State transition: {old_state.name} → {new_state.name}")

            # Call callback if registered
            if self.on_state_change:
                try:
                    self.on_state_change(old_state, new_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}", exc_info=True)

        return self.current_state

    def on_button_press(self) -> State:
        """
        Handle button press event.

        Returns:
            The new state after handling the event
        """
        if self.current_state == State.IDLE:
            # Start loading video
            return self._transition(State.LOADING)
        elif self.current_state == State.LOADING:
            # Ignore button press while loading
            logger.debug("Button press ignored (currently loading)")
            return self.current_state
        elif self.current_state == State.PLAYING:
            # Ignore button press during playback
            logger.debug("Button press ignored (currently playing)")
            return self.current_state
        elif self.current_state == State.ERROR:
            # Ignore button press during error state
            logger.debug("Button press ignored (in error state)")
            return self.current_state

        return self.current_state

    def on_video_ready(self) -> State:
        """
        Handle video ready event (video fetched and ready to play).

        Returns:
            The new state after handling the event
        """
        if self.current_state == State.LOADING:
            return self._transition(State.PLAYING)

        logger.warning(f"Video ready event ignored (current state: {self.current_state.name})")
        return self.current_state

    def on_video_end(self) -> State:
        """
        Handle video end event (video finished playing).

        Returns:
            The new state after handling the event
        """
        if self.current_state == State.PLAYING:
            return self._transition(State.IDLE)

        logger.warning(f"Video end event ignored (current state: {self.current_state.name})")
        return self.current_state

    def on_error(self, error_message: str) -> State:
        """
        Handle error event.

        Args:
            error_message: Description of the error

        Returns:
            The new state after handling the event
        """
        logger.error(f"Error occurred: {error_message}")
        return self._transition(State.ERROR)

    def on_error_recovery(self) -> State:
        """
        Handle error recovery (return to idle state).

        Returns:
            The new state after handling the event
        """
        if self.current_state == State.ERROR:
            logger.info("Recovering from error state")
            return self._transition(State.IDLE)

        return self.current_state

    def reset(self):
        """
        Reset the state machine to initial state.

        This clears all state history and returns to IDLE.
        """
        self.current_state = State.IDLE
        self.previous_state = None
        logger.info("State machine reset to IDLE")

    # Helper methods for state queries
    def is_idle(self) -> bool:
        """Check if currently in IDLE state."""
        return self.current_state == State.IDLE

    def is_loading(self) -> bool:
        """Check if currently in LOADING state."""
        return self.current_state == State.LOADING

    def is_playing(self) -> bool:
        """Check if currently in PLAYING state."""
        return self.current_state == State.PLAYING

    def is_error(self) -> bool:
        """Check if currently in ERROR state."""
        return self.current_state == State.ERROR
