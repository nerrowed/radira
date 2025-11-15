"""Context Chain Tracking System for AI Agent.

This module tracks the sequence of user commands, AI actions, and results
to maintain contextual awareness of the conversation and decision flow.
This allows the AI to:
- Remember what actions it took and why
- Answer questions about previous actions
- Understand the causal relationship between commands and actions
- Provide context-aware explanations
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextTracker:
    """Tracks context chain of user commands, AI actions, and results.

    This system provides lightweight, efficient tracking of action sequences
    without excessive token usage. It stores both in JSON for quick access
    and in ChromaDB for semantic search capabilities.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize context tracker.

        Args:
            persist_directory: Directory for storing context logs and ChromaDB
        """
        self.persist_directory = persist_directory or str(
            Path("workspace/.context")
        )
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # JSON log file for quick sequential access
        self.log_file = Path(self.persist_directory) / "context_log.json"

        # In-memory cache for recent events (last 100)
        self.recent_events: List[Dict[str, Any]] = []
        self.max_recent_events = 100

        # Load existing log if available
        self._load_log()

        # Try to initialize ChromaDB for semantic search
        self.chroma_available = False
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    chroma_telemetry_impl="none"
                )
            )

            # Create collection for context memory
            self.context_memory = self.client.get_or_create_collection(
                name="context_memory",
                metadata={"description": "Context chain tracking for AI actions"}
            )

            self.chroma_available = True
            logger.info(f"Context tracker initialized with ChromaDB at {self.persist_directory}")

        except ImportError:
            logger.warning(
                "ChromaDB not available for context tracking. "
                "Only JSON logging will be used. "
                "Install with: pip install chromadb"
            )
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using JSON logging only.")

    def _load_log(self):
        """Load existing context log from file."""
        if self.log_file.exists():
            try:
                data = json.loads(self.log_file.read_text())
                self.recent_events = data.get("events", [])[-self.max_recent_events:]
                logger.info(f"Loaded {len(self.recent_events)} recent events from log")
            except Exception as e:
                logger.warning(f"Failed to load context log: {e}")
                self.recent_events = []

    def _save_log(self):
        """Save context log to file."""
        try:
            # Only save recent events to keep file size manageable
            data = {
                "events": self.recent_events[-self.max_recent_events:],
                "last_updated": datetime.now().isoformat()
            }
            self.log_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save context log: {e}")

    def add_event(
        self,
        user_command: str,
        ai_action: str,
        result: str,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new event to the context chain.

        Args:
            user_command: The user's original command or question
            ai_action: The action taken by the AI (tool name or decision)
            result: The result or outcome of the action
            status: Status of the action (success, error, partial, etc.)
            metadata: Additional context (iteration number, tokens used, etc.)

        Returns:
            Event ID
        """
        timestamp = datetime.now().isoformat()
        event_id = f"evt_{datetime.now().timestamp()}"

        # Create event record
        event = {
            "id": event_id,
            "timestamp": timestamp,
            "user_command": user_command,
            "ai_action": ai_action,
            "result": result[:500],  # Limit result length for efficiency
            "status": status,
            "metadata": metadata or {}
        }

        # Add to recent events
        self.recent_events.append(event)

        # Keep only recent events in memory
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events = self.recent_events[-self.max_recent_events:]

        # Save to JSON log
        self._save_log()

        # Store in ChromaDB for semantic search
        if self.chroma_available:
            try:
                document = f"""
                User: {user_command}
                Action: {ai_action}
                Result: {result[:200]}
                Status: {status}
                """

                chroma_metadata = {
                    "timestamp": timestamp,
                    "user_command": user_command[:500],
                    "ai_action": ai_action[:200],
                    "status": status,
                }

                # Add scalar metadata fields
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            chroma_metadata[key] = value

                self.context_memory.add(
                    documents=[document],
                    metadatas=[chroma_metadata],
                    ids=[event_id]
                )
            except Exception as e:
                logger.warning(f"Failed to store event in ChromaDB: {e}")

        logger.debug(f"Added context event: {event_id}")
        return event_id

    def get_last_action(self) -> Optional[Dict[str, Any]]:
        """Get the last action taken by the AI.

        Returns:
            Last event dict or None if no events exist
        """
        if not self.recent_events:
            return None
        return self.recent_events[-1]

    def get_last_n_actions(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the last N actions.

        Args:
            n: Number of actions to retrieve

        Returns:
            List of recent events (most recent last)
        """
        return self.recent_events[-n:] if self.recent_events else []

    def summarize_recent_actions(self, n: int = 5) -> str:
        """Generate a human-readable summary of recent actions.

        Args:
            n: Number of recent actions to summarize

        Returns:
            Summary string explaining recent action chain
        """
        recent = self.get_last_n_actions(n)

        if not recent:
            return "Tidak ada aksi sebelumnya yang tercatat."

        summary_lines = ["Ringkasan aksi terakhir:"]

        for i, event in enumerate(recent, 1):
            timestamp = event.get("timestamp", "")
            user_cmd = event.get("user_command", "N/A")
            action = event.get("ai_action", "N/A")
            status = event.get("status", "unknown")

            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = "unknown"

            # Create readable summary
            status_icon = "✓" if status == "success" else "✗" if status == "error" else "○"
            summary_lines.append(
                f"{i}. [{time_str}] {status_icon} User: '{user_cmd[:50]}...' → "
                f"AI Action: {action}"
            )

        return "\n".join(summary_lines)

    def find_related_context(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Find contextually related past actions using semantic search.

        Args:
            query: Query to search for (e.g., "file operations", "why did you create file")
            n_results: Number of results to return

        Returns:
            List of related events
        """
        if not self.chroma_available:
            # Fallback: simple keyword matching in recent events
            results = []
            query_lower = query.lower()
            for event in reversed(self.recent_events):
                if (query_lower in event.get("user_command", "").lower() or
                    query_lower in event.get("ai_action", "").lower() or
                    query_lower in event.get("result", "").lower()):
                    results.append(event)
                    if len(results) >= n_results:
                        break
            return results

        try:
            # Use ChromaDB semantic search
            search_results = self.context_memory.query(
                query_texts=[query],
                n_results=n_results
            )

            events = []
            if search_results and search_results['metadatas']:
                for metadata in search_results['metadatas'][0]:
                    events.append(metadata)

            return events

        except Exception as e:
            logger.warning(f"ChromaDB search failed: {e}. Using fallback.")
            # Fallback to simple search
            return self.find_related_context(query, n_results)

    def explain_last_action(self) -> str:
        """Generate an explanation of why the last action was taken.

        Returns:
            Explanation string
        """
        last = self.get_last_action()

        if not last:
            return "Belum ada aksi yang dilakukan sebelumnya."

        user_cmd = last.get("user_command", "N/A")
        action = last.get("ai_action", "N/A")
        result = last.get("result", "N/A")
        status = last.get("status", "unknown")

        explanation = f"""
Aksi terakhir:
- Perintah user: "{user_cmd}"
- Aksi yang diambil: {action}
- Hasil: {result[:100]}{"..." if len(result) > 100 else ""}
- Status: {status}

Alasan: Saya mengambil aksi '{action}' sebagai respons terhadap perintah '{user_cmd}'.
        """.strip()

        return explanation

    def get_action_chain(self, start_index: int = 0) -> List[Dict[str, Any]]:
        """Get the full chain of actions from a starting point.

        Args:
            start_index: Index to start from (0 = earliest in recent events)

        Returns:
            List of events forming the action chain
        """
        if start_index < 0:
            start_index = max(0, len(self.recent_events) + start_index)

        return self.recent_events[start_index:]

    def clear_context(self):
        """Clear all context tracking data."""
        self.recent_events = []
        self._save_log()

        if self.chroma_available:
            try:
                # Delete and recreate collection
                self.client.delete_collection("context_memory")
                self.context_memory = self.client.get_or_create_collection(
                    name="context_memory",
                    metadata={"description": "Context chain tracking for AI actions"}
                )
                logger.info("Context memory cleared")
            except Exception as e:
                logger.error(f"Failed to clear ChromaDB context: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get context tracking statistics.

        Returns:
            Dict with statistics
        """
        total_events = len(self.recent_events)

        # Count by status
        status_counts = {}
        for event in self.recent_events:
            status = event.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Get most common actions
        action_counts = {}
        for event in self.recent_events:
            action = event.get("ai_action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        most_common_actions = sorted(
            action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        stats = {
            "total_events": total_events,
            "status_breakdown": status_counts,
            "most_common_actions": dict(most_common_actions),
            "chromadb_available": self.chroma_available,
            "storage_path": str(self.persist_directory)
        }

        if self.chroma_available:
            try:
                stats["chromadb_event_count"] = self.context_memory.count()
            except:
                pass

        return stats


# Global instance
_context_tracker: Optional[ContextTracker] = None


def get_context_tracker() -> ContextTracker:
    """Get or create global context tracker instance.

    Returns:
        ContextTracker instance
    """
    global _context_tracker
    if _context_tracker is None:
        _context_tracker = ContextTracker()
    return _context_tracker
