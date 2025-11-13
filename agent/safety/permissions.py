"""Permission management for agent operations."""

import logging
from typing import Dict, Set, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for operations."""
    ALLOWED = "allowed"  # Always allowed
    CONFIRM = "confirm"  # Requires confirmation
    RESTRICTED = "restricted"  # Requires special permission
    DENIED = "denied"  # Always denied


class PermissionManager:
    """Manager for operation permissions."""

    def __init__(self, auto_approve: bool = False):
        """Initialize permission manager.

        Args:
            auto_approve: If True, auto-approve CONFIRM level operations
        """
        self.auto_approve = auto_approve

        # Define permission rules
        self.rules: Dict[str, Dict[str, PermissionLevel]] = {
            "file_system": {
                "read": PermissionLevel.ALLOWED,
                "write": PermissionLevel.ALLOWED,
                "list": PermissionLevel.ALLOWED,
                "exists": PermissionLevel.ALLOWED,
                "search": PermissionLevel.ALLOWED,
                "mkdir": PermissionLevel.ALLOWED,
                "delete": PermissionLevel.CONFIRM,  # Requires confirmation
            },
            "terminal": {
                "git": PermissionLevel.ALLOWED,
                "npm": PermissionLevel.ALLOWED,
                "pip": PermissionLevel.ALLOWED,
                "python": PermissionLevel.ALLOWED,
                "node": PermissionLevel.ALLOWED,
                "ls": PermissionLevel.ALLOWED,
                "cat": PermissionLevel.ALLOWED,
                "echo": PermissionLevel.ALLOWED,
                "rm": PermissionLevel.DENIED,  # Always denied
                "sudo": PermissionLevel.DENIED,
                "shutdown": PermissionLevel.DENIED,
                "reboot": PermissionLevel.DENIED,
            },
            "web_generator": {
                "generate": PermissionLevel.ALLOWED,
            },
            "web_search": {
                "search": PermissionLevel.ALLOWED,
            },
            "pentest": {
                "nmap": PermissionLevel.ALLOWED,
                "sqlmap": PermissionLevel.ALLOWED,
                "ffuf": PermissionLevel.ALLOWED,
                "gospider": PermissionLevel.ALLOWED,
                "nuclei": PermissionLevel.ALLOWED,
                "subfinder": PermissionLevel.ALLOWED,
                "httpx": PermissionLevel.ALLOWED,
            }
        }

        # Track permission requests
        self.requests_log: list = []

        # Callback for confirmation requests
        self.confirm_callback: Optional[Callable] = None

    def check_permission(
        self,
        tool_name: str,
        operation: str,
        **context
    ) -> tuple[bool, Optional[str]]:
        """Check if operation is permitted.

        Args:
            tool_name: Name of the tool
            operation: Operation to perform
            **context: Additional context for decision

        Returns:
            Tuple of (is_permitted, reason_if_denied)
        """
        # Log the request
        self.requests_log.append({
            "tool": tool_name,
            "operation": operation,
            "context": context
        })

        # Get permission level
        level = self._get_permission_level(tool_name, operation)

        if level == PermissionLevel.ALLOWED:
            logger.debug(f"Permission granted: {tool_name}.{operation}")
            return True, None

        elif level == PermissionLevel.DENIED:
            reason = f"Operation '{operation}' is denied for tool '{tool_name}'"
            logger.warning(f"Permission denied: {reason}")
            return False, reason

        elif level == PermissionLevel.CONFIRM:
            if self.auto_approve:
                logger.info(f"Auto-approved: {tool_name}.{operation}")
                return True, None

            # Request confirmation
            if self.confirm_callback:
                approved = self.confirm_callback(tool_name, operation, context)
                if approved:
                    logger.info(f"User approved: {tool_name}.{operation}")
                    return True, None
                else:
                    logger.info(f"User denied: {tool_name}.{operation}")
                    return False, "Operation denied by user"

            # No callback, default to deny
            reason = f"Operation '{operation}' requires confirmation but no callback set"
            logger.warning(reason)
            return False, reason

        elif level == PermissionLevel.RESTRICTED:
            # Check if user has special permission (future implementation)
            reason = f"Operation '{operation}' requires special permission"
            logger.warning(f"Permission restricted: {reason}")
            return False, reason

        # Default deny
        return False, "Permission check failed"

    def _get_permission_level(self, tool_name: str, operation: str) -> PermissionLevel:
        """Get permission level for operation.

        Args:
            tool_name: Tool name
            operation: Operation name

        Returns:
            PermissionLevel
        """
        if tool_name not in self.rules:
            # Unknown tool, default to CONFIRM for safety
            logger.warning(f"Unknown tool '{tool_name}', defaulting to CONFIRM")
            return PermissionLevel.CONFIRM

        tool_rules = self.rules[tool_name]

        if operation in tool_rules:
            return tool_rules[operation]

        # Unknown operation for known tool, default to CONFIRM
        logger.warning(f"Unknown operation '{operation}' for tool '{tool_name}', defaulting to CONFIRM")
        return PermissionLevel.CONFIRM

    def set_permission(
        self,
        tool_name: str,
        operation: str,
        level: PermissionLevel
    ):
        """Set permission level for operation.

        Args:
            tool_name: Tool name
            operation: Operation name
            level: Permission level
        """
        if tool_name not in self.rules:
            self.rules[tool_name] = {}

        self.rules[tool_name][operation] = level
        logger.info(f"Set permission: {tool_name}.{operation} = {level.value}")

    def set_confirm_callback(self, callback: Callable):
        """Set callback for confirmation requests.

        Args:
            callback: Function(tool_name, operation, context) -> bool
        """
        self.confirm_callback = callback

    def get_requests_log(self) -> list:
        """Get log of permission requests.

        Returns:
            List of request dicts
        """
        return self.requests_log

    def clear_log(self):
        """Clear permission requests log."""
        self.requests_log = []

    def get_tool_permissions(self, tool_name: str) -> Dict[str, PermissionLevel]:
        """Get all permissions for a tool.

        Args:
            tool_name: Tool name

        Returns:
            Dict of operation -> PermissionLevel
        """
        return self.rules.get(tool_name, {})

    def is_operation_safe(self, tool_name: str, operation: str) -> bool:
        """Quick check if operation is safe (ALLOWED level).

        Args:
            tool_name: Tool name
            operation: Operation name

        Returns:
            True if operation is at ALLOWED level
        """
        level = self._get_permission_level(tool_name, operation)
        return level == PermissionLevel.ALLOWED


# Global instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager(auto_approve: bool = False) -> PermissionManager:
    """Get or create global permission manager.

    Args:
        auto_approve: Auto-approve confirmations

    Returns:
        PermissionManager instance
    """
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager(auto_approve=auto_approve)
    return _permission_manager
