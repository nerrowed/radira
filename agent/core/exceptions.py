"""Custom exception hierarchy for RADIRA autonomous agent.

This module provides a comprehensive exception hierarchy for better
error handling, debugging, and monitoring throughout the system.
"""


# ==================== BASE EXCEPTIONS ====================

class RadiraException(Exception):
    """Base exception for all RADIRA-specific errors.

    All custom exceptions in the system should inherit from this class.
    This allows catching all RADIRA-specific errors with a single except clause.
    """

    def __init__(self, message: str, details: dict = None):
        """Initialize exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Optional dict with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """String representation of exception."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


# ==================== LLM RELATED ERRORS ====================

class LLMError(RadiraException):
    """Base exception for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """Error communicating with LLM API (Groq)."""
    pass


class RateLimitError(LLMAPIError):
    """Rate limit exceeded for LLM API."""

    def __init__(self, message: str, retry_after: int = None, details: dict = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional details
        """
        super().__init__(message, details)
        self.retry_after = retry_after


class LLMTimeoutError(LLMAPIError):
    """LLM API request timed out."""
    pass


class LLMResponseError(LLMError):
    """Error parsing or processing LLM response."""
    pass


class TokenLimitExceededError(LLMError):
    """Token limit exceeded for request or conversation."""

    def __init__(self, message: str, token_count: int, limit: int, details: dict = None):
        """Initialize token limit error.

        Args:
            message: Error message
            token_count: Actual token count
            limit: Token limit
            details: Additional details
        """
        super().__init__(message, details)
        self.token_count = token_count
        self.limit = limit


class ContextOverflowError(LLMError):
    """Context window size exceeded."""

    def __init__(self, message: str, context_size: int, max_size: int, details: dict = None):
        """Initialize context overflow error.

        Args:
            message: Error message
            context_size: Current context size
            max_size: Maximum allowed size
            details: Additional details
        """
        super().__init__(message, details)
        self.context_size = context_size
        self.max_size = max_size


# ==================== TOOL RELATED ERRORS ====================

class ToolError(RadiraException):
    """Base exception for tool-related errors."""
    pass


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    pass


class ToolExecutionError(ToolError):
    """Error executing a tool."""

    def __init__(self, message: str, tool_name: str, operation: str = None, details: dict = None):
        """Initialize tool execution error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            operation: Operation that was attempted
            details: Additional details
        """
        super().__init__(message, details)
        self.tool_name = tool_name
        self.operation = operation


class ToolValidationError(ToolError):
    """Tool argument validation failed."""
    pass


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""

    def __init__(self, message: str, tool_name: str, timeout_seconds: int, details: dict = None):
        """Initialize tool timeout error.

        Args:
            message: Error message
            tool_name: Name of the tool that timed out
            timeout_seconds: Timeout duration
            details: Additional details
        """
        super().__init__(message, details)
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds


class ToolPermissionError(ToolError):
    """Tool execution denied due to permissions or safety checks."""
    pass


# ==================== MEMORY RELATED ERRORS ====================

class MemoryError(RadiraException):
    """Base exception for memory-related errors."""
    pass


class MemoryStorageError(MemoryError):
    """Error storing data in memory (ChromaDB, etc)."""
    pass


class MemoryRetrievalError(MemoryError):
    """Error retrieving data from memory."""
    pass


class MemoryConnectionError(MemoryError):
    """Error connecting to memory backend (ChromaDB, Redis, etc)."""
    pass


class MemoryCorruptionError(MemoryError):
    """Memory data is corrupted or invalid."""
    pass


# ==================== ORCHESTRATOR RELATED ERRORS ====================

class OrchestratorError(RadiraException):
    """Base exception for orchestrator-related errors."""
    pass


class MaxIterationsExceededError(OrchestratorError):
    """Maximum iteration limit reached."""

    def __init__(self, message: str, iterations: int, max_iterations: int, details: dict = None):
        """Initialize max iterations error.

        Args:
            message: Error message
            iterations: Actual iterations performed
            max_iterations: Maximum allowed iterations
            details: Additional details
        """
        super().__init__(message, details)
        self.iterations = iterations
        self.max_iterations = max_iterations


class TaskClassificationError(OrchestratorError):
    """Error classifying user task."""
    pass


class IntentUnderstandingError(OrchestratorError):
    """Error understanding user intent."""
    pass


# ==================== CONFIGURATION ERRORS ====================

class ConfigurationError(RadiraException):
    """Base exception for configuration-related errors."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration value is missing."""

    def __init__(self, message: str, config_key: str, details: dict = None):
        """Initialize missing config error.

        Args:
            message: Error message
            config_key: Name of missing config key
            details: Additional details
        """
        super().__init__(message, details)
        self.config_key = config_key


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""

    def __init__(self, message: str, config_key: str, config_value: str, details: dict = None):
        """Initialize invalid config error.

        Args:
            message: Error message
            config_key: Name of config key
            config_value: Invalid value
            details: Additional details
        """
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


# ==================== LEARNING RELATED ERRORS ====================

class LearningError(RadiraException):
    """Base exception for learning system errors."""
    pass


class ReflectionError(LearningError):
    """Error during reflection process."""
    pass


class ExperienceStorageError(LearningError):
    """Error storing experience to memory."""
    pass


# ==================== SAFETY RELATED ERRORS ====================

class SafetyError(RadiraException):
    """Base exception for safety-related errors."""
    pass


class SandboxViolationError(SafetyError):
    """Attempted operation violates sandbox restrictions."""
    pass


class BlockedPathError(SafetyError):
    """Attempted to access blocked path."""

    def __init__(self, message: str, path: str, details: dict = None):
        """Initialize blocked path error.

        Args:
            message: Error message
            path: Path that was blocked
            details: Additional details
        """
        super().__init__(message, details)
        self.path = path


class FileSizeExceededError(SafetyError):
    """File size exceeds safety limit."""

    def __init__(self, message: str, file_size: int, max_size: int, details: dict = None):
        """Initialize file size error.

        Args:
            message: Error message
            file_size: Actual file size
            max_size: Maximum allowed size
            details: Additional details
        """
        super().__init__(message, details)
        self.file_size = file_size
        self.max_size = max_size


class UnsafeOperationError(SafetyError):
    """Operation deemed unsafe and blocked."""
    pass


# ==================== STATE MANAGEMENT ERRORS ====================

class StateError(RadiraException):
    """Base exception for state management errors."""
    pass


class SessionError(StateError):
    """Error managing session state."""
    pass


class ContextTrackingError(StateError):
    """Error tracking context."""
    pass


# ==================== VALIDATION ERRORS ====================

class ValidationError(RadiraException):
    """Base exception for validation errors."""
    pass


class InputValidationError(ValidationError):
    """User input validation failed."""
    pass


class OutputValidationError(ValidationError):
    """Output validation failed."""
    pass


# ==================== HELPER FUNCTIONS ====================

def get_exception_hierarchy() -> dict:
    """Get the complete exception hierarchy as a dict.

    Returns:
        Dict mapping exception names to their classes
    """
    import inspect

    exceptions = {}
    for name, obj in globals().items():
        if inspect.isclass(obj) and issubclass(obj, RadiraException):
            exceptions[name] = obj

    return exceptions


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: Exception instance

    Returns:
        True if error should be retried
    """
    retryable_types = (
        LLMTimeoutError,
        LLMAPIError,
        MemoryConnectionError,
        ToolTimeoutError,
    )

    # Don't retry rate limit errors (use backoff instead)
    if isinstance(error, RateLimitError):
        return False

    return isinstance(error, retryable_types)


def should_alert_user(error: Exception) -> bool:
    """Check if error should trigger user alert.

    Args:
        error: Exception instance

    Returns:
        True if user should be alerted
    """
    critical_types = (
        SafetyError,
        ConfigurationError,
        MaxIterationsExceededError,
    )

    return isinstance(error, critical_types)
