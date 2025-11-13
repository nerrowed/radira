"""Audit logging for agent operations."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logger for auditing agent operations."""

    def __init__(self, log_file: Optional[Path] = None, console_output: bool = False):
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file
            console_output: Whether to also log to console
        """
        self.log_file = log_file
        self.console_output = console_output
        self.entries = []

        # Create log file if it doesn't exist
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.write_text("[]")  # Initialize as empty JSON array

    def log(
        self,
        event_type: str,
        tool_name: str,
        operation: str,
        **details
    ):
        """Log an audit event.

        Args:
            event_type: Type of event (tool_execution, permission_check, error, etc.)
            tool_name: Name of tool involved
            operation: Operation performed
            **details: Additional event details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "tool": tool_name,
            "operation": operation,
            "details": details
        }

        # Add to in-memory log
        self.entries.append(entry)

        # Write to file
        if self.log_file:
            self._write_to_file(entry)

        # Console output
        if self.console_output:
            self._print_to_console(entry)

        # Also log to Python logger
        logger.debug(f"Audit: {event_type} - {tool_name}.{operation}")

    def log_tool_execution(
        self,
        tool_name: str,
        operation: str,
        inputs: Dict[str, Any],
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        execution_time: float = 0.0
    ):
        """Log a tool execution event.

        Args:
            tool_name: Tool name
            operation: Operation name
            inputs: Input parameters
            success: Whether execution succeeded
            output: Tool output (if successful)
            error: Error message (if failed)
            execution_time: Execution time in seconds
        """
        self.log(
            event_type="tool_execution",
            tool_name=tool_name,
            operation=operation,
            inputs=inputs,
            success=success,
            output=str(output)[:200] if output else None,  # Truncate long outputs
            error=error,
            execution_time=execution_time
        )

    def log_permission_check(
        self,
        tool_name: str,
        operation: str,
        granted: bool,
        reason: Optional[str] = None
    ):
        """Log a permission check event.

        Args:
            tool_name: Tool name
            operation: Operation name
            granted: Whether permission was granted
            reason: Reason if denied
        """
        self.log(
            event_type="permission_check",
            tool_name=tool_name,
            operation=operation,
            granted=granted,
            reason=reason
        )

    def log_security_event(
        self,
        event: str,
        severity: str,
        details: Dict[str, Any]
    ):
        """Log a security-related event.

        Args:
            event: Event description
            severity: Severity level (low, medium, high, critical)
            details: Event details
        """
        self.log(
            event_type="security",
            tool_name="security",
            operation=event,
            severity=severity,
            **details
        )

    def log_error(
        self,
        tool_name: str,
        operation: str,
        error: str,
        **context
    ):
        """Log an error event.

        Args:
            tool_name: Tool name
            operation: Operation that failed
            error: Error message
            **context: Additional context
        """
        self.log(
            event_type="error",
            tool_name=tool_name,
            operation=operation,
            error=error,
            **context
        )

    def _write_to_file(self, entry: Dict):
        """Write entry to log file.

        Args:
            entry: Log entry dict
        """
        try:
            # Read existing entries
            existing = json.loads(self.log_file.read_text())
            existing.append(entry)

            # Write back (keep last 1000 entries)
            if len(existing) > 1000:
                existing = existing[-1000:]

            self.log_file.write_text(json.dumps(existing, indent=2))

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _print_to_console(self, entry: Dict):
        """Print entry to console.

        Args:
            entry: Log entry dict
        """
        print(f"[AUDIT] {entry['timestamp']} - {entry['event_type']}: "
              f"{entry['tool']}.{entry['operation']}")

    def get_entries(
        self,
        event_type: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get audit log entries.

        Args:
            event_type: Filter by event type
            tool_name: Filter by tool name
            limit: Maximum number of entries

        Returns:
            List of log entries
        """
        entries = self.entries

        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]

        if tool_name:
            entries = [e for e in entries if e["tool"] == tool_name]

        return entries[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics.

        Returns:
            Dict with statistics
        """
        total = len(self.entries)
        by_type = {}
        by_tool = {}

        for entry in self.entries:
            event_type = entry["event_type"]
            tool = entry["tool"]

            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_tool[tool] = by_tool.get(tool, 0) + 1

        return {
            "total_events": total,
            "by_type": by_type,
            "by_tool": by_tool
        }

    def clear(self):
        """Clear in-memory audit log."""
        self.entries = []

    def export(self, output_file: Path):
        """Export audit log to file.

        Args:
            output_file: Path to export file
        """
        output_file.write_text(json.dumps(self.entries, indent=2))
        logger.info(f"Exported {len(self.entries)} audit entries to {output_file}")


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_file: Optional[Path] = None) -> AuditLogger:
    """Get or create global audit logger.

    Args:
        log_file: Path to audit log file

    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        from config.settings import settings
        if log_file is None:
            log_file = settings.logs_dir / "audit.log"
        _audit_logger = AuditLogger(log_file=log_file)
    return _audit_logger
