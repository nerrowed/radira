"""Session management for agent conversations."""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .manager import StateManager, get_state_manager

logger = logging.getLogger(__name__)


class Session:
    """Represents an agent conversation session."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        task: Optional[str] = None,
        max_iterations: int = 10
    ):
        """Initialize session.

        Args:
            session_id: Unique session ID (auto-generated if None)
            task: Initial task description
            max_iterations: Maximum iterations for this session
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.task = task
        self.max_iterations = max_iterations
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        # Session state
        self.iteration = 0
        self.history: List[tuple[str, str]] = []  # (action, observation) pairs
        self.metadata: Dict[str, Any] = {}
        self.is_complete = False
        self.result: Optional[str] = None

    def add_step(self, action: str, observation: str):
        """Add a step to session history.

        Args:
            action: Action taken
            observation: Observation/result
        """
        self.history.append((action, observation))
        self.iteration = len(self.history)
        self.updated_at = datetime.now().isoformat()

    def set_result(self, result: str):
        """Set final result and mark complete.

        Args:
            result: Final result
        """
        self.result = result
        self.is_complete = True
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Session state as dict
        """
        return {
            "session_id": self.session_id,
            "task": self.task,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "iteration": self.iteration,
            "history": self.history,
            "metadata": self.metadata,
            "is_complete": self.is_complete,
            "result": self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary.

        Args:
            data: Session state dict

        Returns:
            Session instance
        """
        session = cls(
            session_id=data.get("session_id"),
            task=data.get("task"),
            max_iterations=data.get("max_iterations", 10)
        )
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.iteration = data.get("iteration", 0)
        session.history = data.get("history", [])
        session.metadata = data.get("metadata", {})
        session.is_complete = data.get("is_complete", False)
        session.result = data.get("result")
        return session


class SessionManager:
    """Manager for agent sessions."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        """Initialize session manager.

        Args:
            state_manager: State manager for persistence
        """
        self.state_manager = state_manager or get_state_manager()
        self.current_session: Optional[Session] = None

    def create_session(
        self,
        task: str,
        max_iterations: int = 10,
        session_id: Optional[str] = None
    ) -> Session:
        """Create a new session.

        Args:
            task: Task description
            max_iterations: Max iterations
            session_id: Optional session ID

        Returns:
            New Session instance
        """
        session = Session(
            session_id=session_id,
            task=task,
            max_iterations=max_iterations
        )
        self.current_session = session
        logger.info(f"Created session: {session.session_id}")
        return session

    def save_session(self, session: Optional[Session] = None) -> bool:
        """Save session to storage.

        Args:
            session: Session to save (defaults to current)

        Returns:
            True if successful
        """
        session = session or self.current_session
        if not session:
            logger.warning("No session to save")
            return False

        success = self.state_manager.save_state(
            session.session_id,
            session.to_dict()
        )

        if success:
            logger.info(f"Saved session: {session.session_id}")
        return success

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session from storage.

        Args:
            session_id: Session ID to load

        Returns:
            Loaded Session or None
        """
        state = self.state_manager.load_state(session_id)
        if not state:
            logger.warning(f"Session not found: {session_id}")
            return None

        # Remove metadata added by state manager
        state.pop("_metadata", None)

        session = Session.from_dict(state)
        self.current_session = session
        logger.info(f"Loaded session: {session_id}")
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete session from storage.

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful
        """
        return self.state_manager.delete_state(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions.

        Returns:
            List of session info dicts
        """
        return self.state_manager.list_sessions()

    def resume_session(self, session_id: str) -> Optional[Session]:
        """Resume a session.

        Args:
            session_id: Session ID to resume

        Returns:
            Resumed Session or None
        """
        session = self.load_session(session_id)
        if session and not session.is_complete:
            logger.info(f"Resumed session: {session_id} (iteration {session.iteration})")
            return session
        elif session and session.is_complete:
            logger.warning(f"Session already complete: {session_id}")
            return session
        return None

    def auto_save(self) -> bool:
        """Auto-save current session.

        Returns:
            True if successful
        """
        if self.current_session:
            return self.save_session(self.current_session)
        return False

    def get_current_session(self) -> Optional[Session]:
        """Get current active session.

        Returns:
            Current Session or None
        """
        return self.current_session

    def clear_current_session(self):
        """Clear current session (doesn't delete from storage)."""
        self.current_session = None


# Global instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager.

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
