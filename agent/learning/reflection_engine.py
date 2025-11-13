"""Reflection engine for analyzing task outcomes and extracting insights.

This is where I look back at what I've done, understand what worked,
what didn't, and why. True learning comes from reflection.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """Engine for reflecting on task execution and extracting lessons.

    This allows the agent to:
    - Analyze what went right and wrong
    - Extract actionable lessons
    - Identify patterns in successes and failures
    - Suggest improvements for future tasks
    """

    def __init__(self, llm_client=None):
        """Initialize reflection engine.

        Args:
            llm_client: Optional LLM client for deep analysis
        """
        self.llm_client = llm_client

    def reflect_on_task(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        errors: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Reflect on a completed task execution.

        Args:
            task: Original task description
            actions: List of actions taken
            outcome: Final outcome/result
            success: Whether task succeeded
            errors: Any errors encountered
            context: Additional context

        Returns:
            Dict with reflection insights
        """
        errors = errors or []
        context = context or {}

        # Basic reflection
        reflection = {
            "task": task,
            "success": success,
            "action_count": len(actions),
            "had_errors": len(errors) > 0,
            "timestamp": datetime.now().isoformat()
        }

        # Analyze what happened
        if success:
            reflection.update(self._analyze_success(task, actions, outcome, context))
        else:
            reflection.update(self._analyze_failure(task, actions, errors, context))

        # Extract patterns
        reflection["patterns"] = self._identify_patterns(actions, success)

        # Generate lessons
        reflection["lessons"] = self._extract_lessons(
            task, actions, outcome, success, errors, context
        )

        # Suggest improvements
        reflection["improvements"] = self._suggest_improvements(
            task, actions, success, errors
        )

        logger.info(f"Reflected on task: {task[:50]}... Success: {success}")

        return reflection

    def _analyze_success(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze successful task execution.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Result
            context: Context

        Returns:
            Analysis dict
        """
        analysis = {
            "success_factors": [],
            "key_actions": [],
            "efficiency_score": 0.0
        }

        # Identify key successful actions
        for action in actions:
            action_lower = action.lower()

            # File operations that succeeded
            if "write" in action_lower or "create" in action_lower:
                analysis["key_actions"].append(f"Successfully created/wrote content")

            # Terminal commands that worked
            elif "terminal" in action_lower:
                analysis["key_actions"].append(f"Executed terminal command effectively")

            # Web generation
            elif "web" in action_lower or "html" in action_lower:
                analysis["key_actions"].append(f"Generated web content")

        # Calculate efficiency (fewer actions = more efficient)
        if len(actions) <= 3:
            analysis["efficiency_score"] = 1.0
            analysis["success_factors"].append("Completed efficiently with minimal actions")
        elif len(actions) <= 6:
            analysis["efficiency_score"] = 0.7
            analysis["success_factors"].append("Completed with reasonable number of actions")
        else:
            analysis["efficiency_score"] = 0.4
            analysis["success_factors"].append("Task required many actions")

        # Check for good practices
        if "search" in str(actions).lower():
            analysis["success_factors"].append("Used search to gather information first")

        return analysis

    def _analyze_failure(
        self,
        task: str,
        actions: List[str],
        errors: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze failed task execution.

        Args:
            task: Task description
            actions: Actions taken
            errors: Errors encountered
            context: Context

        Returns:
            Analysis dict
        """
        analysis = {
            "failure_reasons": [],
            "error_types": [],
            "action_sequence_issues": []
        }

        # Categorize errors
        for error in errors:
            error_lower = error.lower()

            if "permission" in error_lower or "denied" in error_lower:
                analysis["error_types"].append("permission_error")
                analysis["failure_reasons"].append("Insufficient permissions for operation")

            elif "not found" in error_lower or "no such" in error_lower:
                analysis["error_types"].append("resource_not_found")
                analysis["failure_reasons"].append("Required resource/file not found")

            elif "timeout" in error_lower:
                analysis["error_types"].append("timeout")
                analysis["failure_reasons"].append("Operation timed out")

            elif "syntax" in error_lower or "invalid" in error_lower:
                analysis["error_types"].append("syntax_error")
                analysis["failure_reasons"].append("Invalid syntax or parameters")

            elif "rate limit" in error_lower or "429" in error_lower:
                analysis["error_types"].append("rate_limit")
                analysis["failure_reasons"].append("Hit API rate limits")

            else:
                analysis["error_types"].append("unknown")

        # Check action sequence
        if len(actions) < 2:
            analysis["action_sequence_issues"].append("Too few actions attempted")

        # Check if tried to verify before action
        actions_str = " ".join(actions).lower()
        if "write" in actions_str or "create" in actions_str:
            if "read" not in actions_str and "list" not in actions_str:
                analysis["action_sequence_issues"].append(
                    "Didn't verify file/directory existence before writing"
                )

        return analysis

    def _identify_patterns(
        self,
        actions: List[str],
        success: bool
    ) -> List[str]:
        """Identify patterns in action sequences.

        Args:
            actions: List of actions
            success: Whether successful

        Returns:
            List of identified patterns
        """
        patterns = []
        actions_str = " ".join(actions).lower()

        # Pattern: Read before write
        if "read" in actions_str and "write" in actions_str:
            if actions_str.index("read") < actions_str.index("write"):
                patterns.append("read_before_write")

        # Pattern: Search before action
        if "search" in actions_str:
            patterns.append("information_gathering")

        # Pattern: Multiple retries
        action_types = [a.split()[0] if " " in a else a for a in actions]
        if len(action_types) != len(set(action_types)):
            patterns.append("retry_pattern")

        # Pattern: Sequential execution
        if len(actions) >= 3:
            patterns.append("multi_step_process")

        return patterns

    def _extract_lessons(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        errors: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract actionable lessons from execution.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Result
            success: Success status
            errors: Errors
            context: Context

        Returns:
            List of lessons
        """
        lessons = []

        if success:
            # Lesson from success
            if len(actions) <= 3:
                lessons.append({
                    "lesson": "Simple tasks can be solved with direct, minimal actions",
                    "category": "efficiency",
                    "importance": 0.7,
                    "context": f"Task '{task[:50]}...' succeeded with {len(actions)} actions"
                })

            # Check for good patterns
            actions_str = " ".join(actions).lower()
            if "search" in actions_str or "list" in actions_str:
                lessons.append({
                    "lesson": "Gathering information before acting leads to success",
                    "category": "strategy",
                    "importance": 0.8,
                    "context": "Used information gathering before main action"
                })

        else:
            # Lessons from failure
            for error in errors:
                error_lower = error.lower()

                if "not found" in error_lower:
                    lessons.append({
                        "lesson": "Always verify file/resource existence before operations",
                        "category": "error_prevention",
                        "importance": 0.9,
                        "context": f"Failed due to missing resource: {error[:100]}"
                    })

                elif "permission" in error_lower:
                    lessons.append({
                        "lesson": "Check permissions before attempting operations",
                        "category": "error_prevention",
                        "importance": 0.8,
                        "context": "Permission denied error"
                    })

                elif "rate limit" in error_lower:
                    lessons.append({
                        "lesson": "Need to pace API calls to avoid rate limits",
                        "category": "optimization",
                        "importance": 0.9,
                        "context": "Hit rate limit during execution"
                    })

        return lessons

    def _suggest_improvements(
        self,
        task: str,
        actions: List[str],
        success: bool,
        errors: List[str]
    ) -> List[str]:
        """Suggest improvements for future similar tasks.

        Args:
            task: Task description
            actions: Actions taken
            success: Success status
            errors: Errors

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        if success:
            # Even success can be improved
            if len(actions) > 5:
                suggestions.append(
                    "Consider if some actions could be combined or eliminated"
                )
        else:
            # Improvement suggestions from failure
            actions_str = " ".join(actions).lower()

            if "read" not in actions_str and "list" not in actions_str:
                suggestions.append(
                    "Start by listing/reading to understand current state"
                )

            if any("not found" in e.lower() for e in errors):
                suggestions.append(
                    "Add file existence checks before file operations"
                )

            if any("permission" in e.lower() for e in errors):
                suggestions.append(
                    "Verify permissions or use alternative approaches"
                )

            if len(actions) < 3:
                suggestions.append(
                    "Try breaking down the task into more granular steps"
                )

        return suggestions

    def compare_attempts(
        self,
        similar_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare multiple attempts at similar tasks.

        Args:
            similar_tasks: List of task execution data

        Returns:
            Comparison analysis
        """
        if not similar_tasks:
            return {"message": "No tasks to compare"}

        successes = [t for t in similar_tasks if t.get("success", False)]
        failures = [t for t in similar_tasks if not t.get("success", False)]

        comparison = {
            "total_attempts": len(similar_tasks),
            "success_rate": len(successes) / len(similar_tasks),
            "common_success_patterns": [],
            "common_failure_patterns": []
        }

        # Find common patterns in successes
        if successes:
            avg_actions_success = sum(
                len(t.get("actions", [])) for t in successes
            ) / len(successes)
            comparison["avg_actions_when_successful"] = avg_actions_success

        # Find common patterns in failures
        if failures:
            failure_errors = []
            for task in failures:
                failure_errors.extend(task.get("errors", []))

            # Most common error types
            error_types = {}
            for error in failure_errors:
                error_lower = error.lower()
                if "not found" in error_lower:
                    error_types["not_found"] = error_types.get("not_found", 0) + 1
                elif "permission" in error_lower:
                    error_types["permission"] = error_types.get("permission", 0) + 1

            comparison["common_error_types"] = error_types

        return comparison


# Global instance
_reflection_engine: Optional[ReflectionEngine] = None


def get_reflection_engine(llm_client=None) -> ReflectionEngine:
    """Get or create global reflection engine.

    Args:
        llm_client: Optional LLM client

    Returns:
        ReflectionEngine instance
    """
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = ReflectionEngine(llm_client=llm_client)
    return _reflection_engine
