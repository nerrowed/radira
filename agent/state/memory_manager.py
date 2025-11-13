"""Memory Management System untuk mengelola semua memory di ChromaDB.

Module ini menyediakan tools untuk:
- List, view, add, delete memory
- Manage context memory, experiences, lessons, strategies
- Import/export memory
- Clear dan reset memory
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manager untuk mengelola semua memory di ChromaDB."""

    def __init__(self):
        """Initialize memory manager."""
        from agent.state.context_tracker import get_context_tracker
        from agent.state.memory import get_vector_memory

        self.context_tracker = get_context_tracker()
        self.vector_memory = get_vector_memory()

    # ==================== CONTEXT MEMORY ====================

    def list_context_memory(
        self,
        limit: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List semua context memory.

        Args:
            limit: Batasi jumlah hasil
            status_filter: Filter by status (success, error, completed, incomplete)

        Returns:
            List of context events
        """
        events = self.context_tracker.recent_events

        # Filter by status
        if status_filter:
            events = [e for e in events if e.get('status') == status_filter]

        # Limit results
        if limit:
            events = events[-limit:]

        return events

    def get_context_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get specific context event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event dict or None
        """
        for event in self.context_tracker.recent_events:
            if event.get('id') == event_id:
                return event
        return None

    def delete_context_by_id(self, event_id: str) -> bool:
        """Delete context event by ID.

        Args:
            event_id: Event ID

        Returns:
            True if deleted successfully
        """
        try:
            # Remove from recent events
            self.context_tracker.recent_events = [
                e for e in self.context_tracker.recent_events
                if e.get('id') != event_id
            ]

            # Save updated log
            self.context_tracker._save_log()

            # Remove from ChromaDB if available
            if self.context_tracker.chroma_available:
                try:
                    self.context_tracker.context_memory.delete(ids=[event_id])
                except Exception as e:
                    logger.warning(f"Failed to delete from ChromaDB: {e}")

            logger.info(f"Deleted context event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete context: {e}")
            return False

    def clear_all_context(self) -> bool:
        """Clear all context memory.

        Returns:
            True if cleared successfully
        """
        try:
            self.context_tracker.clear_context()
            logger.info("Cleared all context memory")
            return True
        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return False

    # ==================== EXPERIENCES ====================

    def list_experiences(
        self,
        limit: int = 10,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List experiences from vector memory.

        Args:
            limit: Number of experiences to return
            success_only: Only return successful experiences

        Returns:
            List of experiences
        """
        if not self.vector_memory.available:
            logger.warning("ChromaDB not available")
            return []

        try:
            results = self.vector_memory.experiences.get(limit=limit)

            experiences = []
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if not success_only or metadata.get('success', False):
                        experiences.append(metadata)

            return experiences

        except Exception as e:
            logger.error(f"Failed to list experiences: {e}")
            return []

    def get_experience_by_id(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Get specific experience by ID.

        Args:
            exp_id: Experience ID

        Returns:
            Experience dict or None
        """
        if not self.vector_memory.available:
            return None

        try:
            result = self.vector_memory.experiences.get(ids=[exp_id])
            if result and result['metadatas']:
                return result['metadatas'][0]
        except Exception as e:
            logger.error(f"Failed to get experience: {e}")

        return None

    def delete_experience(self, exp_id: str) -> bool:
        """Delete experience by ID.

        Args:
            exp_id: Experience ID

        Returns:
            True if deleted
        """
        if not self.vector_memory.available:
            logger.warning("ChromaDB not available")
            return False

        try:
            self.vector_memory.experiences.delete(ids=[exp_id])
            logger.info(f"Deleted experience: {exp_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete experience: {e}")
            return False

    def add_experience(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add new experience.

        Args:
            task: Task description
            actions: List of actions taken
            outcome: Final outcome
            success: Whether successful
            metadata: Additional metadata

        Returns:
            Experience ID
        """
        return self.vector_memory.store_experience(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            metadata=metadata
        )

    # ==================== LESSONS ====================

    def list_lessons(
        self,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List lessons learned.

        Args:
            limit: Number of lessons
            category: Filter by category

        Returns:
            List of lessons
        """
        if not self.vector_memory.available:
            logger.warning("ChromaDB not available")
            return []

        try:
            results = self.vector_memory.lessons.get(limit=limit)

            lessons = []
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if not category or metadata.get('category') == category:
                        lessons.append(metadata)

            return lessons

        except Exception as e:
            logger.error(f"Failed to list lessons: {e}")
            return []

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID.

        Args:
            lesson_id: Lesson ID

        Returns:
            True if deleted
        """
        if not self.vector_memory.available:
            return False

        try:
            self.vector_memory.lessons.delete(ids=[lesson_id])
            logger.info(f"Deleted lesson: {lesson_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete lesson: {e}")
            return False

    def add_lesson(
        self,
        lesson: str,
        context: str,
        category: str = "general",
        importance: float = 1.0
    ) -> str:
        """Add new lesson.

        Args:
            lesson: Lesson text
            context: Context where this applies
            category: Category
            importance: Importance (0.0 to 1.0)

        Returns:
            Lesson ID
        """
        return self.vector_memory.store_lesson(
            lesson=lesson,
            context=context,
            category=category,
            importance=importance
        )

    # ==================== STRATEGIES ====================

    def list_strategies(
        self,
        limit: int = 10,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List successful strategies.

        Args:
            limit: Number of strategies
            task_type: Filter by task type

        Returns:
            List of strategies
        """
        if not self.vector_memory.available:
            logger.warning("ChromaDB not available")
            return []

        try:
            results = self.vector_memory.strategies.get(limit=limit)

            strategies = []
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    if not task_type or task_type.lower() in metadata.get('task_type', '').lower():
                        strategies.append(metadata)

            # Sort by success rate
            strategies.sort(
                key=lambda x: x.get('success_rate', 0) * x.get('usage_count', 1),
                reverse=True
            )

            return strategies

        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            return []

    def delete_strategy(self, strategy_id: str) -> bool:
        """Delete strategy by ID.

        Args:
            strategy_id: Strategy ID

        Returns:
            True if deleted
        """
        if not self.vector_memory.available:
            return False

        try:
            self.vector_memory.strategies.delete(ids=[strategy_id])
            logger.info(f"Deleted strategy: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete strategy: {e}")
            return False

    def add_strategy(
        self,
        strategy: str,
        task_type: str,
        success_rate: float = 1.0,
        context: Optional[str] = None
    ) -> str:
        """Add new strategy.

        Args:
            strategy: Strategy description
            task_type: Task type
            success_rate: Success rate (0.0 to 1.0)
            context: Additional context

        Returns:
            Strategy ID
        """
        return self.vector_memory.store_strategy(
            strategy=strategy,
            task_type=task_type,
            success_rate=success_rate,
            context=context
        )

    # ==================== SEARCH & QUERY ====================

    def search_all(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all memory types.

        Args:
            query: Search query
            n_results: Number of results per type

        Returns:
            Dict with results from each memory type
        """
        results = {
            "context": [],
            "experiences": [],
            "lessons": [],
            "strategies": []
        }

        # Search context
        try:
            results["context"] = self.context_tracker.find_related_context(
                query, n_results=n_results
            )
        except Exception as e:
            logger.warning(f"Context search failed: {e}")

        # Search experiences
        try:
            results["experiences"] = self.vector_memory.recall_similar_experiences(
                query, n_results=n_results
            )
        except Exception as e:
            logger.warning(f"Experience search failed: {e}")

        # Search lessons
        try:
            results["lessons"] = self.vector_memory.recall_lessons(
                query, n_results=n_results
            )
        except Exception as e:
            logger.warning(f"Lesson search failed: {e}")

        # Search strategies
        try:
            # For strategies, extract potential task type from query
            results["strategies"] = self.vector_memory.strategies.query(
                query_texts=[query],
                n_results=n_results
            )['metadatas'][0] if self.vector_memory.available else []
        except Exception as e:
            logger.warning(f"Strategy search failed: {e}")

        return results

    # ==================== STATISTICS ====================

    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all memory types.

        Returns:
            Dict with statistics
        """
        stats = {
            "context": self.context_tracker.get_statistics(),
            "vector_memory": self.vector_memory.get_statistics() if self.vector_memory.available else {},
            "timestamp": datetime.now().isoformat()
        }

        return stats

    # ==================== BULK OPERATIONS ====================

    def clear_all_memory(self) -> Dict[str, bool]:
        """Clear ALL memory (WARNING: Cannot be undone!).

        Returns:
            Dict with results for each memory type
        """
        results = {}

        # Clear context
        results['context'] = self.clear_all_context()

        # Clear vector memory collections
        if self.vector_memory.available:
            try:
                # Delete and recreate collections
                self.vector_memory.client.delete_collection("experiences")
                self.vector_memory.experiences = self.vector_memory.client.create_collection("experiences")
                results['experiences'] = True
            except Exception as e:
                logger.error(f"Failed to clear experiences: {e}")
                results['experiences'] = False

            try:
                self.vector_memory.client.delete_collection("lessons_learned")
                self.vector_memory.lessons = self.vector_memory.client.create_collection("lessons_learned")
                results['lessons'] = True
            except Exception as e:
                logger.error(f"Failed to clear lessons: {e}")
                results['lessons'] = False

            try:
                self.vector_memory.client.delete_collection("successful_strategies")
                self.vector_memory.strategies = self.vector_memory.client.create_collection("successful_strategies")
                results['strategies'] = True
            except Exception as e:
                logger.error(f"Failed to clear strategies: {e}")
                results['strategies'] = False

        return results

    def export_all_memory(self, output_file: Path) -> bool:
        """Export all memory to JSON file.

        Args:
            output_file: Path to output file

        Returns:
            True if successful
        """
        try:
            export_data = {
                "context": self.list_context_memory(),
                "experiences": self.list_experiences(limit=1000),
                "lessons": self.list_lessons(limit=1000),
                "strategies": self.list_strategies(limit=1000),
                "statistics": self.get_all_statistics(),
                "exported_at": datetime.now().isoformat()
            }

            output_file.write_text(json.dumps(export_data, indent=2))
            logger.info(f"Memory exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
            return False

    def import_memory(self, input_file: Path) -> Dict[str, int]:
        """Import memory from JSON file.

        Args:
            input_file: Path to input file

        Returns:
            Dict with counts of imported items
        """
        counts = {
            "experiences": 0,
            "lessons": 0,
            "strategies": 0
        }

        try:
            data = json.loads(input_file.read_text())

            # Import experiences
            if "experiences" in data:
                for exp in data["experiences"]:
                    try:
                        self.add_experience(
                            task=exp.get("task", ""),
                            actions=exp.get("actions", []),
                            outcome=exp.get("outcome", ""),
                            success=exp.get("success", False),
                            metadata=exp.get("metadata")
                        )
                        counts["experiences"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to import experience: {e}")

            # Import lessons
            if "lessons" in data:
                for lesson in data["lessons"]:
                    try:
                        self.add_lesson(
                            lesson=lesson.get("lesson", ""),
                            context=lesson.get("context", ""),
                            category=lesson.get("category", "general"),
                            importance=lesson.get("importance", 1.0)
                        )
                        counts["lessons"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to import lesson: {e}")

            # Import strategies
            if "strategies" in data:
                for strategy in data["strategies"]:
                    try:
                        self.add_strategy(
                            strategy=strategy.get("strategy", ""),
                            task_type=strategy.get("task_type", ""),
                            success_rate=strategy.get("success_rate", 1.0),
                            context=strategy.get("context")
                        )
                        counts["strategies"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to import strategy: {e}")

            logger.info(f"Imported memory: {counts}")
            return counts

        except Exception as e:
            logger.error(f"Failed to import memory: {e}")
            return counts


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager instance.

    Returns:
        MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
