"""Input validation and output sanitization for security."""

import re
import logging
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class InputValidator:
    """Validator for input sanitization and security checks."""

    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('\s*OR\s+'?1'?\s*=\s*'?1)",
        r"('\s*OR\s+'?1'?\s*=\s*'?1'?\s*--)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(;\s*DROP\b)",
        r"(--\s*$)",
        r"(/\*.*\*/)",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\(.*\)",  # Command substitution
        r"`.*`",  # Backtick command substitution
        r">\s*/dev/",  # Device file access
        r"\|\s*sh",  # Pipe to shell
        r"\|\s*bash",  # Pipe to bash
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # Directory traversal
        r"\.\.",  # Parent directory
        r"~\/",  # Home directory
        r"/etc/",  # System directories
        r"/proc/",
        r"/sys/",
        r"C:\\Windows",
        r"C:\\System32",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers (onclick, onerror, etc.)
        r"<iframe",
        r"<embed",
        r"<object",
    ]

    def __init__(self, strict_mode: bool = False):
        """Initialize validator.

        Args:
            strict_mode: If True, be more aggressive in blocking
        """
        self.strict_mode = strict_mode

    def validate_input(self, user_input: str, context: str = "general") -> Tuple[bool, Optional[str]]:
        """Validate user input for security issues.

        Args:
            user_input: Input string to validate
            context: Context of input (command, file_path, web_content, etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not user_input:
            return True, None

        # Check for SQL injection
        if context in ["command", "general"]:
            if self._check_sql_injection(user_input):
                return False, "Potential SQL injection detected"

        # Check for command injection
        if context in ["command", "terminal", "general"]:
            if self._check_command_injection(user_input):
                return False, "Potential command injection detected"

        # Check for path traversal
        if context in ["file_path", "general"]:
            if self._check_path_traversal(user_input):
                return False, "Potential path traversal detected"

        # Check for XSS
        if context in ["web_content", "general"]:
            if self._check_xss(user_input):
                return False, "Potential XSS attack detected"

        return True, None

    def _check_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns."""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        return False

    def _check_command_injection(self, text: str) -> bool:
        """Check for command injection patterns."""
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Command injection pattern detected: {pattern}")
                return True
        return False

    def _check_path_traversal(self, text: str) -> bool:
        """Check for path traversal patterns."""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Path traversal pattern detected: {pattern}")
                return True
        return False

    def _check_xss(self, text: str) -> bool:
        """Check for XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {pattern}")
                return True
        return False

    def sanitize_path(self, path: str) -> str:
        """Sanitize file path.

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path
        """
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '', path)
        # Remove path traversal attempts
        sanitized = sanitized.replace('..', '')
        return sanitized

    def sanitize_command(self, command: str) -> str:
        """Sanitize command string.

        Args:
            command: Command to sanitize

        Returns:
            Sanitized command
        """
        # Remove shell metacharacters if in strict mode
        if self.strict_mode:
            sanitized = re.sub(r'[;&|`$()]', '', command)
            return sanitized
        return command


class OutputValidator:
    """Validator for output filtering and secret detection."""

    # Patterns for secrets and credentials
    SECRET_PATTERNS = {
        "api_key": [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI style
            r'gsk_[a-zA-Z0-9]{20,}',  # Groq style
        ],
        "password": [
            r'password["\']?\s*[:=]\s*["\']?([^"\'\\s]{8,})',
            r'passwd["\']?\s*[:=]\s*["\']?([^"\'\\s]{8,})',
        ],
        "token": [
            r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})',
            r'bearer\s+([a-zA-Z0-9_\-\.]{20,})',
        ],
        "aws_key": [
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key
            r'aws[_-]?secret[_-]?access[_-]?key',
        ],
        "private_key": [
            r'-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----',
        ],
        "database_url": [
            r'(postgresql|mysql|mongodb):\/\/[^\\s]+',
        ]
    }

    def __init__(self, redact: bool = True):
        """Initialize output validator.

        Args:
            redact: If True, redact secrets. If False, just detect.
        """
        self.redact = redact
        self.detected_secrets: List[Dict[str, str]] = []

    def validate_output(self, output: str) -> Tuple[str, List[str]]:
        """Validate and optionally redact secrets from output.

        Args:
            output: Output string to validate

        Returns:
            Tuple of (cleaned_output, list_of_detected_secret_types)
        """
        if not output:
            return output, []

        cleaned = output
        detected = []

        for secret_type, patterns in self.SECRET_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, output, re.IGNORECASE)
                for match in matches:
                    detected.append(secret_type)
                    logger.warning(f"Detected {secret_type} in output")

                    # Store detection info
                    self.detected_secrets.append({
                        "type": secret_type,
                        "pattern": pattern,
                        "match": match.group(0)[:20] + "..."  # First 20 chars
                    })

                    if self.redact:
                        # Redact the secret
                        secret_value = match.group(0)
                        cleaned = cleaned.replace(secret_value, f"[REDACTED_{secret_type.upper()}]")

        return cleaned, list(set(detected))

    def check_for_secrets(self, text: str) -> bool:
        """Quick check if text contains any secrets.

        Args:
            text: Text to check

        Returns:
            True if secrets detected
        """
        for patterns in self.SECRET_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False

    def get_detected_secrets(self) -> List[Dict[str, str]]:
        """Get list of detected secrets.

        Returns:
            List of detected secret info dicts
        """
        return self.detected_secrets

    def clear_detections(self):
        """Clear detected secrets list."""
        self.detected_secrets = []


# Global instances
_input_validator: Optional[InputValidator] = None
_output_validator: Optional[OutputValidator] = None


def get_input_validator(strict_mode: bool = False) -> InputValidator:
    """Get or create global input validator.

    Args:
        strict_mode: Strict validation mode

    Returns:
        InputValidator instance
    """
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator(strict_mode=strict_mode)
    return _input_validator


def get_output_validator(redact: bool = True) -> OutputValidator:
    """Get or create global output validator.

    Args:
        redact: Whether to redact secrets

    Returns:
        OutputValidator instance
    """
    global _output_validator
    if _output_validator is None:
        _output_validator = OutputValidator(redact=redact)
    return _output_validator
