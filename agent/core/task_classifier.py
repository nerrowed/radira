"""Task classifier untuk routing cerdas sebelum ReAct loop.

Menentukan apakah task perlu tools atau bisa dijawab langsung.
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Jenis-jenis task."""
    CONVERSATIONAL = "conversational"  # Greeting, casual chat
    SIMPLE_QA = "simple_qa"  # Pertanyaan simple yang bisa dijawab dari knowledge
    FILE_OPERATION = "file_operation"  # File read/write/modify
    WEB_SEARCH = "web_search"  # Butuh search internet
    CODE_GENERATION = "code_generation"  # Generate atau modify code
    PENTEST = "pentest"  # Security testing
    TERMINAL_COMMAND = "terminal_command"  # Execute commands
    COMPLEX_MULTI_STEP = "complex_multi_step"  # Multi-step task


class TaskClassifier:
    """Classifier untuk menentukan jenis task dan tool requirements."""

    # Patterns untuk instant classification
    CONVERSATIONAL_PATTERNS = [
        r'\b(halo|hai|hello|hi|hey)\b',
        r'\b(terima kasih|thanks|thank you)\b',
        r'\b(selamat pagi|selamat siang|selamat malam)\b',
        r'\b(apa kabar|how are you)\b',
        r'\b(bye|goodbye|sampai jumpa)\b',
    ]

    SIMPLE_QA_PATTERNS = [
        r'\b(apa itu|what is|apakah|jelaskan|explain)\b',
        r'\b(kapan|when|dimana|where|siapa|who)\b',
        r'\b(bagaimana|how do|mengapa|why)\b',
        r'\b(definisi|definition|arti|meaning)\b',
    ]

    FILE_OPERATION_PATTERNS = [
        r'\b(buat file|create file|tulis file|write file)\b',
        r'\b(baca file|read file|lihat file|view file)\b',
        r'\b(edit file|ubah file|modify file)\b',
        r'\b(hapus file|delete file|remove file)\b',
        r'\b(simpan|save|persist)\b',
    ]

    WEB_SEARCH_PATTERNS = [
        r'\b(cari|search|google|look up)\b.*\b(web|internet|online)\b',
        r'\b(cuaca|weather)\b',
        r'\b(berita|news|latest|terbaru)\b',
        r'\b(harga|price|cost)\b.*\b(online|toko|store)\b',
    ]

    CODE_GEN_PATTERNS = [
        r'\b(buat|create|generate)\b.*\b(code|program|script|function)\b',
        r'\b(implement|implementasi)\b.*\b(algorithm|function|class)\b',
        r'\b(fix|perbaiki)\b.*\b(bug|error|issue)\b',
    ]

    PENTEST_PATTERNS = [
        r'\b(scan|nmap|pentest|penetration test)\b',
        r'\b(subdomain|enumerate|enumeration)\b',
        r'\b(sqlmap|ffuf|nuclei|nikto)\b',
        r'\b(vulnerability|vuln|security test)\b',
        r'\b(exploit|payload)\b',
    ]

    TERMINAL_PATTERNS = [
        r'\b(jalankan|run|execute)\b.*\b(command|perintah)\b',
        r'\b(install|npm|pip|yarn|cargo)\b',
        r'\b(git|commit|push|pull)\b',
        r'\b(docker|container)\b',
    ]

    def __init__(self, llm_client=None):
        """Initialize classifier.

        Args:
            llm_client: Optional LLM client for ambiguous cases
        """
        self.llm_client = llm_client

    def classify(self, task: str) -> Tuple[TaskType, float]:
        """Classify task type with confidence score.

        Args:
            task: Task description

        Returns:
            Tuple of (TaskType, confidence_score)
        """
        task_lower = task.lower().strip()

        # Check conversational (highest priority)
        if self._matches_patterns(task_lower, self.CONVERSATIONAL_PATTERNS):
            return TaskType.CONVERSATIONAL, 1.0

        # Check pentest (specific tools)
        if self._matches_patterns(task_lower, self.PENTEST_PATTERNS):
            return TaskType.PENTEST, 0.9

        # Check file operations
        if self._matches_patterns(task_lower, self.FILE_OPERATION_PATTERNS):
            return TaskType.FILE_OPERATION, 0.85

        # Check code generation
        if self._matches_patterns(task_lower, self.CODE_GEN_PATTERNS):
            return TaskType.CODE_GENERATION, 0.85

        # Check web search
        if self._matches_patterns(task_lower, self.WEB_SEARCH_PATTERNS):
            return TaskType.WEB_SEARCH, 0.85

        # Check terminal commands
        if self._matches_patterns(task_lower, self.TERMINAL_PATTERNS):
            return TaskType.TERMINAL_COMMAND, 0.85

        # Check simple QA
        if self._matches_patterns(task_lower, self.SIMPLE_QA_PATTERNS):
            # QA with specific tech terms might need tools
            if self._has_technical_indicators(task_lower):
                return TaskType.SIMPLE_QA, 0.6
            return TaskType.SIMPLE_QA, 0.8

        # Fallback: check task complexity
        complexity = self._estimate_complexity(task)

        if complexity > 0.7:
            return TaskType.COMPLEX_MULTI_STEP, 0.5
        elif complexity > 0.4:
            return TaskType.SIMPLE_QA, 0.5
        else:
            return TaskType.CONVERSATIONAL, 0.5

    def get_required_tools(self, task_type: TaskType) -> List[str]:
        """Get list of required tools for task type.

        Args:
            task_type: Type of task

        Returns:
            List of tool names
        """
        tool_mapping = {
            TaskType.CONVERSATIONAL: [],  # No tools
            TaskType.SIMPLE_QA: [],  # Direct LLM
            TaskType.FILE_OPERATION: ["filesystem"],
            TaskType.WEB_SEARCH: ["web_search"],
            TaskType.CODE_GENERATION: ["filesystem", "terminal"],
            TaskType.PENTEST: ["pentest", "terminal", "filesystem"],
            TaskType.TERMINAL_COMMAND: ["terminal"],
            TaskType.COMPLEX_MULTI_STEP: ["filesystem", "terminal", "web_search"],  # All tools
        }

        return tool_mapping.get(task_type, [])

    def get_temperature(self, task_type: TaskType) -> float:
        """Get recommended temperature for task type.

        Args:
            task_type: Type of task

        Returns:
            Temperature value (0.0 - 1.0)
        """
        temp_mapping = {
            TaskType.CONVERSATIONAL: 0.0,  # Deterministic
            TaskType.SIMPLE_QA: 0.2,  # Mostly deterministic
            TaskType.FILE_OPERATION: 0.3,  # Structured
            TaskType.WEB_SEARCH: 0.3,  # Structured
            TaskType.CODE_GENERATION: 0.5,  # Creative but controlled
            TaskType.PENTEST: 0.5,  # Exploratory
            TaskType.TERMINAL_COMMAND: 0.3,  # Structured
            TaskType.COMPLEX_MULTI_STEP: 0.4,  # Balanced
        }

        return temp_mapping.get(task_type, 0.3)

    def get_max_iterations(self, task_type: TaskType) -> int:
        """Get recommended max iterations for task type.

        Args:
            task_type: Type of task

        Returns:
            Max iterations count
        """
        iteration_mapping = {
            TaskType.CONVERSATIONAL: 1,  # Direct response
            TaskType.SIMPLE_QA: 1,  # Direct response
            TaskType.FILE_OPERATION: 3,  # Read/verify/write
            TaskType.WEB_SEARCH: 3,  # Search/extract/summarize
            TaskType.CODE_GENERATION: 5,  # Generate/test/refine
            TaskType.PENTEST: 8,  # Multi-step exploration
            TaskType.TERMINAL_COMMAND: 3,  # Execute/verify/retry
            TaskType.COMPLEX_MULTI_STEP: 10,  # Full complexity
        }

        return iteration_mapping.get(task_type, 10)

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any pattern.

        Args:
            text: Text to check
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _has_technical_indicators(self, text: str) -> bool:
        """Check if text contains technical terms that might need tools.

        Args:
            text: Text to check

        Returns:
            True if technical terms found
        """
        technical_terms = [
            'python', 'javascript', 'java', 'c++', 'rust', 'go',
            'api', 'database', 'server', 'docker', 'kubernetes',
            'react', 'vue', 'angular', 'node', 'npm',
            'error', 'bug', 'issue', 'problem',
            'install', 'configure', 'setup',
        ]

        text_lower = text.lower()
        return any(term in text_lower for term in technical_terms)

    def _estimate_complexity(self, task: str) -> float:
        """Estimate task complexity (0.0 - 1.0).

        Args:
            task: Task description

        Returns:
            Complexity score
        """
        complexity = 0.0

        # Length indicator
        if len(task) > 200:
            complexity += 0.3
        elif len(task) > 100:
            complexity += 0.2
        elif len(task) > 50:
            complexity += 0.1

        # Multiple sentences
        sentences = task.count('.') + task.count('?') + task.count('!')
        complexity += min(sentences * 0.1, 0.3)

        # Keywords indicating complexity
        complex_keywords = [
            'and', 'then', 'after', 'before', 'also', 'additionally',
            'first', 'second', 'next', 'finally',
            'if', 'when', 'unless', 'while',
        ]

        keyword_count = sum(1 for kw in complex_keywords if kw in task.lower())
        complexity += min(keyword_count * 0.1, 0.4)

        return min(complexity, 1.0)


# Global instance
_task_classifier: Optional[TaskClassifier] = None


def get_task_classifier(llm_client=None) -> TaskClassifier:
    """Get or create global task classifier.

    Args:
        llm_client: Optional LLM client

    Returns:
        TaskClassifier instance
    """
    global _task_classifier
    if _task_classifier is None:
        _task_classifier = TaskClassifier(llm_client=llm_client)
    return _task_classifier
