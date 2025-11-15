"""Enhanced Retrieval System - Smart memory retrieval with type-based search.

This module provides intelligent retrieval of different memory types:
- RULES: Always retrieved and injected into system prompt
- FACTS: Retrieved when contextually relevant
- EXPERIENCES: Retrieved semantically based on current task
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedRetrieval:
    """Enhanced retrieval system with type-aware semantic search."""

    def __init__(self, vector_memory=None, rule_engine=None):
        """Initialize enhanced retrieval.

        Args:
            vector_memory: VectorMemory instance
            rule_engine: RuleEngine instance
        """
        self.vector_memory = vector_memory
        self.rule_engine = rule_engine

        # Lazy import to avoid circular dependencies
        if vector_memory is None:
            from agent.state.memory import get_vector_memory
            self.vector_memory = get_vector_memory()

        if rule_engine is None:
            from agent.core.rule_engine import get_rule_engine
            self.rule_engine = get_rule_engine()

    def retrieve_for_task(
        self,
        task: str,
        max_experiences: int = 3,
        max_facts: int = 5,
        max_lessons: int = 3
    ) -> Dict[str, Any]:
        """Retrieve all relevant memory for a task.

        This is the MAIN retrieval method - gets everything needed for reasoning.

        Args:
            task: Current task description
            max_experiences: Max number of experiences to retrieve
            max_facts: Max number of facts to retrieve
            max_lessons: Max number of lessons to retrieve

        Returns:
            Dict with:
            - rules: List of all rules (always ALL rules)
            - facts: List of relevant facts
            - experiences: List of similar experiences
            - lessons: List of relevant lessons
            - strategies: List of proven strategies
        """
        logger.debug(f"Retrieving memory for task: {task[:50]}...")

        result = {
            "rules": [],
            "facts": [],
            "experiences": [],
            "lessons": [],
            "strategies": [],
            "metadata": {
                "retrieved_at": datetime.now().isoformat(),
                "task": task[:100]
            }
        }

        # 1. RULES - Always get ALL rules (they must always be applied)
        try:
            result["rules"] = self._get_all_rules()
        except Exception as e:
            logger.warning(f"Failed to retrieve rules: {e}")

        # 2. FACTS - Get relevant facts
        try:
            result["facts"] = self._get_relevant_facts(task, max_facts)
        except Exception as e:
            logger.warning(f"Failed to retrieve facts: {e}")

        # 3. EXPERIENCES - Semantic search for similar past tasks
        try:
            result["experiences"] = self._get_similar_experiences(task, max_experiences)
        except Exception as e:
            logger.warning(f"Failed to retrieve experiences: {e}")

        # 4. LESSONS - Get relevant lessons learned
        try:
            result["lessons"] = self._get_relevant_lessons(task, max_lessons)
        except Exception as e:
            logger.warning(f"Failed to retrieve lessons: {e}")

        # 5. STRATEGIES - Get proven strategies for this type of task
        try:
            result["strategies"] = self._get_strategies(task)
        except Exception as e:
            logger.warning(f"Failed to retrieve strategies: {e}")

        # Log retrieval stats
        logger.info(
            f"Retrieved: {len(result['rules'])} rules, {len(result['facts'])} facts, "
            f"{len(result['experiences'])} experiences, {len(result['lessons'])} lessons, "
            f"{len(result['strategies'])} strategies"
        )

        return result

    def _get_all_rules(self) -> List[Dict[str, Any]]:
        """Get ALL rules (rules must always be available).

        Returns:
            List of all rules
        """
        if not self.rule_engine:
            return []

        rules = self.rule_engine.get_all_rules()
        return [
            {
                "trigger": rule.trigger,
                "response": rule.response,
                "type": rule.trigger_type,
                "priority": rule.priority
            }
            for rule in rules
        ]

    def _get_relevant_facts(self, task: str, max_results: int) -> List[Dict[str, Any]]:
        """Get facts relevant to the current task.

        Args:
            task: Current task
            max_results: Maximum number of facts

        Returns:
            List of relevant facts
        """
        if not self.vector_memory or not self.vector_memory.available:
            return []

        try:
            # Query facts collection
            results = self.vector_memory.facts.query(
                query_texts=[task],
                n_results=max_results
            )

            facts = []
            if results and results.get('metadatas'):
                for metadata in results['metadatas'][0]:
                    facts.append(metadata)

            return facts

        except Exception as e:
            logger.warning(f"Failed to query facts: {e}")
            return []

    def _get_similar_experiences(self, task: str, max_results: int) -> List[Dict[str, Any]]:
        """Get similar past experiences.

        Args:
            task: Current task
            max_results: Maximum number of experiences

        Returns:
            List of similar experiences
        """
        if not self.vector_memory:
            return []

        try:
            experiences = self.vector_memory.recall_similar_experiences(
                query=task,
                n_results=max_results,
                success_only=False  # Include both successes and failures
            )
            return experiences

        except Exception as e:
            logger.warning(f"Failed to retrieve experiences: {e}")
            return []

    def _get_relevant_lessons(self, task: str, max_results: int) -> List[Dict[str, Any]]:
        """Get relevant lessons learned.

        Args:
            task: Current task
            max_results: Maximum number of lessons

        Returns:
            List of relevant lessons
        """
        if not self.vector_memory:
            return []

        try:
            lessons = self.vector_memory.recall_lessons(
                query=task,
                n_results=max_results
            )
            return lessons

        except Exception as e:
            logger.warning(f"Failed to retrieve lessons: {e}")
            return []

    def _get_strategies(self, task: str) -> List[Dict[str, Any]]:
        """Get proven strategies for this type of task.

        Args:
            task: Current task

        Returns:
            List of strategies
        """
        if not self.vector_memory or not self.vector_memory.available:
            return []

        try:
            # Query strategies collection
            results = self.vector_memory.strategies.query(
                query_texts=[task],
                n_results=3
            )

            strategies = []
            if results and results.get('metadatas'):
                for metadata in results['metadatas'][0]:
                    strategies.append(metadata)

            # Sort by success rate
            strategies.sort(
                key=lambda s: s.get('success_rate', 0) * s.get('usage_count', 1),
                reverse=True
            )

            return strategies

        except Exception as e:
            logger.warning(f"Failed to retrieve strategies: {e}")
            return []

    def format_for_prompt(self, retrieved: Dict[str, Any]) -> str:
        """Format retrieved memory for injection into system prompt.

        Args:
            retrieved: Retrieved memory dict from retrieve_for_task()

        Returns:
            Formatted string for prompt injection
        """
        sections = []

        # RULES section (most important - always first)
        if retrieved.get("rules"):
            sections.append("=" * 70)
            sections.append("🔴 PERMANENT RULES - YOU MUST ALWAYS FOLLOW THESE")
            sections.append("=" * 70)
            sections.append("")

            for i, rule in enumerate(retrieved["rules"], 1):
                trigger_type = rule.get("type", "contains")
                trigger = rule.get("trigger", "")
                response = rule.get("response", "")

                if trigger_type == "exact":
                    condition = f"User says EXACTLY: '{trigger}'"
                elif trigger_type == "contains":
                    condition = f"User input CONTAINS: '{trigger}'"
                else:
                    condition = f"User input MATCHES pattern: {trigger}"

                sections.append(f"RULE {i}:")
                sections.append(f"  WHEN: {condition}")
                sections.append(f"  THEN: {response}")
                sections.append(f"  PRIORITY: {rule.get('priority', 0)}")
                sections.append("")

            sections.append("⚠️  CHECK THESE RULES **BEFORE** ANY OTHER REASONING!")
            sections.append("=" * 70)
            sections.append("")

        # FACTS section
        if retrieved.get("facts"):
            sections.append("📋 KNOWN FACTS ABOUT USER:")
            sections.append("-" * 50)
            for i, fact in enumerate(retrieved["facts"], 1):
                category = fact.get("category", "general")
                value = fact.get("value", fact.get("fact", ""))
                sections.append(f"{i}. [{category.upper()}] {value}")
            sections.append("")

        # EXPERIENCES section
        if retrieved.get("experiences"):
            sections.append("💭 SIMILAR PAST EXPERIENCES:")
            sections.append("-" * 50)
            for i, exp in enumerate(retrieved["experiences"][:3], 1):
                task = exp.get("task", "")[:80]
                outcome = exp.get("outcome", "")[:100]
                success = "✅ SUCCESS" if exp.get("success") else "❌ FAILED"

                sections.append(f"{i}. {success}")
                sections.append(f"   Task: {task}")
                sections.append(f"   Result: {outcome}")
                sections.append("")

        # LESSONS section
        if retrieved.get("lessons"):
            sections.append("💡 LESSONS LEARNED:")
            sections.append("-" * 50)
            for i, lesson in enumerate(retrieved["lessons"][:3], 1):
                lesson_text = lesson.get("lesson", "")
                importance = lesson.get("importance", 0.5)
                stars = "⭐" * min(5, max(1, int(importance * 5)))

                sections.append(f"{i}. {stars} {lesson_text}")
            sections.append("")

        # STRATEGIES section
        if retrieved.get("strategies"):
            sections.append("🎯 PROVEN STRATEGIES:")
            sections.append("-" * 50)
            for i, strategy in enumerate(retrieved["strategies"][:2], 1):
                strategy_text = strategy.get("strategy", "")
                success_rate = strategy.get("success_rate", 0) * 100

                sections.append(f"{i}. [{success_rate:.0f}% success] {strategy_text}")
            sections.append("")

        if not sections:
            return ""

        # Add header and footer
        header = [
            "",
            "╔" + "═" * 68 + "╗",
            "║" + " RETRIEVED MEMORY - USE THIS TO INFORM YOUR REASONING ".center(68) + "║",
            "╚" + "═" * 68 + "╝",
            ""
        ]

        footer = [
            "",
            "=" * 70,
            "⚠️  IMPORTANT:",
            "- ALWAYS check RULES first before any reasoning",
            "- Use FACTS to personalize your response",
            "- Learn from past EXPERIENCES (both successes and failures)",
            "- Apply LESSONS LEARNED to avoid past mistakes",
            "- Use PROVEN STRATEGIES when available",
            "=" * 70,
            ""
        ]

        return "\n".join(header + sections + footer)


# Global instance
_enhanced_retrieval: Optional[EnhancedRetrieval] = None


def get_enhanced_retrieval() -> EnhancedRetrieval:
    """Get or create global enhanced retrieval instance.

    Returns:
        EnhancedRetrieval instance
    """
    global _enhanced_retrieval
    if _enhanced_retrieval is None:
        _enhanced_retrieval = EnhancedRetrieval()
    return _enhanced_retrieval
