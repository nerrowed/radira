"""Answer validator untuk mendeteksi jawaban yang sudah cukup.

Mencegah agent terus looping padahal jawaban sudah didapat.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Validator untuk menentukan apakah jawaban sudah sufficient."""

    # Keywords yang mengindikasikan jawaban lengkap
    COMPLETION_INDICATORS = [
        "successfully", "completed", "done", "finished", "created",
        "berhasil", "selesai", "sukses", "sudah", "telah",
        "found", "retrieved", "obtained", "generated",
        "ditemukan", "didapat", "dibuat",
    ]

    # Keywords yang mengindikasikan masih proses
    PROGRESS_INDICATORS = [
        "trying", "attempting", "in progress", "working on",
        "mencoba", "sedang", "proses",
    ]

    # Error indicators
    ERROR_INDICATORS = [
        "error", "failed", "could not", "unable", "not found",
        "gagal", "tidak bisa", "tidak ditemukan",
    ]

    def __init__(self):
        """Initialize validator."""
        pass

    def is_sufficient(
        self,
        task: str,
        observation: str,
        thought: Optional[str] = None,
        history: Optional[List[Tuple[str, str]]] = None
    ) -> Tuple[bool, str]:
        """Determine if observation contains sufficient answer.

        Args:
            task: Original task
            observation: Latest observation from tool
            thought: Agent's latest thought (optional)
            history: Full history (optional)

        Returns:
            Tuple of (is_sufficient, reason)
        """
        # Empty observation is not sufficient
        if not observation or len(observation.strip()) < 10:
            return False, "Observation too short"

        # Check if observation is just an error
        if self._is_pure_error(observation):
            return False, "Observation is error"

        # Check completion indicators
        has_completion = self._has_completion_indicators(observation, thought)
        if has_completion:
            # Make sure it's not just starting
            if not self._has_progress_indicators(observation):
                return True, "Completion indicators found"

        # Check if observation directly answers question-based tasks
        if self._is_question(task):
            if self._contains_answer_to_question(task, observation):
                return True, "Observation answers the question"

        # Check for successful file/command operations
        if self._is_operation_task(task):
            if self._operation_succeeded(observation):
                return True, "Operation completed successfully"

        # Check for repeated identical observations (stuck)
        if history and len(history) >= 2:
            if self._is_repeating(observation, history):
                return True, "Repeating observations - should stop"

        # If thought says "I have the answer" or similar
        if thought and self._thought_indicates_completion(thought):
            return True, "Agent thinks task is complete"

        return False, "Not sufficient yet"

    def should_force_final_answer(
        self,
        iteration: int,
        max_iterations: int,
        history: List[Tuple[str, str]],
        last_observation: str
    ) -> Tuple[bool, str]:
        """Determine if agent should be forced to provide Final Answer.

        Args:
            iteration: Current iteration
            max_iterations: Maximum iterations
            history: Execution history
            last_observation: Latest observation

        Returns:
            Tuple of (should_force, reason)
        """
        # Near max iterations with valid observation
        if iteration >= max_iterations - 2:
            if len(last_observation) > 50 and not self._is_pure_error(last_observation):
                return True, "Near max iterations with valid data"

        # Looping detection (same action 3+ times)
        if len(history) >= 3:
            recent_actions = [action for action, _ in history[-5:]]
            action_counts = {action: recent_actions.count(action) for action in set(recent_actions)}

            if any(count >= 3 for count in action_counts.values()):
                return True, "Loop detected - same action repeated 3+ times"

        # No progress in last N iterations
        if len(history) >= 4:
            last_4_observations = [obs for _, obs in history[-4:]]
            if self._all_similar(last_4_observations):
                return True, "No progress - similar observations"

        # Alternating between two actions
        if len(history) >= 4:
            recent_actions = [action for action, _ in history[-4:]]
            if len(set(recent_actions)) == 2:
                # Check if alternating A-B-A-B
                if recent_actions[0] == recent_actions[2] and recent_actions[1] == recent_actions[3]:
                    return True, "Alternating loop detected"

        return False, "Not forcing yet"

    def extract_answer_from_observation(self, observation: str, task: str) -> str:
        """Extract usable answer from observation.

        Args:
            observation: Observation text
            task: Original task

        Returns:
            Extracted answer
        """
        # If observation is already clean and direct
        if len(observation) < 500:
            return observation

        # Try to extract main result
        # Look for patterns like "Result: ...", "Output: ...", "Found: ..."
        result_patterns = [
            r'Result:\s*(.*?)(?:\n\n|\Z)',
            r'Output:\s*(.*?)(?:\n\n|\Z)',
            r'Found:\s*(.*?)(?:\n\n|\Z)',
            r'Hasil:\s*(.*?)(?:\n\n|\Z)',
        ]

        for pattern in result_patterns:
            match = re.search(pattern, observation, re.DOTALL)
            if match:
                return match.group(1).strip()

        # If too long, truncate and summarize
        if len(observation) > 1000:
            return observation[:800] + "...\n\n(Output truncated)"

        return observation

    def _is_pure_error(self, observation: str) -> bool:
        """Check if observation is just an error message.

        Args:
            observation: Observation text

        Returns:
            True if pure error
        """
        obs_lower = observation.lower()

        # Check if starts with "error"
        if obs_lower.strip().startswith("error:"):
            return True

        # Check if contains error indicators but no success indicators
        has_error = any(ind in obs_lower for ind in self.ERROR_INDICATORS)
        has_success = any(ind in obs_lower for ind in self.COMPLETION_INDICATORS)

        if has_error and not has_success:
            # Make sure it's predominantly error
            if obs_lower.count("error") > 2 or obs_lower.count("failed") > 2:
                return True

        return False

    def _has_completion_indicators(self, observation: str, thought: Optional[str] = None) -> bool:
        """Check for completion indicators.

        Args:
            observation: Observation text
            thought: Thought text

        Returns:
            True if completion indicators found
        """
        text = observation.lower()
        if thought:
            text += " " + thought.lower()

        return any(indicator in text for indicator in self.COMPLETION_INDICATORS)

    def _has_progress_indicators(self, text: str) -> bool:
        """Check for progress/ongoing indicators.

        Args:
            text: Text to check

        Returns:
            True if progress indicators found
        """
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.PROGRESS_INDICATORS)

    def _is_question(self, task: str) -> bool:
        """Check if task is a question.

        Args:
            task: Task text

        Returns:
            True if question
        """
        question_words = [
            'apa', 'what', 'siapa', 'who', 'kapan', 'when',
            'dimana', 'where', 'bagaimana', 'how', 'mengapa', 'why',
            'berapa', 'how many', 'how much'
        ]

        task_lower = task.lower()

        # Ends with question mark
        if task.strip().endswith('?'):
            return True

        # Starts with question word
        return any(task_lower.startswith(qw) for qw in question_words)

    def _contains_answer_to_question(self, task: str, observation: str) -> bool:
        """Check if observation contains answer to question.

        Args:
            task: Question task
            observation: Observation

        Returns:
            True if answer present
        """
        # Extract key terms from question
        task_lower = task.lower()

        # Remove question words
        question_words = ['apa', 'what', 'siapa', 'who', 'kapan', 'when', 'bagaimana', 'how']
        for qw in question_words:
            task_lower = task_lower.replace(qw, '')

        # Get important words (more than 3 chars)
        key_terms = [word for word in task_lower.split() if len(word) > 3]

        if not key_terms:
            return False

        # Check if observation discusses these terms
        obs_lower = observation.lower()
        matches = sum(1 for term in key_terms if term in obs_lower)

        # At least 50% of key terms should be present
        return matches >= len(key_terms) * 0.5

    def _is_operation_task(self, task: str) -> bool:
        """Check if task is an operation (create, delete, run, etc).

        Args:
            task: Task text

        Returns:
            True if operation task
        """
        operation_words = [
            'buat', 'create', 'hapus', 'delete', 'jalankan', 'run',
            'install', 'execute', 'scan', 'search', 'generate',
            'tulis', 'write', 'simpan', 'save'
        ]

        task_lower = task.lower()
        return any(op in task_lower for op in operation_words)

    def _operation_succeeded(self, observation: str) -> bool:
        """Check if operation succeeded based on observation.

        Args:
            observation: Observation text

        Returns:
            True if operation succeeded
        """
        success_phrases = [
            "successfully", "completed", "created", "done",
            "berhasil", "sukses", "selesai", "telah dibuat",
            "file created", "command executed", "operation complete"
        ]

        obs_lower = observation.lower()
        return any(phrase in obs_lower for phrase in success_phrases)

    def _is_repeating(self, current_obs: str, history: List[Tuple[str, str]]) -> bool:
        """Check if current observation is repeating previous ones.

        Args:
            current_obs: Current observation
            history: Execution history

        Returns:
            True if repeating
        """
        if len(history) < 2:
            return False

        # Get last 3 observations
        last_observations = [obs for _, obs in history[-3:]]

        # Check similarity with current
        similar_count = sum(
            1 for obs in last_observations
            if self._similarity(current_obs, obs) > 0.8
        )

        return similar_count >= 2

    def _all_similar(self, observations: List[str]) -> bool:
        """Check if all observations are similar.

        Args:
            observations: List of observations

        Returns:
            True if all similar
        """
        if len(observations) < 2:
            return False

        # Compare each with first
        first = observations[0]
        similarities = [self._similarity(first, obs) for obs in observations[1:]]

        return sum(similarities) / len(similarities) > 0.7

    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 - 1.0).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score
        """
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _thought_indicates_completion(self, thought: str) -> bool:
        """Check if agent's thought indicates completion.

        Args:
            thought: Thought text

        Returns:
            True if indicates completion
        """
        completion_phrases = [
            "i have", "saya punya", "sudah dapat", "already have",
            "task complete", "task selesai", "finished",
            "ready to provide", "siap memberikan",
            "dapat menjawab", "can answer now"
        ]

        thought_lower = thought.lower()
        return any(phrase in thought_lower for phrase in completion_phrases)


# Global instance
_answer_validator: Optional[AnswerValidator] = None


def get_answer_validator() -> AnswerValidator:
    """Get or create global answer validator.

    Returns:
        AnswerValidator instance
    """
    global _answer_validator
    if _answer_validator is None:
        _answer_validator = AnswerValidator()
    return _answer_validator
