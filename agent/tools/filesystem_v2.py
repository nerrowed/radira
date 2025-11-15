"""Improved file system tools - split into individual operations for better LLM usability."""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .base import BaseTool, ToolResult, ToolStatus, ToolExecutionError
from config.settings import settings
from agent.state.error_memory import ErrorMemory

logger = logging.getLogger(__name__)


class BaseFileSystemTool(BaseTool):
    """Base class for file system tools with common functionality."""

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

    @property
    def category(self) -> str:
        return "file_system"

    @property
    def is_dangerous(self) -> bool:
        return True


class ReadFileTool(BaseFileSystemTool):
    """Tool specifically for reading file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return """Read the contents of a text file.

Use this when you need to:
- View the contents of a configuration file
- Read source code files
- Check log files
- Examine any text-based file

The file must be text-readable (not binary) and within size limits."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to read (relative to workspace or absolute)",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Read config file: {'path': 'config.json'}",
            "Read Python script: {'path': 'src/main.py'}",
            "Read log file: {'path': 'logs/app.log'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Read file contents."""
        path_str = kwargs.get("path", "")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

        if not path.exists():
            return self._log_and_return_error(
                operation="read",
                error_message=f"File does not exist: {path}",
                path=path
            )

        if not path.is_file():
            return self._log_and_return_error(
                operation="read",
                error_message=f"Not a file: {path}. Use 'list_directory' to view directory contents.",
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
                error_message="File is not text-readable (binary file). Cannot read binary files.",
                path=path,
                file_size=file_size
            )

    @property
    def requires_confirmation(self) -> bool:
        return False


class WriteFileTool(BaseFileSystemTool):
    """Tool specifically for writing content to files."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return """Write content to a file (creates new file or overwrites existing).

Use this when you need to:
- Create a new file with content
- Update/overwrite an existing file
- Save generated code or configuration
- Write output to a file

The file will be created if it doesn't exist. Parent directories will be created automatically.
WARNING: This will overwrite existing files without warning!"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to write (relative to workspace or absolute)",
                "required": True
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Create new file: {'path': 'output.txt', 'content': 'Hello World'}",
            "Write Python code: {'path': 'script.py', 'content': 'print(\"Hello\")'}",
            "Save JSON config: {'path': 'config.json', 'content': '{\"key\": \"value\"}'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Write content to file."""
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

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
                output=f"File written successfully: {path} ({file_size} bytes)",
                metadata={"path": str(path), "size": file_size}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="write",
                error_message=f"Failed to write file: {e}",
                path=path,
                content_length=len(content)
            )

    @property
    def requires_confirmation(self) -> bool:
        return False


class ListDirectoryTool(BaseFileSystemTool):
    """Tool specifically for listing directory contents."""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return """List all files and subdirectories in a directory.

Use this when you need to:
- See what files are in a folder
- Explore directory structure
- Check if a file exists in a directory
- Get file sizes and types

Returns a list of items with name, type (file/dir), size, and path."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to the directory to list (relative to workspace or absolute). Use '.' for current directory.",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "List current directory: {'path': '.'}",
            "List subdirectory: {'path': 'src'}",
            "List nested folder: {'path': 'src/components'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """List directory contents."""
        path_str = kwargs.get("path", ".")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

        if not path.exists():
            return self._log_and_return_error(
                operation="list",
                error_message=f"Directory does not exist: {path}",
                path=path
            )

        if not path.is_dir():
            return self._log_and_return_error(
                operation="list",
                error_message=f"Not a directory: {path}. Use 'read_file' to read file contents.",
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

    @property
    def requires_confirmation(self) -> bool:
        return False


class CreateDirectoryTool(BaseFileSystemTool):
    """Tool specifically for creating directories."""

    @property
    def name(self) -> str:
        return "create_directory"

    @property
    def description(self) -> str:
        return """Create a new directory (folder).

Use this when you need to:
- Create a new folder to organize files
- Set up a directory structure
- Create nested directories

Parent directories will be created automatically if they don't exist.
If the directory already exists, this operation will succeed (no error)."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to the directory to create (relative to workspace or absolute)",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Create simple directory: {'path': 'new_folder'}",
            "Create nested directories: {'path': 'src/components/ui'}",
            "Create in subdirectory: {'path': 'output/results'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Create directory."""
        path_str = kwargs.get("path", "")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

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

    @property
    def requires_confirmation(self) -> bool:
        return False


class DeleteFileTool(BaseFileSystemTool):
    """Tool specifically for deleting files or directories."""

    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return """Delete a file or directory.

Use this when you need to:
- Remove an unwanted file
- Delete a directory and all its contents
- Clean up temporary files

WARNING: This operation is permanent and cannot be undone!
For directories, all contents will be deleted recursively."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file or directory to delete (relative to workspace or absolute)",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Delete file: {'path': 'temp.txt'}",
            "Delete directory: {'path': 'old_folder'}",
            "Delete nested file: {'path': 'logs/old.log'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Delete file or directory."""
        path_str = kwargs.get("path", "")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

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
                    output=f"File deleted: {path} ({file_size} bytes)"
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
                error_message=f"Failed to delete {item_type}: {e}",
                path=path,
                item_type=item_type
            )

    @property
    def requires_confirmation(self) -> bool:
        return True  # Deletion should require confirmation


class SearchFilesTool(BaseFileSystemTool):
    """Tool specifically for searching files by pattern."""

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return """Search for files matching a pattern (glob pattern).

Use this when you need to:
- Find all files with a specific extension (e.g., *.py)
- Search for files with specific names
- Locate files matching a pattern

Supports wildcards:
- * matches any characters (e.g., *.txt finds all .txt files)
- ** matches any directory level (e.g., **/*.py finds all .py files recursively)
- ? matches single character

Returns a list of matching files with paths and sizes."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Directory to search in (relative to workspace or absolute). Use '.' for current directory.",
                "required": True
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match files (e.g., '*.py', '**/*.txt', 'test_*.py')",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Find Python files: {'path': '.', 'pattern': '*.py'}",
            "Find all text files recursively: {'path': '.', 'pattern': '**/*.txt'}",
            "Find test files: {'path': 'tests', 'pattern': 'test_*.py'}",
            "Find JSON configs: {'path': 'config', 'pattern': '*.json'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Search for files matching pattern."""
        path_str = kwargs.get("path", ".")
        pattern = kwargs.get("pattern", "*")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

        if not path.exists() or not path.is_dir():
            return self._log_and_return_error(
                operation="search",
                error_message=f"Invalid search directory: {path}. Must be an existing directory.",
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
                metadata={"pattern": pattern, "count": len(matches), "search_dir": str(path)}
            )
        except Exception as e:
            return self._log_and_return_error(
                operation="search",
                error_message=f"Search failed: {e}",
                path=path,
                pattern=pattern
            )

    @property
    def requires_confirmation(self) -> bool:
        return False


class CheckFileExistsTool(BaseFileSystemTool):
    """Tool specifically for checking if a file or directory exists."""

    @property
    def name(self) -> str:
        return "check_file_exists"

    @property
    def description(self) -> str:
        return """Check if a file or directory exists.

Use this when you need to:
- Verify a file exists before reading it
- Check if a directory exists before creating it
- Validate paths before operations

Returns True if the path exists, False otherwise."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "path": {
                "type": "string",
                "description": "Path to check (relative to workspace or absolute)",
                "required": True
            }
        }

    @property
    def examples(self) -> List[str]:
        return [
            "Check file: {'path': 'config.json'}",
            "Check directory: {'path': 'src'}",
            "Check nested path: {'path': 'src/utils/helpers.py'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Check if path exists."""
        path_str = kwargs.get("path", "")

        try:
            path = self._resolve_path(path_str)
        except ToolExecutionError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )

        exists = path.exists()
        item_type = "unknown"
        if exists:
            item_type = "directory" if path.is_dir() else "file"

        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=exists,
            metadata={
                "path": str(path),
                "exists": exists,
                "type": item_type
            }
        )

    @property
    def requires_confirmation(self) -> bool:
        return False
