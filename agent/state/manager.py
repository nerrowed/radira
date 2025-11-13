"""State management for agent persistence."""

import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class StateManager:
    """Manager for agent state persistence."""

    def __init__(self, storage_backend: str = "file", **kwargs):
        """Initialize state manager.

        Args:
            storage_backend: Backend to use ('file' or 'redis')
            **kwargs: Backend-specific configuration
        """
        self.backend = storage_backend
        self.config = kwargs

        if storage_backend == "redis":
            try:
                import redis
                redis_url = kwargs.get("redis_url", "redis://localhost:6379")
                self.client = redis.from_url(redis_url, decode_responses=True)
                self.client.ping()  # Test connection
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to file storage.")
                self.backend = "file"
                self.client = None
        else:
            self.client = None

        # File storage fallback
        if self.backend == "file":
            self.state_dir = Path(kwargs.get("state_dir", "workspace/.state"))
            self.state_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using file storage at {self.state_dir}")

    def save_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save agent state.

        Args:
            session_id: Session identifier
            state: State dictionary to save

        Returns:
            True if successful
        """
        try:
            # Add metadata
            state["_metadata"] = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "backend": self.backend
            }

            if self.backend == "redis" and self.client:
                # Save to Redis
                key = f"agent:state:{session_id}"
                self.client.set(key, json.dumps(state))
                # Set expiry (24 hours)
                self.client.expire(key, 86400)
                logger.info(f"Saved state to Redis: {session_id}")
            else:
                # Save to file
                state_file = self.state_dir / f"{session_id}.json"
                state_file.write_text(json.dumps(state, indent=2))
                logger.info(f"Saved state to file: {state_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state.

        Args:
            session_id: Session identifier

        Returns:
            State dictionary or None if not found
        """
        try:
            if self.backend == "redis" and self.client:
                # Load from Redis
                key = f"agent:state:{session_id}"
                data = self.client.get(key)
                if data:
                    logger.info(f"Loaded state from Redis: {session_id}")
                    return json.loads(data)
            else:
                # Load from file
                state_file = self.state_dir / f"{session_id}.json"
                if state_file.exists():
                    logger.info(f"Loaded state from file: {state_file}")
                    return json.loads(state_file.read_text())

            logger.warning(f"State not found: {session_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None

    def delete_state(self, session_id: str) -> bool:
        """Delete agent state.

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        try:
            if self.backend == "redis" and self.client:
                key = f"agent:state:{session_id}"
                self.client.delete(key)
                logger.info(f"Deleted state from Redis: {session_id}")
            else:
                state_file = self.state_dir / f"{session_id}.json"
                if state_file.exists():
                    state_file.unlink()
                    logger.info(f"Deleted state file: {state_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete state: {e}")
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions.

        Returns:
            List of session info dicts
        """
        sessions = []

        try:
            if self.backend == "redis" and self.client:
                # List from Redis
                keys = self.client.keys("agent:state:*")
                for key in keys:
                    session_id = key.replace("agent:state:", "")
                    data = self.client.get(key)
                    if data:
                        state = json.loads(data)
                        metadata = state.get("_metadata", {})
                        sessions.append({
                            "session_id": session_id,
                            "timestamp": metadata.get("timestamp"),
                            "backend": "redis"
                        })
            else:
                # List from files
                for state_file in self.state_dir.glob("*.json"):
                    try:
                        state = json.loads(state_file.read_text())
                        metadata = state.get("_metadata", {})
                        sessions.append({
                            "session_id": state_file.stem,
                            "timestamp": metadata.get("timestamp"),
                            "backend": "file"
                        })
                    except Exception as e:
                        logger.warning(f"Failed to read {state_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")

        return sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)

    def clear_all(self) -> bool:
        """Clear all saved states.

        Returns:
            True if successful
        """
        try:
            if self.backend == "redis" and self.client:
                keys = self.client.keys("agent:state:*")
                if keys:
                    self.client.delete(*keys)
                logger.info("Cleared all states from Redis")
            else:
                for state_file in self.state_dir.glob("*.json"):
                    state_file.unlink()
                logger.info("Cleared all state files")

            return True

        except Exception as e:
            logger.error(f"Failed to clear states: {e}")
            return False


# Global instance
_state_manager: Optional[StateManager] = None


def get_state_manager(backend: str = "file", **kwargs) -> StateManager:
    """Get or create global state manager.

    Args:
        backend: Storage backend ('file' or 'redis')
        **kwargs: Backend configuration

    Returns:
        StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        from config.settings import settings
        if backend == "redis" and "redis_url" not in kwargs:
            kwargs["redis_url"] = settings.redis_url
        _state_manager = StateManager(backend=backend, **kwargs)
    return _state_manager
