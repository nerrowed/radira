"""Base classes for agent tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import time

# Import centralized exceptions
from agent.core.exceptions import (
    ToolError,
    ToolValidationError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ToolPermissionError
)


class ToolStatus(Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """Result from tool execution."""

    status: ToolStatus
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if execution failed."""
        return self.status == ToolStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata or {},
            "execution_time": self.execution_time
        }

    def __str__(self) -> str:
        """String representation."""
        if self.is_success:
            return f"Success: {self.output}"
        else:
            return f"Error: {self.error}"


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    def __init__(self):
        """Initialize tool."""
        self._execution_count = 0
        self._total_execution_time = 0.0

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (unique identifier)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """Expected parameters for the tool.

        Returns:
            Dict with parameter definitions (name, type, description, required)
        """
        return {}

    @property
    def examples(self) -> List[str]:
        """Usage examples for the tool.

        Returns:
            List of example usage strings
        """
        return []

    @property
    def category(self) -> str:
        """Tool category (e.g., 'file_system', 'terminal', 'web').

        Returns:
            Category string
        """
        return "general"

    @property
    def requires_confirmation(self) -> bool:
        """Whether tool requires user confirmation before execution.

        Returns:
            True if confirmation needed
        """
        return False

    @property
    def is_dangerous(self) -> bool:
        """Whether tool can perform dangerous operations.

        Returns:
            True if potentially dangerous
        """
        return False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution status and output
        """
        pass

    def validate_input(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate input parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required parameters
        for param_name, param_info in self.parameters.items():
            if param_info.get("required", False) and param_name not in kwargs:
                return False, f"Missing required parameter: {param_name}"

        return True, None

    def run(self, **kwargs) -> ToolResult:
        """Run tool with validation and timing.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult
        """
        # Validate input
        is_valid, error_msg = self.validate_input(**kwargs)
        if not is_valid:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=error_msg
            )

        # Execute with timing
        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            result.execution_time = time.time() - start_time

            # Update stats
            self._execution_count += 1
            self._total_execution_time += result.execution_time

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Tool execution failed: {str(e)}",
                execution_time=execution_time
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics.

        Returns:
            Dict with execution stats
        """
        avg_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0
            else 0.0
        )

        return {
            "name": self.name,
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_time
        }

    def reset_stats(self):
        """Reset execution statistics."""
        self._execution_count = 0
        self._total_execution_time = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation.

        Returns:
            Dict with tool information
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "examples": self.examples,
            "requires_confirmation": self.requires_confirmation,
            "is_dangerous": self.is_dangerous
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category}')>"


# Note: Tool exceptions are now imported from agent.core.exceptions
# This ensures consistency across the entire codebase
