"""File system operations tool with safety checks."""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .base import BaseTool, ToolResult, ToolStatus, ToolExecutionError
from config.settings import settings
from agent.state.error_memory import ErrorMemory

logger = logging.getLogger(__name__)


class FileSystemTool(BaseTool):
    """Tool for safe file system operations."""

    def __init__(self, working_directory: Optional[str] = None):
        """Initialize file system tool.

        Args:
            working_directory: Base directory for operations (default from settings)
        """
        super().__init__()
        self.working_dir = Path(working_directory or settings.working_directory).resolve()
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Safety settings
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.allowed_extensions = set(
            ext.strip() for ext in settings.allowed_extensions.split(',')
        )
        self.blocked_paths = [
            Path(p.strip()) for p in settings.blocked_paths.split(',')
        ]

        # Error learning system
        self.error_memory = ErrorMemory(storage_dir=str(self.working_dir))

    @property
    def name(self) -> str:
        return "file_system"

    @property
    def description(self) -> str:
        return "Read, write, list, and manage files and directories safely within the workspace"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "operation": {
                "type": "string",
                "description": "Operation to perform: read, write, list, delete, mkdir, exists, search",
                "required": True
            },
            "path": {
                "type": "string",
                "description": "File or directory path (relative to workspace)",
                "required": True
            },
            "content": {
                "type": "string",
                "description": "Content for write operation",
                "required": False
            },
            "pattern": {
                "type": "string",
                "description": "Search pattern for search operation",
                "required": False
            }
        }

    @property
    def category(self) -> str:
        return "file_system"

    @property
    def examples(self) -> List[str]:
        return [
            "Read file: {'operation': 'read', 'path': 'example.txt'}",
            "Write file: {'operation': 'write', 'path': 'output.txt', 'content': 'Hello World'}",
            "List directory: {'operation': 'list', 'path': '.'}",
            "Create directory: {'operation': 'mkdir', 'path': 'new_folder'}",
            "Search files: {'operation': 'search', 'path': '.', 'pattern': '*.py'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute file system operation.

        Args:
            operation: Operation type
            path: Target path
            content: Content for write operations
            pattern: Pattern for search operations

        Returns:
            ToolResult
        """
        operation = kwargs.get("operation")
        path_str = kwargs.get("path", "")

        # Resolve and validate path
        try:
            target_path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

        # Execute operation
        operation_map = {
            "read": self._read_file,
            "write": self._write_file,
            "list": self._list_directory,
            "delete": self._delete,
            "mkdir": self._make_directory,
            "exists": self._check_exists,
            "search": self._search_files,
        }

        if operation not in operation_map:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Unknown operation: {operation}. Available: {', '.join(operation_map.keys())}"
            )

        try:
            # Remove 'operation' and 'path' from kwargs to avoid conflicts
            clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['operation', 'path']}
            return operation_map[operation](target_path, **clean_kwargs)
        except Exception as e:
            logger.error(f"File system operation '{operation}' failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Operation failed: {str(e)}"
            )

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve and validate path.

        Args:
            path_str: Path string

        Returns:
            Resolved Path object

        Raises:
            ToolExecutionError: If path is invalid or blocked
        """
        # Handle empty path
        if not path_str:
            return self.working_dir

        # Create path relative to working directory
        if Path(path_str).is_absolute():
            target = Path(path_str)
        else:
            target = self.working_dir / path_str

        # Resolve to absolute path
        try:
            target = target.resolve()
        except Exception as e:
            raise ToolExecutionError(f"Invalid path: {e}")

        # Security check: must be within working directory (sandbox mode)
        if settings.sandbox_mode:
            try:
                target.relative_to(self.working_dir)
            except ValueError:
                raise ToolExecutionError(
                    f"Path '{target}' is outside workspace '{self.working_dir}'. "
                    f"Sandbox mode is enabled."
                )

        # Check blocked paths
        for blocked in self.blocked_paths:
            try:
                target.relative_to(blocked)
                raise ToolExecutionError(f"Access to '{blocked}' is blocked for safety")
            except ValueError:
                # Not relative to blocked path, ok to continue
                pass

        return target

    def _check_extension(self, path: Path) -> bool:
        """Check if file extension is allowed.

        Args:
            path: File path

        Returns:
            True if allowed
        """
        if not self.allowed_extensions:
            return True
        return path.suffix in self.allowed_extensions

    def _log_and_return_error(
        self,
        operation: str,
        error_message: str,
        path: Optional[Path] = None,
        **extra_metadata
    ) -> ToolResult:
        """Log error to error memory and return ToolResult.

        Args:
            operation: Operation name
            error_message: Error description
            path: Path involved (if any)
            **extra_metadata: Additional context

        Returns:
            ToolResult with ERROR status
        """
        # Build metadata
        metadata = extra_metadata.copy()
        if path:
            metadata["path"] = str(path)

        # Log to error memory and get remediation
        remediation = None
        try:
            error_id = self.error_memory.log_error(
                tool_name=self.name,
                operation=operation,
                error_message=error_message,
                **metadata
            )

            # Get remediation suggestion from the logged error
            error_record = next(
                (e for e in self.error_memory.errors if e['id'] == error_id),
                None
            )
            if error_record and 'remediation' in error_record:
                remediation = error_record['remediation']

        except Exception as e:
            logger.warning(f"Failed to log error to memory: {e}")

        # Build error message with remediation
        full_error = error_message
        if remediation:
            full_error += f"\n\n💡 Suggested fix: {remediation['suggestion']}"

        # Return error result with remediation in metadata
        return ToolResult(
            status=ToolStatus.ERROR,
            output=None,
            error=full_error,
            metadata={"remediation": remediation} if remediation else None
        )

    def _read_file(self, path: Path, **kwargs) -> ToolResult:
        """Read file contents."""
        if not path.exists():
            return self._log_and_return_error(
                operation="read",
                error_message=f"File does not exist: {path}",
                path=path
            )

        if not path.is_file():
            return self._log_and_return_error(
                operation="read",
                error_message=f"Not a file: {path}",
                path=path
            )

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            return self._log_and_return_error(
                operation="read",
                error_message=f"File too large: {file_size / 1024 / 1024:.2f}MB (max: {self.max_file_size / 1024 / 1024}MB)",
                path=path,
                file_size=file_size,
                max_size=self.max_file_size
            )

        # Read file
        try:
            content = path.read_text(encoding='utf-8')
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=content,
                metadata={"path": str(path), "size": file_size}
            )
        except UnicodeDecodeError:
            return self._log_and_return_error(
                operation="read",
                error_message="File is not text-readable (binary file?)",
                path=path,
                file_size=file_size
            )

    def _write_file(self, path: Path, **kwargs) -> ToolResult:
        """Write content to file."""
        content = kwargs.get("content", "")

        # Check extension
        if not self._check_extension(path):
            return self._log_and_return_error(
                operation="write",
                error_message=f"File extension '{path.suffix}' not allowed. Allowed: {self.allowed_extensions}",
                path=path,
                extension=path.suffix,
                allowed_extensions=list(self.allowed_extensions)
            )

        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            path.write_text(content, encoding='utf-8')
            file_size = path.stat().st_size
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"File written successfully: {path}",
                metadata={"path": str(path), "size": file_size}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="write",
                error_message=f"Failed to write file: {e}",
                path=path,
                content_length=len(content)
            )

    def _list_directory(self, path: Path, **kwargs) -> ToolResult:
        """List directory contents."""
        if not path.exists():
            return self._log_and_return_error(
                operation="list",
                error_message=f"Directory does not exist: {path}",
                path=path
            )

        if not path.is_dir():
            return self._log_and_return_error(
                operation="list",
                error_message=f"Not a directory: {path}",
                path=path
            )

        try:
            items = []
            for item in sorted(path.iterdir()):
                item_type = "dir" if item.is_dir() else "file"
                size = item.stat().st_size if item.is_file() else 0
                
                # Resolve item path to handle symlinks
                try:
                    item_resolved = item.resolve()
                    # Try to get relative path, fallback to absolute if outside workspace
                    try:
                        relative_path = str(item_resolved.relative_to(self.working_dir))
                    except ValueError:
                        # Item is outside workspace (symlink or absolute path issue)
                        # Use relative path from the directory being listed instead
                        relative_path = str(item.relative_to(path))
                except Exception:
                    # Fallback: use item name if resolution fails
                    relative_path = item.name
                
                items.append({
                    "name": item.name,
                    "type": item_type,
                    "size": size,
                    "path": relative_path
                })

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=items,
                metadata={"path": str(path), "count": len(items)}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="list",
                error_message=f"Failed to list directory: {e}",
                path=path
            )

    def _delete(self, path: Path, **kwargs) -> ToolResult:
        """Delete file or directory."""
        if not path.exists():
            return self._log_and_return_error(
                operation="delete",
                error_message=f"Path does not exist: {path}",
                path=path
            )

        try:
            if path.is_file():
                file_size = path.stat().st_size
                path.unlink()
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output=f"File deleted: {path}"
                )
            elif path.is_dir():
                shutil.rmtree(path)
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output=f"Directory deleted: {path}"
                )
        except Exception as e:
            item_type = "file" if path.is_file() else "directory"
            return self._log_and_return_error(
                operation="delete",
                error_message=f"Failed to delete: {e}",
                path=path,
                item_type=item_type
            )

    def _make_directory(self, path: Path, **kwargs) -> ToolResult:
        """Create directory."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"Directory created: {path}",
                metadata={"path": str(path)}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="mkdir",
                error_message=f"Failed to create directory: {e}",
                path=path
            )

    def _check_exists(self, path: Path, **kwargs) -> ToolResult:
        """Check if path exists."""
        exists = path.exists()
        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=exists,
            metadata={"path": str(path), "exists": exists}
        )

    def _search_files(self, path: Path, **kwargs) -> ToolResult:
        """Search for files matching pattern."""
        pattern = kwargs.get("pattern", "*")

        if not path.exists() or not path.is_dir():
            return self._log_and_return_error(
                operation="search",
                error_message=f"Invalid search directory: {path}",
                path=path,
                pattern=pattern
            )

        try:
            matches = []
            for item in path.rglob(pattern):
                if item.is_file():
                    # Resolve item path to handle symlinks
                    try:
                        item_resolved = item.resolve()
                        # Try to get relative path, fallback to absolute if outside workspace
                        try:
                            relative_path = str(item_resolved.relative_to(self.working_dir))
                        except ValueError:
                            # Item is outside workspace (symlink or absolute path issue)
                            # Use relative path from the search directory instead
                            relative_path = str(item.relative_to(path))
                    except Exception:
                        # Fallback: use item name if resolution fails
                        relative_path = item.name
                    
                    matches.append({
                        "name": item.name,
                        "path": relative_path,
                        "size": item.stat().st_size
                    })

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=matches,
                metadata={"pattern": pattern, "count": len(matches)}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="search",
                error_message=f"Search failed: {e}",
                path=path,
                pattern=pattern
            )

    @property
    def is_dangerous(self) -> bool:
        return True

    @property
    def requires_confirmation(self) -> bool:
        # Only delete operations require confirmation
        return False
