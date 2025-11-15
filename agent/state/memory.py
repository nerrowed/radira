"""Vector memory system for long-term learning and experience storage.

This is the foundation of reflective learning - where I remember,
reflect, and grow from every interaction.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorMemory:
    """Vector-based long-term memory for storing and retrieving experiences.

    This allows the agent to:
    - Remember past successes and failures
    - Find similar situations from history
    - Learn patterns over time
    - Improve decision-making based on experience
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize vector memory.

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory or str(
            Path("workspace/.memory")
        )
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Try to import and initialize ChromaDB
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

            # Create collections for different types of memories
            self.experiences = self.client.get_or_create_collection(
                name="experiences",
                metadata={"description": "Task execution experiences"}
            )

            self.lessons = self.client.get_or_create_collection(
                name="lessons_learned",
                metadata={"description": "Extracted lessons and insights"}
            )

            self.strategies = self.client.get_or_create_collection(
                name="successful_strategies",
                metadata={"description": "Strategies that worked well"}
            )

            self.available = True
            logger.info(f"Vector memory initialized at {self.persist_directory}")

        except ImportError:
            logger.warning(
                "ChromaDB not available. Install with: pip install chromadb. "
                "Falling back to simple in-memory storage."
            )
            self.client = None
            self.available = False
            # Fallback to simple dict storage
            self._memory_fallback = {
                "experiences": [],
                "lessons": [],
                "strategies": []
            }

    def store_experience(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a task execution experience.

        Args:
            task: Original task description
            actions: List of actions taken
            outcome: Final outcome
            success: Whether task succeeded
            metadata: Additional context

        Returns:
            Experience ID
        """
        # ChromaDB metadata doesn't support lists, convert to string
        actions_str = "; ".join(actions) if actions else "no_actions"

        # Store full data including list for retrieval
        full_experience = {
            "task": task,
            "actions": actions,  # Keep as list
            "outcome": outcome,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        # ChromaDB metadata (only scalar values)
        chroma_metadata = {
            "task": task[:500],  # Limit length
            "actions_str": actions_str[:500],  # String version for ChromaDB
            "outcome": outcome[:500],
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "action_count": len(actions)
        }

        # Add custom metadata fields if they're scalar
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)) and key not in chroma_metadata:
                    chroma_metadata[key] = value

        experience_id = f"exp_{datetime.now().timestamp()}"

        # Create searchable document
        document = f"""
        Task: {task}
        Actions: {actions_str}
        Outcome: {outcome}
        Success: {success}
        """

        if self.available:
            self.experiences.add(
                documents=[document],
                metadatas=[chroma_metadata],  # Use scalar-only metadata
                ids=[experience_id]
            )
        else:
            self._memory_fallback["experiences"].append({
                "id": experience_id,
                "document": document,
                "metadata": full_experience
            })

        logger.info(f"Stored experience: {experience_id}")
        return experience_id

    def store_lesson(
        self,
        lesson: str,
        context: str,
        category: str = "general",
        importance: float = 1.0
    ) -> str:
        """Store a learned lesson.

        Args:
            lesson: The lesson learned
            context: Context where this applies
            category: Lesson category
            importance: Importance score (0.0 to 1.0)

        Returns:
            Lesson ID
        """
        lesson_data = {
            "lesson": lesson,
            "context": context,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }

        lesson_id = f"lesson_{datetime.now().timestamp()}"

        document = f"{lesson}\nContext: {context}\nCategory: {category}"

        if self.available:
            self.lessons.add(
                documents=[document],
                metadatas=[lesson_data],
                ids=[lesson_id]
            )
        else:
            self._memory_fallback["lessons"].append({
                "id": lesson_id,
                "document": document,
                "metadata": lesson_data
            })

        logger.info(f"Learned: {lesson}")
        return lesson_id

    def store_strategy(
        self,
        strategy: str,
        task_type: str,
        success_rate: float = 1.0,
        context: Optional[str] = None
    ) -> str:
        """Store a successful strategy.

        Args:
            strategy: Description of the strategy
            task_type: Type of task this applies to
            success_rate: How often this works (0.0 to 1.0)
            context: Additional context

        Returns:
            Strategy ID
        """
        strategy_data = {
            "strategy": strategy,
            "task_type": task_type,
            "success_rate": success_rate,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "usage_count": 1
        }

        strategy_id = f"strat_{datetime.now().timestamp()}"

        document = f"Strategy: {strategy}\nTask Type: {task_type}\nContext: {context or ''}"

        if self.available:
            self.strategies.add(
                documents=[document],
                metadatas=[strategy_data],
                ids=[strategy_id]
            )
        else:
            self._memory_fallback["strategies"].append({
                "id": strategy_id,
                "document": document,
                "metadata": strategy_data
            })

        logger.info(f"Stored strategy for {task_type}")
        return strategy_id

    def recall_similar_experiences(
        self,
        query: str,
        n_results: int = 3,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Find similar past experiences.

        Args:
            query: Query to search for
            n_results: Number of results to return
            success_only: Only return successful experiences

        Returns:
            List of similar experiences
        """
        if self.available:
            results = self.experiences.query(
                query_texts=[query],
                n_results=n_results
            )

            experiences = []
            if results and results['metadatas']:
                for metadata in results['metadatas'][0]:
                    if not success_only or metadata.get('success', False):
                        experiences.append(metadata)

            return experiences
        else:
            # Fallback: simple text matching
            experiences = []
            for exp in self._memory_fallback["experiences"]:
                if query.lower() in exp["document"].lower():
                    if not success_only or exp["metadata"].get('success', False):
                        experiences.append(exp["metadata"])
                        if len(experiences) >= n_results:
                            break
            return experiences

    def recall_lessons(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall relevant lessons.

        Args:
            query: What to search for
            n_results: Number of lessons
            category: Filter by category

        Returns:
            List of relevant lessons
        """
        if self.available:
            results = self.lessons.query(
                query_texts=[query],
                n_results=n_results
            )

            lessons = []
            if results and results['metadatas']:
                for metadata in results['metadatas'][0]:
                    if not category or metadata.get('category') == category:
                        lessons.append(metadata)

            return lessons
        else:
            lessons = []
            for lesson in self._memory_fallback["lessons"]:
                if query.lower() in lesson["document"].lower():
                    if not category or lesson["metadata"].get('category') == category:
                        lessons.append(lesson["metadata"])
                        if len(lessons) >= n_results:
                            break
            return lessons

    def recall_strategies(
        self,
        task_type: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Recall successful strategies for a task type.

        Args:
            task_type: Type of task
            n_results: Number of strategies

        Returns:
            List of strategies
        """
        query = f"task type: {task_type}"

        if self.available:
            results = self.strategies.query(
                query_texts=[query],
                n_results=n_results
            )

            strategies = []
            if results and results['metadatas']:
                strategies = results['metadatas'][0]

            return sorted(
                strategies,
                key=lambda x: x.get('success_rate', 0) * x.get('usage_count', 1),
                reverse=True
            )
        else:
            strategies = []
            for strat in self._memory_fallback["strategies"]:
                if task_type.lower() in strat["document"].lower():
                    strategies.append(strat["metadata"])
                    if len(strategies) >= n_results:
                        break
            return strategies

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dict with memory stats
        """
        if self.available:
            return {
                "total_experiences": self.experiences.count(),
                "total_lessons": self.lessons.count(),
                "total_strategies": self.strategies.count(),
                "storage_path": self.persist_directory,
                "backend": "chromadb"
            }
        else:
            return {
                "total_experiences": len(self._memory_fallback["experiences"]),
                "total_lessons": len(self._memory_fallback["lessons"]),
                "total_strategies": len(self._memory_fallback["strategies"]),
                "storage_path": self.persist_directory,
                "backend": "fallback"
            }

    def export_memory(self, output_file: Path):
        """Export all memories to JSON file.

        Args:
            output_file: Path to export file
        """
        if self.available:
            export_data = {
                "experiences": self.experiences.get()['metadatas'],
                "lessons": self.lessons.get()['metadatas'],
                "strategies": self.strategies.get()['metadatas']
            }
        else:
            export_data = {
                "experiences": [e["metadata"] for e in self._memory_fallback["experiences"]],
                "lessons": [l["metadata"] for l in self._memory_fallback["lessons"]],
                "strategies": [s["metadata"] for s in self._memory_fallback["strategies"]]
            }

        output_file.write_text(json.dumps(export_data, indent=2))
        logger.info(f"Memory exported to {output_file}")


# Global instance
_vector_memory: Optional[VectorMemory] = None


def get_vector_memory() -> VectorMemory:
    """Get or create global vector memory instance.

    Returns:
        VectorMemory instance
    """
    global _vector_memory
    if _vector_memory is None:
        _vector_memory = VectorMemory()
    return _vector_memory
