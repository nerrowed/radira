"""Self-improvement system that provides actionable recommendations.

This is where I become introspective - analyzing my own performance
and suggesting concrete ways to improve myself.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from agent.state.memory import get_vector_memory, VectorMemory

logger = logging.getLogger(__name__)


class SelfImprovementSuggester:
    """System for generating self-improvement suggestions.

    Analyzes accumulated experiences and provides:
    - Performance analysis
    - Weakness identification
    - Concrete improvement suggestions
    - Progress tracking over time
    """

    def __init__(self, vector_memory: Optional[VectorMemory] = None):
        """Initialize self-improvement suggester.

        Args:
            vector_memory: Vector memory instance
        """
        self.memory = vector_memory or get_vector_memory()

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze overall agent performance.

        Returns:
            Performance analysis dict
        """
        if not self.memory.available:
            return {
                "message": "Memory not available for analysis",
                "suggestions": ["Install ChromaDB for persistent learning: pip install chromadb"]
            }

        try:
            # Get all experiences
            all_experiences = self.memory.experiences.get()

            if not all_experiences or not all_experiences.get('metadatas'):
                return {
                    "message": "Not enough data yet - need to complete more tasks",
                    "total_experiences": 0,
                    "error": False
                }

            experiences = all_experiences['metadatas']
            total = len(experiences)

            # Calculate metrics
            successful = sum(1 for exp in experiences if exp.get('success', False))
            failed = total - successful
            success_rate = successful / total if total > 0 else 0.0

            # Analyze failures
            failure_patterns = self._analyze_failures(experiences)

            # Analyze successes
            success_patterns = self._analyze_successes(experiences)

            # Get efficiency metrics
            efficiency = self._calculate_efficiency(experiences)

            analysis = {
                "total_experiences": total,
                "successful": successful,
                "failed": failed,
                "success_rate": success_rate,
                "failure_patterns": failure_patterns,
                "success_patterns": success_patterns,
                "efficiency_metrics": efficiency,
                "timestamp": datetime.now().isoformat()
            }

            return analysis

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {
                "message": f"Analysis failed: {str(e)}",
                "error": True
            }

    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Generate concrete improvement suggestions.

        Returns:
            List of suggestion dicts with priority and actionability
        """
        analysis = self.analyze_performance()

        if analysis.get("error") or analysis.get("total_experiences", 0) == 0:
            return [
                {
                    "suggestion": "Complete more tasks to gather learning data",
                    "priority": "high",
                    "category": "data_collection",
                    "actionable": True
                }
            ]

        suggestions = []

        # Analyze success rate
        success_rate = analysis.get("success_rate", 0.0)

        if success_rate < 0.5:
            suggestions.append({
                "suggestion": "Low success rate detected. Consider breaking down complex tasks into smaller steps",
                "priority": "critical",
                "category": "strategy",
                "actionable": True,
                "current_metric": f"Success rate: {success_rate:.1%}"
            })

        elif success_rate < 0.7:
            suggestions.append({
                "suggestion": "Moderate success rate. Focus on information gathering before taking actions",
                "priority": "high",
                "category": "strategy",
                "actionable": True,
                "current_metric": f"Success rate: {success_rate:.1%}"
            })

        # Analyze failure patterns
        failure_patterns = analysis.get("failure_patterns", {})
        common_errors = failure_patterns.get("common_error_types", {})

        if "not_found" in common_errors and common_errors["not_found"] > 2:
            suggestions.append({
                "suggestion": "Frequently encountering 'not found' errors. Always verify file/resource existence before operations",
                "priority": "high",
                "category": "error_prevention",
                "actionable": True,
                "occurrences": common_errors["not_found"]
            })

        if "permission" in common_errors and common_errors["permission"] > 1:
            suggestions.append({
                "suggestion": "Permission errors detected. Check file/directory permissions before operations",
                "priority": "medium",
                "category": "error_prevention",
                "actionable": True,
                "occurrences": common_errors["permission"]
            })

        if "rate_limit" in common_errors:
            suggestions.append({
                "suggestion": "Rate limit errors detected. Consider adding more delays between iterations",
                "priority": "high",
                "category": "optimization",
                "actionable": True,
                "occurrences": common_errors["rate_limit"]
            })

        # Analyze efficiency
        efficiency = analysis.get("efficiency_metrics", {})
        avg_actions = efficiency.get("avg_actions_per_task", 0)

        if avg_actions > 8:
            suggestions.append({
                "suggestion": "Tasks taking many actions. Look for opportunities to combine operations",
                "priority": "medium",
                "category": "efficiency",
                "actionable": True,
                "current_metric": f"Avg actions per task: {avg_actions:.1f}"
            })

        # Success pattern insights
        success_patterns = analysis.get("success_patterns", {})
        if success_patterns.get("information_gathering_helps"):
            suggestions.append({
                "suggestion": "Information gathering correlates with success. Always search/read before acting",
                "priority": "medium",
                "category": "best_practice",
                "actionable": True
            })

        # If no specific suggestions, provide general guidance
        if not suggestions and success_rate > 0.7:
            suggestions.append({
                "suggestion": "Performance is good! Focus on maintaining consistency and learning from any failures",
                "priority": "low",
                "category": "maintenance",
                "actionable": True,
                "current_metric": f"Success rate: {success_rate:.1%}"
            })

        return sorted(suggestions, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]])

    def get_learning_progress_report(self) -> Dict[str, Any]:
        """Generate learning progress report.

        Returns:
            Progress report dict
        """
        stats = self.memory.get_statistics()
        analysis = self.analyze_performance()

        report = {
            "memory_stats": stats,
            "performance_analysis": analysis,
            "improvement_suggestions": self.get_improvement_suggestions(),
            "learning_enabled": self.memory.available,
            "timestamp": datetime.now().isoformat()
        }

        return report

    def _analyze_failures(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failure patterns.

        Args:
            experiences: List of experience dicts

        Returns:
            Failure analysis
        """
        failures = [exp for exp in experiences if not exp.get('success', False)]

        if not failures:
            return {"message": "No failures to analyze"}

        # Extract error types from metadata
        error_types = {}
        for failure in failures:
            metadata = failure.get('metadata', {})
            errors = metadata.get('errors', [])

            for error in errors:
                error_lower = str(error).lower()

                if "not found" in error_lower or "no such" in error_lower:
                    error_types["not_found"] = error_types.get("not_found", 0) + 1
                elif "permission" in error_lower or "denied" in error_lower:
                    error_types["permission"] = error_types.get("permission", 0) + 1
                elif "timeout" in error_lower:
                    error_types["timeout"] = error_types.get("timeout", 0) + 1
                elif "rate limit" in error_lower or "429" in error_lower:
                    error_types["rate_limit"] = error_types.get("rate_limit", 0) + 1
                elif "syntax" in error_lower or "invalid" in error_lower:
                    error_types["syntax"] = error_types.get("syntax", 0) + 1

        return {
            "total_failures": len(failures),
            "failure_rate": len(failures) / len(experiences),
            "common_error_types": error_types
        }

    def _analyze_successes(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze success patterns.

        Args:
            experiences: List of experience dicts

        Returns:
            Success analysis
        """
        successes = [exp for exp in experiences if exp.get('success', False)]

        if not successes:
            return {"message": "No successes to analyze yet"}

        # Count common patterns
        patterns = {
            "information_gathering": 0,
            "direct_approach": 0,
            "multi_step": 0
        }

        for success in successes:
            actions = success.get('actions', [])
            actions_str = " ".join(str(a) for a in actions).lower()

            if "search" in actions_str or "list" in actions_str or "read" in actions_str:
                patterns["information_gathering"] += 1

            if len(actions) <= 3:
                patterns["direct_approach"] += 1

            if len(actions) > 3:
                patterns["multi_step"] += 1

        # Calculate insights
        total_successes = len(successes)
        insights = {
            "total_successes": total_successes,
            "information_gathering_rate": patterns["information_gathering"] / total_successes,
            "direct_approach_rate": patterns["direct_approach"] / total_successes,
            "multi_step_rate": patterns["multi_step"] / total_successes
        }

        # Add boolean flags for easy access
        insights["information_gathering_helps"] = insights["information_gathering_rate"] > 0.5

        return insights

    def _calculate_efficiency(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate efficiency metrics.

        Args:
            experiences: List of experience dicts

        Returns:
            Efficiency metrics
        """
        if not experiences:
            return {}

        # Calculate average actions per task
        action_counts = []
        for exp in experiences:
            actions = exp.get('actions', [])
            action_counts.append(len(actions))

        avg_actions = sum(action_counts) / len(action_counts)

        # Calculate efficiency for successes vs failures
        successes = [exp for exp in experiences if exp.get('success', False)]
        failures = [exp for exp in experiences if not exp.get('success', False)]

        avg_actions_success = 0
        avg_actions_failure = 0

        if successes:
            success_actions = [len(exp.get('actions', [])) for exp in successes]
            avg_actions_success = sum(success_actions) / len(success_actions)

        if failures:
            failure_actions = [len(exp.get('actions', [])) for exp in failures]
            avg_actions_failure = sum(failure_actions) / len(failure_actions)

        return {
            "avg_actions_per_task": avg_actions,
            "avg_actions_when_successful": avg_actions_success,
            "avg_actions_when_failed": avg_actions_failure,
            "efficiency_rating": "high" if avg_actions <= 4 else ("medium" if avg_actions <= 7 else "low")
        }


# Global instance
_self_improvement_suggester: Optional[SelfImprovementSuggester] = None


def get_self_improvement_suggester() -> SelfImprovementSuggester:
    """Get or create global self-improvement suggester.

    Returns:
        SelfImprovementSuggester instance
    """
    global _self_improvement_suggester
    if _self_improvement_suggester is None:
        _self_improvement_suggester = SelfImprovementSuggester()
    return _self_improvement_suggester
