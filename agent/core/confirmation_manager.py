"""Confirmation manager for tool execution control.

Provides Yes/No/Auto modes for safe tool execution with user confirmation.
"""

from enum import Enum
from typing import Dict, Any, Optional
from rich.prompt import Confirm, Prompt
from rich.console import Console
import logging

logger = logging.getLogger(__name__)
console = Console()


class ConfirmationMode(Enum):
    """Confirmation modes for tool execution."""
    YES = "yes"  # Always execute without asking
    NO = "no"    # Always ask for confirmation
    AUTO = "auto"  # Smart decision based on operation danger level


class ConfirmationManager:
    """Manages tool execution confirmation with cost-efficient smart detection."""

    # Tools that NEVER need confirmation (read-only operations)
    SAFE_TOOLS = {
        "file_system": ["read", "list", "exists", "search"],
        "terminal": [],  # All terminal commands need confirmation
        "web_search": ["search"],  # Read-only
        "pentest": [],  # All pentest needs confirmation
        "web_generator": [],  # All generation needs confirmation
        "code_generator": []  # All code generation needs confirmation
    }

    # Operations that are considered dangerous
    DANGEROUS_OPERATIONS = {
        "file_system": ["write", "delete", "mkdir"],
        "terminal": ["*"],  # All terminal commands
        "web_generator": ["*"],  # All web generation
        "code_generator": ["*"],  # All code generation
        "pentest": ["*"]  # All pentest operations
    }

    def __init__(self, mode: ConfirmationMode = ConfirmationMode.AUTO, verbose: bool = True):
        """Initialize confirmation manager.

        Args:
            mode: Confirmation mode (YES, NO, AUTO)
            verbose: Show confirmation messages
        """
        self.mode = mode
        self.verbose = verbose
        self.confirmation_cache = {}  # Cache decisions per session

    def should_execute_tool(
        self,
        tool_name: str,
        operation: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Determine if tool should be executed based on confirmation mode.

        Args:
            tool_name: Name of tool to execute
            operation: Operation type (e.g., "write", "read")
            arguments: Tool arguments

        Returns:
            True if should execute, False if user declined
        """
        # Mode: YES - Always execute
        if self.mode == ConfirmationMode.YES:
            return True

        # Mode: NO - Always ask
        if self.mode == ConfirmationMode.NO:
            return self._prompt_user_confirmation(tool_name, operation, arguments)

        # Mode: AUTO - Smart decision
        return self._auto_confirm(tool_name, operation, arguments)

    def _auto_confirm(
        self,
        tool_name: str,
        operation: Optional[str],
        arguments: Optional[Dict[str, Any]]
    ) -> bool:
        """Smart confirmation based on operation danger level.

        Args:
            tool_name: Tool name
            operation: Operation type
            arguments: Arguments

        Returns:
            True if safe to execute, False if user declined confirmation
        """
        # Check if operation is safe (no confirmation needed)
        if self._is_safe_operation(tool_name, operation):
            if self.verbose:
                console.print(f"[dim]   ✓ Auto-approved: {tool_name}.{operation} (safe)[/dim]")
            return True

        # Check if operation is dangerous (requires confirmation)
        if self._is_dangerous_operation(tool_name, operation, arguments):
            return self._prompt_user_confirmation(tool_name, operation, arguments)

        # Default: Execute without confirmation for unknown operations
        if self.verbose:
            console.print(f"[dim]   ✓ Auto-approved: {tool_name}.{operation} (default)[/dim]")
        return True

    def _is_safe_operation(self, tool_name: str, operation: Optional[str]) -> bool:
        """Check if operation is safe (read-only).

        Args:
            tool_name: Tool name
            operation: Operation type

        Returns:
            True if safe
        """
        if tool_name not in self.SAFE_TOOLS:
            return False

        safe_ops = self.SAFE_TOOLS[tool_name]

        # If no operation specified, assume not safe
        if operation is None:
            return False

        return operation in safe_ops

    def _is_dangerous_operation(
        self,
        tool_name: str,
        operation: Optional[str],
        arguments: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if operation is dangerous (needs confirmation).

        Args:
            tool_name: Tool name
            operation: Operation type
            arguments: Tool arguments

        Returns:
            True if dangerous
        """
        if tool_name not in self.DANGEROUS_OPERATIONS:
            return False

        dangerous_ops = self.DANGEROUS_OPERATIONS[tool_name]

        # Wildcard: all operations are dangerous
        if "*" in dangerous_ops:
            return True

        # If no operation specified, assume dangerous
        if operation is None:
            return True

        # Check if specific operation is dangerous
        if operation in dangerous_ops:
            # Additional checks for file_system.write
            if tool_name == "file_system" and operation == "write":
                # Check if overwriting existing file (more dangerous)
                path = arguments.get("path") if arguments else None
                if path and self._file_exists(path):
                    return True  # Overwriting existing file
            return True

        return False

    def _file_exists(self, path: str) -> bool:
        """Check if file exists (for overwrite detection).

        Args:
            path: File path

        Returns:
            True if exists
        """
        try:
            from pathlib import Path
            return Path(path).exists()
        except Exception:
            return False

    def _prompt_user_confirmation(
        self,
        tool_name: str,
        operation: Optional[str],
        arguments: Optional[Dict[str, Any]]
    ) -> bool:
        """Prompt user for confirmation.

        Args:
            tool_name: Tool name
            operation: Operation type
            arguments: Arguments

        Returns:
            True if user confirms, False otherwise
        """
        # Build confirmation message
        op_str = f".{operation}" if operation else ""
        args_str = self._format_arguments(arguments)

        console.print()  # Blank line
        console.print(f"[yellow]⚠️  About to execute:[/yellow] [bold]{tool_name}{op_str}[/bold]")
        if args_str:
            console.print(f"   [dim]Arguments: {args_str}[/dim]")

        # Ask for confirmation
        try:
            confirmed = Confirm.ask("   Proceed?", default=True)
            console.print()  # Blank line
            return confirmed
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]   Cancelled by user[/yellow]\n")
            return False

    def _format_arguments(self, arguments: Optional[Dict[str, Any]]) -> str:
        """Format arguments for display.

        Args:
            arguments: Tool arguments

        Returns:
            Formatted string
        """
        if not arguments:
            return ""

        # Limit display to important args
        important_keys = ["path", "operation", "command", "description", "filename"]
        filtered = {k: v for k, v in arguments.items() if k in important_keys}

        if not filtered:
            # Show first 3 keys if no important ones
            filtered = dict(list(arguments.items())[:3])

        # Format
        parts = []
        for key, value in filtered.items():
            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            parts.append(f"{key}={value}")

        return ", ".join(parts)

    def set_mode(self, mode: ConfirmationMode):
        """Change confirmation mode.

        Args:
            mode: New confirmation mode
        """
        self.mode = mode
        if self.verbose:
            console.print(f"[cyan]Confirmation mode changed to:[/cyan] {mode.value}")

    def get_mode(self) -> ConfirmationMode:
        """Get current confirmation mode.

        Returns:
            Current mode
        """
        return self.mode


# Global instance
_confirmation_manager: Optional[ConfirmationManager] = None


def get_confirmation_manager(
    mode: ConfirmationMode = ConfirmationMode.AUTO,
    verbose: bool = True
) -> ConfirmationManager:
    """Get or create singleton confirmation manager.

    Args:
        mode: Confirmation mode
        verbose: Show messages

    Returns:
        ConfirmationManager instance
    """
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = ConfirmationManager(mode=mode, verbose=verbose)
    return _confirmation_manager
