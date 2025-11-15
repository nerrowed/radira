"""Task Importance Filter - Prevents trivial tasks from triggering learning.

This filter uses multiple strategies to identify trivial tasks:
1. Regex-based detection for short confirmations and greetings
2. Semantic-based detection using task classifier
3. Metric-based analysis (action count, outcome complexity, etc.)

Only meaningful tasks that contain multi-step reasoning, problem-solving,
decision-making, or analysis should trigger reflection and learning.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from agent.core.task_classifier import get_task_classifier, TaskType

logger = logging.getLogger(__name__)


class ImportanceLevel(Enum):
    """Importance levels for tasks."""
    TRIVIAL = "trivial"  # Should NOT trigger learning
    LOW = "low"  # Borderline, likely skip
    MEDIUM = "medium"  # Should trigger learning
    HIGH = "high"  # Definitely trigger learning


class TaskImportanceFilter:
    """Filter that determines if a task is important enough for learning.

    This prevents noise in the memory system by filtering out:
    - Short confirmations ("ya", "oke", "lanjut", "no 1 menarik")
    - Greetings and pleasantries
    - Trivial questions
    - Single-action tasks with no complexity
    - Simple conversational exchanges
    """

    # Regex patterns for trivial tasks (case-insensitive)
    TRIVIAL_PATTERNS = [
        # Short confirmations (Indonesian & English)
        r'^\s*(ya|yes|yep|yup|ok|oke|okay|baik|sip|siap)\s*$',
        r'^\s*(no|tidak|nggak|gak|nope)\s*$',
        r'^\s*(lanjut|next|continue|proceed|gas|go)\s*$',
        r'^\s*(stop|berhenti|halt|cancel|batal)\s*$',

        # Agreement expressions
        r'^\s*(setuju|agree|understood|mengerti|paham)\s*$',
        r'^\s*(benar|betul|correct|right|tepat)\s*$',
        r'^\s*(salah|wrong|incorrect)\s*$',

        # Acknowledgments
        r'^\s*(thanks|terima kasih|makasih|thx|ty)\s*$',
        r'^\s*(maaf|sorry|excuse me)\s*$',

        # Greetings
        r'^\s*(halo|hai|hello|hi|hey|hei)\s*$',
        r'^\s*(selamat pagi|selamat siang|selamat malam|good morning|good evening)\s*$',
        r'^\s*(bye|goodbye|sampai jumpa|dadah)\s*$',

        # Simple number/item selections
        r'^\s*(no|nomor|number)?\s*[0-9]+\s*(menarik|aja|saja)?\s*$',
        r'^\s*pilih\s*[0-9]+\s*$',
        r'^\s*yang\s*(pertama|kedua|ketiga|ini|itu)\s*$',

        # Very short responses (1-3 words, non-technical)
        r'^\s*\w{1,15}\s*$',  # Single word
        r'^\s*\w{1,15}\s+\w{1,15}\s*$',  # Two words
    ]

    # Patterns that indicate meaningful tasks (even if short)
    MEANINGFUL_PATTERNS = [
        # Technical terms
        r'\b(code|program|script|function|class|bug|error|fix|implement)\b',
        r'\b(file|directory|folder|path|read|write|create|delete)\b',
        r'\b(search|find|lookup|query|scan|analyze)\b',
        r'\b(install|setup|configure|build|deploy|test)\b',
        r'\b(pentest|vulnerability|security|exploit|scan)\b',

        # Programming languages
        r'\b(python|javascript|java|c\+\+|rust|go|typescript)\b',

        # Question words that need analysis
        r'\b(why|how|what|when|where|explain|describe|compare)\b',

        # Action verbs that indicate work
        r'\b(generate|modify|update|refactor|optimize|improve)\b',
    ]

    def __init__(self):
        """Initialize the importance filter."""
        self.task_classifier = get_task_classifier()

        # Compile patterns for efficiency
        self.trivial_regex = [re.compile(p, re.IGNORECASE) for p in self.TRIVIAL_PATTERNS]
        self.meaningful_regex = [re.compile(p, re.IGNORECASE) for p in self.MEANINGFUL_PATTERNS]

        logger.info("Task Importance Filter initialized")

    def should_learn(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        errors: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, ImportanceLevel, str]:
        """Determine if task is important enough to trigger learning.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Final outcome
            success: Whether task succeeded
            errors: Any errors encountered
            context: Additional context

        Returns:
            Tuple of (should_learn, importance_level, reason)
        """
        errors = errors or []
        context = context or {}

        # Step 1: Check regex patterns for trivial tasks
        is_trivial_regex = self._check_trivial_regex(task)
        if is_trivial_regex:
            logger.debug(f"Task filtered as TRIVIAL (regex): {task[:50]}")
            return False, ImportanceLevel.TRIVIAL, "Matched trivial pattern (short confirmation/greeting)"

        # Step 2: Check for meaningful patterns (override trivial)
        is_meaningful = self._check_meaningful_patterns(task)

        # Step 3: Use task classifier for semantic analysis
        task_type, confidence = self.task_classifier.classify(task)

        # Conversational tasks are trivial
        if task_type == TaskType.CONVERSATIONAL and not is_meaningful:
            logger.debug(f"Task filtered as TRIVIAL (conversational): {task[:50]}")
            return False, ImportanceLevel.TRIVIAL, "Conversational task with no technical content"

        # Simple QA with high confidence and no actions is trivial
        if task_type == TaskType.SIMPLE_QA and confidence > 0.7 and len(actions) == 0:
            logger.debug(f"Task filtered as TRIVIAL (simple QA): {task[:50]}")
            return False, ImportanceLevel.TRIVIAL, "Simple question with direct answer, no actions taken"

        # Step 4: Analyze task metrics
        metrics = self._analyze_task_metrics(task, actions, outcome, success, errors)
        importance_score = metrics["importance_score"]

        # Step 5: Determine importance level
        if importance_score < 0.2:
            return False, ImportanceLevel.TRIVIAL, f"Importance score too low: {importance_score:.2f}"
        elif importance_score < 0.4:
            return False, ImportanceLevel.LOW, f"Importance score below threshold: {importance_score:.2f}"
        elif importance_score < 0.7:
            return True, ImportanceLevel.MEDIUM, f"Medium importance task: {importance_score:.2f}"
        else:
            return True, ImportanceLevel.HIGH, f"High importance task: {importance_score:.2f}"

    def _check_trivial_regex(self, task: str) -> bool:
        """Check if task matches trivial regex patterns.

        Args:
            task: Task description

        Returns:
            True if matches trivial pattern
        """
        task_stripped = task.strip()

        # Very short tasks (< 5 chars) are likely trivial
        if len(task_stripped) < 5:
            return True

        # Check against trivial patterns
        for pattern in self.trivial_regex:
            if pattern.match(task_stripped):
                return True

        return False

    def _check_meaningful_patterns(self, task: str) -> bool:
        """Check if task contains meaningful technical patterns.

        Args:
            task: Task description

        Returns:
            True if contains meaningful patterns
        """
        for pattern in self.meaningful_regex:
            if pattern.search(task):
                return True

        return False

    def _analyze_task_metrics(
        self,
        task: str,
        actions: List[str],
        outcome: str,
        success: bool,
        errors: List[str]
    ) -> Dict[str, Any]:
        """Analyze task metrics to calculate importance score.

        Args:
            task: Task description
            actions: Actions taken
            outcome: Final outcome
            success: Success status
            errors: Errors encountered

        Returns:
            Dict with metrics and importance score
        """
        score = 0.0
        factors = []

        # Factor 1: Number of actions (more actions = more complex)
        action_count = len(actions)
        if action_count == 0:
            score += 0.0
            factors.append("No actions taken (0.0)")
        elif action_count == 1:
            score += 0.1
            factors.append("Single action (0.1)")
        elif action_count <= 3:
            score += 0.3
            factors.append(f"{action_count} actions (0.3)")
        elif action_count <= 6:
            score += 0.5
            factors.append(f"{action_count} actions (0.5)")
        else:
            score += 0.7
            factors.append(f"{action_count} actions (0.7)")

        # Factor 2: Task description length (longer = more complex)
        task_length = len(task)
        if task_length < 20:
            score += 0.0
            factors.append("Very short task (0.0)")
        elif task_length < 50:
            score += 0.1
            factors.append("Short task (0.1)")
        elif task_length < 100:
            score += 0.2
            factors.append("Medium task (0.2)")
        else:
            score += 0.3
            factors.append("Long task (0.3)")

        # Factor 3: Outcome complexity
        outcome_length = len(outcome)
        if outcome_length > 200:
            score += 0.2
            factors.append("Complex outcome (0.2)")
        elif outcome_length > 100:
            score += 0.1
            factors.append("Moderate outcome (0.1)")

        # Factor 4: Errors indicate learning opportunity
        if errors and len(errors) > 0:
            score += 0.3
            factors.append(f"Encountered {len(errors)} errors (0.3)")

        # Factor 5: Failure indicates learning opportunity
        if not success:
            score += 0.2
            factors.append("Task failed (0.2)")

        # Factor 6: Multi-sentence task (indicates complexity)
        sentence_count = task.count('.') + task.count('?') + task.count('!')
        if sentence_count >= 2:
            score += 0.2
            factors.append("Multi-sentence task (0.2)")

        # Factor 7: Technical keywords
        technical_keywords = [
            'function', 'class', 'method', 'variable', 'algorithm',
            'database', 'api', 'server', 'client', 'request',
            'response', 'error', 'exception', 'bug', 'test',
            'deploy', 'build', 'compile', 'debug', 'refactor'
        ]

        task_lower = task.lower()
        keyword_count = sum(1 for kw in technical_keywords if kw in task_lower)
        if keyword_count > 0:
            keyword_score = min(keyword_count * 0.15, 0.3)
            score += keyword_score
            factors.append(f"{keyword_count} technical keywords ({keyword_score:.2f})")

        # Normalize score to 0-1 range
        importance_score = min(score, 1.0)

        return {
            "importance_score": importance_score,
            "action_count": action_count,
            "task_length": task_length,
            "outcome_length": outcome_length,
            "error_count": len(errors),
            "success": success,
            "factors": factors
        }

    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get statistics about filtering.

        Returns:
            Statistics dict
        """
        return {
            "trivial_patterns_count": len(self.TRIVIAL_PATTERNS),
            "meaningful_patterns_count": len(self.MEANINGFUL_PATTERNS),
            "filter_active": True
        }


# Global instance
_task_importance_filter: Optional[TaskImportanceFilter] = None


def get_task_importance_filter() -> TaskImportanceFilter:
    """Get or create global task importance filter.

    Returns:
        TaskImportanceFilter instance
    """
    global _task_importance_filter
    if _task_importance_filter is None:
        _task_importance_filter = TaskImportanceFilter()
    return _task_importance_filter
