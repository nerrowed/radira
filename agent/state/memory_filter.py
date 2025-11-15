"""Memory Filter - Intelligent filtering to prevent storing useless data.

This module implements smart filtering to ensure only valuable information
gets stored in the agent's memory system.
"""

import logging
import re
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory that can be stored."""
    RULE = "rule"  # Permanent behavioral instruction
    FACT = "fact"  # Long-term user information
    EXPERIENCE = "experience"  # Episodic task memory
    USELESS = "useless"  # Should not be stored


class MemoryFilter:
    """Filter to classify and validate memory before storage.

    Prevents storing:
    - Emotional chatter (greetings, thanks, etc.)
    - Repetitive content
    - Non-informative text
    - Meta commentary
    - Filler text
    """

    # Patterns for useless content
    USELESS_PATTERNS = [
        # Greetings
        r"^(halo|hai|hello|hi|hey|selamat pagi|selamat siang|selamat malam)\b",
        # Thanks
        r"(terima kasih|thanks|thank you|makasih)",
        # Casual responses
        r"^(ok|oke|baik|ya|yup|sure|good|nice|cool)\s*$",
        # Questions about wellbeing
        r"(apa kabar|how are you|what's up|gimana|bagaimana)",
        # Empty/short responses
        r"^\w{1,3}$",  # 1-3 character responses
    ]

    # Patterns for rule detection
    RULE_PATTERNS = [
        r"jika\s+.*\s+(maka|lalu|jawab|respon|balas)",  # Indonesian: jika X maka Y
        r"kalau\s+.*\s+(maka|lalu|jawab|respon|balas)",  # Indonesian: kalau X maka Y
        r"if\s+.*\s+(then|respond|answer|say)",  # English: if X then Y
        r"when\s+.*\s+(then|respond|answer|say)",  # English: when X then Y
        r"selalu\s+(jawab|respon|balas)",  # Always respond
        r"always\s+(respond|answer|say)",  # Always respond
        r"ingat\s+bahwa",  # Remember that
        r"remember\s+that",  # Remember that
    ]

    # Patterns for fact detection
    FACT_PATTERNS = [
        r"(nama\s+saya|my\s+name|i\s+am)\s+\w+",  # Name
        r"saya\s+(suka|tidak\s+suka|prefer)",  # Preferences
        r"i\s+(like|dislike|prefer|love|hate)",  # Preferences
        r"(umur|usia|age)\s+(saya|my)\s+\d+",  # Age
        r"saya\s+(tinggal|bekerja)\s+(di|at)",  # Location/work
        r"i\s+(live|work)\s+(in|at)",  # Location/work
    ]

    def __init__(self):
        """Initialize memory filter."""
        self.compiled_useless = [re.compile(p, re.IGNORECASE) for p in self.USELESS_PATTERNS]
        self.compiled_rules = [re.compile(p, re.IGNORECASE) for p in self.RULE_PATTERNS]
        self.compiled_facts = [re.compile(p, re.IGNORECASE) for p in self.FACT_PATTERNS]

    def classify_memory(
        self,
        user_input: str,
        agent_response: str,
        task_success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryType:
        """Classify what type of memory this is (or if it should be stored at all).

        Args:
            user_input: User's input text
            agent_response: Agent's response
            task_success: Whether the task succeeded
            metadata: Additional context

        Returns:
            MemoryType enum indicating what type of memory this is
        """
        # Check if useless
        if self._is_useless(user_input, agent_response):
            return MemoryType.USELESS

        # Check if it's a rule definition
        if self._is_rule(user_input):
            return MemoryType.RULE

        # Check if it's a fact
        if self._is_fact(user_input):
            return MemoryType.FACT

        # Check if it's a valuable experience
        if self._is_valuable_experience(user_input, agent_response, task_success, metadata):
            return MemoryType.EXPERIENCE

        # Default: useless if we can't classify it as valuable
        return MemoryType.USELESS

    def _is_useless(self, user_input: str, agent_response: str) -> bool:
        """Check if the interaction is useless chatter.

        Args:
            user_input: User's input
            agent_response: Agent's response

        Returns:
            True if useless, False otherwise
        """
        # Check user input
        user_lower = user_input.lower().strip()

        # Empty or too short
        if len(user_lower) < 3:
            return True

        # Match useless patterns
        for pattern in self.compiled_useless:
            if pattern.search(user_lower):
                logger.debug(f"Useless pattern matched: {pattern.pattern}")
                return True

        # Check if response is just acknowledgment
        response_lower = agent_response.lower().strip()
        if len(response_lower) < 20 and any(
            word in response_lower for word in ["ok", "baik", "ya", "sure", "done"]
        ):
            # Short acknowledgment without useful info
            return True

        return False

    def _is_rule(self, user_input: str) -> bool:
        """Check if user is defining a rule.

        Args:
            user_input: User's input

        Returns:
            True if this is a rule definition
        """
        for pattern in self.compiled_rules:
            if pattern.search(user_input):
                logger.info(f"Rule pattern detected: {pattern.pattern}")
                return True

        # Additional heuristic: contains command words
        command_words = ["selalu", "jangan", "harus", "wajib", "always", "never", "must"]
        if any(word in user_input.lower() for word in command_words):
            # Check if it's instructional (not just using the word casually)
            if len(user_input.split()) > 3:  # Not too short
                return True

        return False

    def _is_fact(self, user_input: str) -> bool:
        """Check if user is stating a fact about themselves.

        Args:
            user_input: User's input

        Returns:
            True if this is a fact about the user
        """
        for pattern in self.compiled_facts:
            if pattern.search(user_input):
                logger.info(f"Fact pattern detected: {pattern.pattern}")
                return True

        # Additional heuristic: self-description
        self_descriptors = ["saya adalah", "i am", "saya seorang", "my"]
        if any(desc in user_input.lower() for desc in self_descriptors):
            return True

        return False

    def _is_valuable_experience(
        self,
        user_input: str,
        agent_response: str,
        task_success: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if this is a valuable experience worth storing.

        Args:
            user_input: User's input
            agent_response: Agent's response
            task_success: Whether task succeeded
            metadata: Additional context

        Returns:
            True if valuable experience
        """
        # Check if this was a meaningful task
        if metadata:
            # If tools were used, it's likely valuable
            if metadata.get("tool_count", 0) > 0:
                return True

            # If there were errors, valuable to learn from
            if metadata.get("errors"):
                return True

        # Check if response contains solution or lesson
        response_lower = agent_response.lower()
        valuable_indicators = [
            "berhasil", "sukses", "selesai", "completed", "success",  # Success
            "error", "gagal", "failed",  # Failure (learn from it)
            "solusi", "solution", "cara",  # Solution
            "karena", "because", "sebab",  # Explanation
        ]

        if any(indicator in response_lower for indicator in valuable_indicators):
            return True

        # If task involved code generation, file operations, etc. (long response)
        if len(agent_response) > 200:
            return True

        # If user input was a complex task (not just a question)
        task_indicators = ["buat", "create", "generate", "tulis", "write", "ubah", "modify"]
        if any(indicator in user_input.lower() for indicator in task_indicators):
            return True

        return False

    def should_store(
        self,
        user_input: str,
        agent_response: str,
        task_success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Quick check if memory should be stored at all.

        Args:
            user_input: User's input
            agent_response: Agent's response
            task_success: Whether task succeeded
            metadata: Additional context

        Returns:
            True if should store, False otherwise
        """
        memory_type = self.classify_memory(user_input, agent_response, task_success, metadata)
        return memory_type != MemoryType.USELESS

    def extract_rule_components(self, user_input: str) -> Optional[Dict[str, str]]:
        """Extract trigger and response from a rule definition.

        Args:
            user_input: User's input containing rule

        Returns:
            Dict with 'trigger' and 'response', or None if not a rule
        """
        if not self._is_rule(user_input):
            return None

        # Try to parse Indonesian format: "Jika X, maka Y"
        match = re.search(
            r"(?:jika|kalau)\s+(?:saya\s+)?(?:bilang\s+)?['\"]?([^'\"]+?)['\"]?\s*,?\s*(?:maka\s+)?(?:jawab|respon|balas)\s+['\"]?([^'\"]+)['\"]?",
            user_input,
            re.IGNORECASE
        )
        if match:
            trigger = match.group(1).strip()
            response = match.group(2).strip()
            return {"trigger": trigger, "response": response}

        # Try English format: "If X, then Y"
        match = re.search(
            r"(?:if|when)\s+(?:i\s+)?(?:say\s+)?['\"]?([^'\"]+?)['\"]?\s*,?\s*(?:then\s+)?(?:respond|answer|say)\s+['\"]?([^'\"]+)['\"]?",
            user_input,
            re.IGNORECASE
        )
        if match:
            trigger = match.group(1).strip()
            response = match.group(2).strip()
            return {"trigger": trigger, "response": response}

        # Fallback: just extract the whole thing as a general rule
        return {
            "trigger": user_input.strip(),
            "response": "acknowledged"
        }

    def extract_fact_info(self, user_input: str) -> Optional[Dict[str, str]]:
        """Extract fact information from user input.

        Args:
            user_input: User's input containing fact

        Returns:
            Dict with 'category' and 'value', or None if not a fact
        """
        if not self._is_fact(user_input):
            return None

        # Try to extract name
        match = re.search(r"(?:nama\s+saya|my\s+name|i\s+am)\s+(\w+)", user_input, re.IGNORECASE)
        if match:
            return {"category": "name", "value": match.group(1)}

        # Try to extract preference
        match = re.search(
            r"saya\s+(suka|tidak\s+suka|prefer)\s+(.+)",
            user_input,
            re.IGNORECASE
        )
        if match:
            return {"category": "preference", "value": user_input.strip()}

        # Generic fact
        return {"category": "general", "value": user_input.strip()}


# Global instance
_memory_filter: Optional[MemoryFilter] = None


def get_memory_filter() -> MemoryFilter:
    """Get or create global memory filter instance.

    Returns:
        MemoryFilter instance
    """
    global _memory_filter
    if _memory_filter is None:
        _memory_filter = MemoryFilter()
    return _memory_filter
