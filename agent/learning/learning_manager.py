"""Learning manager that orchestrates the complete learning cycle.

This is the heart of self-improvement - where reflection, memory, and
action come together to create lasting growth.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from agent.state.memory import get_vector_memory, VectorMemory
from agent.learning.reflection_engine import get_reflection_engine, ReflectionEngine
from agent.state.error_memory import ErrorMemory

logger = logging.getLogger(__name__)


class LearningManager:
    """Manager that orchestrates the learning process.

    Combines reflection and memory to enable continuous learning:
    - Reflects on each task execution
    - Stores experiences in vector memory
    - Extracts and stores lessons
    - Retrieves relevant past experiences
    - Tracks improvement over time
    """

    def __init__(
        self,
        vector_memory: Optional[VectorMemory] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
        error_memory: Optional[ErrorMemory] = None
    ):
        """Initialize learning manager.

        Args:
            vector_memory: Vector memory instance
            reflection_engine: Reflection engine instance
            error_memory: Error memory instance
        """
        self.memory = vector_memory or get_vector_memory()
        self.reflection = reflection_engine or get_reflection_engine()
        self.error_memory = error_memory or ErrorMemory()

        logger.info("Learning manager initialized with error learning")

    def learn_from_task(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        errors: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete learning cycle for a task execution.

        This is called after each task to reflect and store lessons.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Final outcome
            success: Whether task succeeded
            errors: Any errors encountered
            context: Additional context

        Returns:
            Learning summary
        """
        errors = errors or []
        context = context or {}

        logger.info(f"Learning from task: {task[:50]}... Success: {success}")

        # Step 1: Reflect on what happened
        reflection_result = self.reflection.reflect_on_task(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            errors=errors,
            context=context
        )

        # Step 2: Store experience in vector memory
        experience_id = self.memory.store_experience(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            metadata={
                "reflection": reflection_result,
                "errors": errors,
                "context": context
            }
        )

        # Step 3: Extract and store lessons
        lessons_stored = []
        for lesson_data in reflection_result.get("lessons", []):
            lesson_id = self.memory.store_lesson(
                lesson=lesson_data["lesson"],
                context=lesson_data["context"],
                category=lesson_data["category"],
                importance=lesson_data["importance"]
            )
            lessons_stored.append(lesson_id)

        # Step 4: Store successful strategies
        strategies_stored = []
        if success:
            # Extract task type
            task_type = self._classify_task_type(task, actions)

            # Determine strategy description
            strategy = self._extract_strategy(actions, reflection_result)

            if strategy:
                strategy_id = self.memory.store_strategy(
                    strategy=strategy,
                    task_type=task_type,
                    success_rate=1.0,
                    context=f"Task: {task[:100]}"
                )
                strategies_stored.append(strategy_id)

        # Step 5: Create learning summary
        learning_summary = {
            "experience_id": experience_id,
            "lessons_count": len(lessons_stored),
            "strategies_count": len(strategies_stored),
            "reflection": reflection_result,
            "improvements_suggested": reflection_result.get("improvements", []),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"Learned: {len(lessons_stored)} lessons, "
            f"{len(strategies_stored)} strategies stored"
        )

        return learning_summary

    def get_relevant_experience(
        self,
        current_task: str,
        n_results: int = 3
    ) -> Dict[str, Any]:
        """Get relevant past experiences for current task.

        Args:
            current_task: Current task description
            n_results: Number of experiences to retrieve

        Returns:
            Dict with experiences, lessons, and strategies
        """
        logger.info(f"Retrieving relevant experience for: {current_task[:50]}...")

        # Get similar past experiences
        similar_experiences = self.memory.recall_similar_experiences(
            query=current_task,
            n_results=n_results
        )

        # Get relevant lessons
        relevant_lessons = self.memory.recall_lessons(
            query=current_task,
            n_results=5
        )

        # Get strategies for this task type
        task_type = self._classify_task_type(current_task, [])
        relevant_strategies = self.memory.recall_strategies(
            task_type=task_type,
            n_results=3
        )

        # Compile insights
        insights = {
            "similar_experiences": similar_experiences,
            "relevant_lessons": relevant_lessons,
            "recommended_strategies": relevant_strategies,
            "experience_summary": self._summarize_experiences(similar_experiences)
        }

        logger.info(
            f"Found {len(similar_experiences)} similar experiences, "
            f"{len(relevant_lessons)} lessons, "
            f"{len(relevant_strategies)} strategies"
        )

        return insights

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about learning progress.

        Returns:
            Learning statistics
        """
        memory_stats = self.memory.get_statistics()

        # Calculate success rate from experiences
        success_rate = 0.0
        if self.memory.available:
            try:
                all_experiences = self.memory.experiences.get()
                if all_experiences and all_experiences.get('metadatas'):
                    total = len(all_experiences['metadatas'])
                    successful = sum(
                        1 for exp in all_experiences['metadatas']
                        if exp.get('success', False)
                    )
                    success_rate = successful / total if total > 0 else 0.0
            except Exception as e:
                logger.warning(f"Could not calculate success rate: {e}")

        stats = {
            **memory_stats,
            "overall_success_rate": success_rate,
            "learning_enabled": self.memory.available,
            "memory_backend": memory_stats.get("backend", "unknown")
        }

        return stats

    def _classify_task_type(self, task: str, actions: List[str]) -> str:
        """Classify task into a type.

        Args:
            task: Task description
            actions: Actions taken

        Returns:
            Task type string
        """
        task_lower = task.lower()
        actions_str = " ".join(actions).lower()

        # Check for specific task types
        if "web" in task_lower or "html" in task_lower or "website" in task_lower:
            return "web_generation"

        elif "file" in task_lower and ("create" in task_lower or "write" in task_lower):
            return "file_creation"

        elif "search" in task_lower or "find" in task_lower:
            return "information_gathering"

        elif "terminal" in actions_str or "command" in task_lower:
            return "terminal_operation"

        elif "pentest" in task_lower or "scan" in task_lower:
            return "security_testing"

        elif "read" in task_lower or "check" in task_lower:
            return "information_retrieval"

        elif "install" in task_lower or "setup" in task_lower:
            return "environment_setup"

        else:
            return "general"

    def _extract_strategy(
        self,
        actions: List[str],
        reflection: Dict[str, Any]
    ) -> Optional[str]:
        """Extract strategy description from successful execution.

        Args:
            actions: Actions taken
            reflection: Reflection result

        Returns:
            Strategy description or None
        """
        if not actions:
            return None

        # Get key actions from reflection
        key_actions = reflection.get("key_actions", [])

        # Get patterns
        patterns = reflection.get("patterns", [])

        # Build strategy description
        strategy_parts = []

        if "read_before_write" in patterns:
            strategy_parts.append("Verify state before modifying")

        if "information_gathering" in patterns:
            strategy_parts.append("Gather information first")

        if len(actions) <= 3:
            strategy_parts.append("Use direct, minimal actions")

        if key_actions:
            # Use the first key action as main strategy
            strategy_parts.append(key_actions[0])

        if strategy_parts:
            return " → ".join(strategy_parts)

        return None

    def _summarize_experiences(
        self,
        experiences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize a list of experiences.

        Args:
            experiences: List of experience dicts

        Returns:
            Summary dict
        """
        if not experiences:
            return {
                "message": "No similar experiences found",
                "success_rate": 0.0,
                "total_count": 0
            }

        successful = sum(1 for exp in experiences if exp.get("success", False))
        total = len(experiences)

        summary = {
            "total_count": total,
            "successful_count": successful,
            "failed_count": total - successful,
            "success_rate": successful / total if total > 0 else 0.0
        }

        # Get common actions from successful experiences
        if successful > 0:
            successful_exps = [e for e in experiences if e.get("success", False)]
            all_actions = []
            for exp in successful_exps:
                all_actions.extend(exp.get("actions", []))

            summary["common_successful_actions"] = list(set(all_actions))[:5]

        return summary

    def get_error_prevention_strategy(
        self,
        tool_name: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get error prevention strategy based on past errors.

        Args:
            tool_name: Tool to use
            operation: Operation to perform
            params: Operation parameters

        Returns:
            Prevention strategy with warnings and validations
        """
        if not self.error_memory:
            return None

        try:
            strategy = self.error_memory.get_prevention_strategy(
                tool_name=tool_name,
                operation=operation,
                params=params
            )
            return strategy
        except Exception as e:
            logger.warning(f"Failed to get error prevention strategy: {e}")
            return None

    def analyze_error_patterns(
        self,
        tool_name: Optional[str] = None,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze error patterns to identify improvement opportunities.

        Args:
            tool_name: Filter by tool name (None = all tools)
            time_window_days: Analyze errors from last N days

        Returns:
            Analysis report with patterns and recommendations
        """
        if not self.error_memory:
            return {"error": "Error memory not initialized"}

        try:
            analysis = self.error_memory.analyze_errors(
                tool_name=tool_name,
                time_window_days=time_window_days
            )

            # Log high-severity recommendations
            if analysis.get("recommendations"):
                high_severity = [
                    r for r in analysis["recommendations"]
                    if r.get("severity") == "high"
                ]
                if high_severity:
                    logger.warning(
                        f"Found {len(high_severity)} high-severity error patterns. "
                        "Review recommendations for improvement."
                    )

            return analysis
        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")
            return {"error": str(e)}

    def learn_from_errors(self) -> Dict[str, Any]:
        """Analyze recent errors and convert them to actionable lessons.

        This method:
        1. Analyzes error patterns
        2. Creates lessons from common errors
        3. Stores prevention strategies

        Returns:
            Summary of learning from errors
        """
        if not self.error_memory:
            return {"message": "Error memory not available"}

        try:
            # Analyze errors from last 7 days
            analysis = self.error_memory.analyze_errors(time_window_days=7)

            if analysis.get("total_errors", 0) == 0:
                return {"message": "No recent errors to learn from"}

            lessons_created = []
            strategies_created = []

            # Convert high-frequency errors to lessons
            for error_type, count in list(analysis.get("top_error_types", {}).items())[:3]:
                if count >= 3:
                    lesson = f"Common error pattern: {error_type[:100]}. Occurred {count} times."
                    lesson_id = self.memory.store_lesson(
                        lesson=lesson,
                        context=f"Error pattern analysis",
                        category="error_prevention",
                        importance=min(count / 10.0, 1.0)  # Scale importance
                    )
                    lessons_created.append(lesson_id)

            # Convert recommendations to strategies
            for rec in analysis.get("recommendations", [])[:5]:
                if rec.get("severity") in ["high", "medium"]:
                    strategy = rec.get("action", "")
                    if strategy:
                        strategy_id = self.memory.store_strategy(
                            strategy=strategy,
                            task_type="error_prevention",
                            success_rate=0.8,  # Conservative estimate
                            context=rec.get("message", "")[:100]
                        )
                        strategies_created.append(strategy_id)

            logger.info(
                f"Learned from errors: {len(lessons_created)} lessons, "
                f"{len(strategies_created)} prevention strategies created"
            )

            return {
                "lessons_created": len(lessons_created),
                "strategies_created": len(strategies_created),
                "total_errors_analyzed": analysis.get("total_errors", 0),
                "recommendations": analysis.get("recommendations", [])
            }

        except Exception as e:
            logger.error(f"Failed to learn from errors: {e}")
            return {"error": str(e)}

    def get_error_summary(self) -> str:
        """Get human-readable error memory summary.

        Returns:
            Summary string
        """
        if not self.error_memory:
            return "Error memory not initialized"

        return self.error_memory.get_summary()

    def export_learning_data(self, output_path: str):
        """Export all learning data to file.

        Args:
            output_path: Path to export file
        """
        from pathlib import Path

        self.memory.export_memory(Path(output_path))
        logger.info(f"Learning data exported to: {output_path}")


# Global instance
_learning_manager: Optional[LearningManager] = None


def get_learning_manager() -> LearningManager:
    """Get or create global learning manager.

    Returns:
        LearningManager instance
    """
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningManager()
    return _learning_manager
