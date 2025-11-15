"""Improved terminal command execution tool with better LLM guidance."""

import subprocess
import shlex
import os
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .base import BaseTool, ToolResult, ToolStatus, ToolExecutionError
from config.settings import settings

logger = logging.getLogger(__name__)


class TerminalToolV2(BaseTool):
    """Enhanced terminal tool with better LLM-friendly descriptions and error messages."""

    # Safe commands that are generally allowed
    WHITELIST = {
        # Version control
        'git', 'gh', 'svn',
        # Package managers
        'npm', 'yarn', 'pnpm', 'pip', 'pipenv', 'poetry', 'cargo', 'go',
        # Build tools
        'make', 'cmake', 'gradle', 'maven', 'ant',
        # Programming languages
        'python', 'python3', 'node', 'nodejs', 'ruby', 'java', 'javac',
        # File viewers (read-only)
        'cat', 'less', 'more', 'head', 'tail', 'grep', 'find', 'ls', 'dir',
        'tree', 'file', 'wc', 'diff',
        # Directory navigation
        'cd', 'pwd', 'mkdir',
        # Text processing
        'echo', 'printf', 'sed', 'awk', 'cut', 'sort', 'uniq',
        # Network tools (safe)
        'ping', 'curl', 'wget', 'telnet',
        # System info (read-only)
        'uname', 'whoami', 'date', 'uptime', 'hostname',
        # Docker (if enabled)
        'docker', 'docker-compose',
        # Pentest tools (CEH certified user)
        'nmap', 'sqlmap', 'ffuf', 'gospider', 'nuclei', 'subfinder', 'httpx',
        'amass', 'nikto', 'dirb', 'gobuster', 'wfuzz',
    }

    # Dangerous commands that should never be allowed
    BLACKLIST = {
        'rm', 'rmdir', 'del', 'erase',  # File deletion
        'format', 'mkfs', 'dd',  # Disk formatting
        'shutdown', 'reboot', 'poweroff', 'halt',  # System control
        'kill', 'killall', 'pkill',  # Process killing
        'chmod', 'chown', 'chgrp',  # Permission changes
        'iptables', 'ufw', 'firewall-cmd',  # Firewall
        'systemctl', 'service', 'init',  # Service management
        'useradd', 'userdel', 'usermod', 'passwd',  # User management
        'su', 'sudo',  # Privilege escalation
        'mount', 'umount',  # Filesystem mounting
    }

    def __init__(self, working_directory: Optional[str] = None, timeout: int = None):
        """Initialize terminal tool.

        Args:
            working_directory: Working directory for commands
            timeout: Command timeout in seconds (default from settings)
        """
        super().__init__()
        self.working_dir = Path(working_directory or settings.working_directory)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout or settings.command_timeout_seconds
        self.is_windows = platform.system() == 'Windows'

    @property
    def name(self) -> str:
        return "run_terminal_command"

    @property
    def description(self) -> str:
        return """Execute terminal/shell commands safely.

Use this when you need to:
- Run git commands (git status, git add, git commit, git push, etc.)
- Execute package manager commands (npm install, pip install, cargo build, etc.)
- Run build tools (make, gradle, maven, etc.)
- Execute scripts (python script.py, node app.js, etc.)
- View file contents (cat, ls, grep, find, etc.)
- Process text (sed, awk, sort, etc.)
- Get system information (whoami, hostname, uname, etc.)
- Use network tools (ping, curl, wget, etc.)

IMPORTANT - Common commands:
• List files: ls -la or dir
• Git status: git status
• Install Python package: pip install package_name
• Install Node package: npm install package_name
• Run Python script: python script.py
• Run Node script: node app.js
• View file: cat filename
• Search in files: grep "pattern" filename

Commands are validated for safety. Dangerous operations like rm, sudo, chmod are blocked.
If your command is blocked, try using the appropriate file_system tool instead."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "command": {
                "type": "string",
                "description": """The command to execute. Examples:
- 'ls -la' (list files)
- 'git status' (check git status)
- 'python script.py' (run Python script)
- 'npm install' (install dependencies)
- 'cat file.txt' (view file contents)

Only safe commands are allowed. The command will be validated before execution.""",
                "required": True
            }
        }

    @property
    def category(self) -> str:
        return "terminal"

    @property
    def examples(self) -> List[str]:
        return [
            "List files: {'command': 'ls -la'}",
            "Git status: {'command': 'git status'}",
            "Install Python package: {'command': 'pip install requests'}",
            "Run Python script: {'command': 'python script.py'}",
            "Check Node version: {'command': 'node --version'}",
            "View file: {'command': 'cat config.json'}",
            "Search files: {'command': 'grep \"TODO\" *.py'}",
            "Git commit: {'command': 'git commit -m \"Update files\"'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute terminal command.

        Args:
            command: Command string to execute

        Returns:
            ToolResult with command output or error
        """
        command = kwargs.get("command", "")

        if not command:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No command provided. Please specify a command to execute."
            )

        # Validate command safety
        is_safe, reason = self._validate_command(command)
        if not is_safe:
            logger.warning(f"Blocked unsafe command: {command} - {reason}")

            # Provide helpful suggestions based on the blocked command
            suggestion = self._get_command_suggestion(command)
            error_msg = f"❌ Command blocked for safety: {reason}"
            if suggestion:
                error_msg += f"\n\n💡 Suggestion: {suggestion}"

            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=error_msg
            )

        # Execute command
        try:
            result = self._execute_command(command)
            return result
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"⏱️ Command timeout after {self.timeout} seconds. The command took too long to complete."
            )
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"❌ Command execution failed: {str(e)}"
            )

    def _get_command_suggestion(self, command: str) -> Optional[str]:
        """Get helpful suggestion for blocked command.

        Args:
            command: The blocked command

        Returns:
            Helpful suggestion or None
        """
        command_lower = command.lower()

        # Suggestions for common blocked operations
        if 'rm ' in command_lower or 'del ' in command_lower:
            return "Use the 'delete_file' tool instead to safely delete files or directories."

        if 'mkdir' in command_lower:
            return "Use the 'create_directory' tool instead to create directories."

        if 'cat ' in command_lower or 'type ' in command_lower:
            return "Use the 'read_file' tool instead to read file contents."

        if 'chmod' in command_lower or 'chown' in command_lower:
            return "Permission changes are not allowed for security reasons."

        if 'sudo' in command_lower or 'su ' in command_lower:
            return "Privilege escalation is not allowed for security reasons."

        # Check if command is not in whitelist
        try:
            parts = shlex.split(command)
            if parts:
                base_cmd = Path(parts[0]).stem.lower()
                if base_cmd not in self.WHITELIST:
                    allowed_cmds = ', '.join(sorted(self.WHITELIST)[:20])  # Show first 20
                    return f"This command is not in the allowed list. Safe commands include: {allowed_cmds}... (and more)"
        except:
            pass

        return None

    def _validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """Validate command for safety.

        Args:
            command: Command string

        Returns:
            Tuple of (is_safe, reason_if_not)
        """
        # Parse command to get the base command
        try:
            if self.is_windows:
                # On Windows, don't split if it's a complex command
                parts = command.strip().split()
                if not parts:
                    return False, "Empty command"
                base_cmd = parts[0].lower()
            else:
                parts = shlex.split(command)
                if not parts:
                    return False, "Empty command"
                base_cmd = parts[0].lower()
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

        # Extract just the command name without path
        base_cmd = Path(base_cmd).stem.lower()

        # Check blacklist first
        if base_cmd in self.BLACKLIST:
            return False, f"'{base_cmd}' is a dangerous command and is not allowed"

        # Check for dangerous patterns
        dangerous_patterns = [
            ('rm -rf /', 'Recursive deletion of root directory'),
            ('rm -rf *', 'Recursive deletion of all files'),
            ('> /dev/sda', 'Direct disk access'),
            ('dd if=', 'Disk duplication/formatting'),
            (':(){:|:&};:', 'Fork bomb detected'),
            ('mkfs.', 'Filesystem formatting'),
        ]

        command_lower = command.lower()
        for pattern, description in dangerous_patterns:
            if pattern in command_lower:
                return False, f"Dangerous pattern detected: {description}"

        # Check whitelist
        if base_cmd not in self.WHITELIST:
            return False, f"'{base_cmd}' is not in the allowed commands list"

        # Additional checks for specific commands
        if base_cmd == 'rm' and ('-rf' in command or '-fr' in command):
            return False, "Recursive force delete is not allowed"

        if base_cmd in ['curl', 'wget'] and any(x in command for x in ['|', '>', '>>']):
            return False, "Output redirection with network tools is not allowed"

        return True, None

    def _execute_command(self, command: str) -> ToolResult:
        """Execute command using subprocess.

        Args:
            command: Command to execute

        Returns:
            ToolResult
        """
        logger.info(f"Executing command: {command}")

        # Prepare environment
        env = os.environ.copy()

        # Execute command
        if self.is_windows:
            # On Windows, use shell=True but be careful
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.working_dir),
                env=env,
                text=True
            )
        else:
            # On Unix, use shell=True for complex commands
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.working_dir),
                env=env,
                text=True
            )

        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            raise

        # Check return code
        if process.returncode == 0:
            output_text = stdout.strip() if stdout else "✅ Command completed successfully"
            if stderr:
                output_text += f"\n\n⚠️ Warnings/Info:\n{stderr.strip()}"

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=output_text,
                metadata={
                    "command": command,
                    "return_code": process.returncode,
                    "working_dir": str(self.working_dir)
                }
            )
        else:
            error_text = stderr.strip() if stderr else stdout.strip() if stdout else "Command failed"

            # Add helpful context to common errors
            helpful_error = self._add_error_context(command, error_text, process.returncode)

            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"❌ Command failed (exit code {process.returncode}):\n{helpful_error}",
                metadata={
                    "command": command,
                    "return_code": process.returncode,
                    "working_dir": str(self.working_dir)
                }
            )

    def _add_error_context(self, command: str, error_text: str, return_code: int) -> str:
        """Add helpful context to error messages.

        Args:
            command: The command that failed
            error_text: The error message
            return_code: The exit code

        Returns:
            Enhanced error message with context
        """
        enhanced = error_text

        # Common git errors
        if command.startswith('git'):
            if 'not a git repository' in error_text.lower():
                enhanced += "\n\n💡 This directory is not a git repository. Run 'git init' first or cd to a git repository."
            elif 'no changes added to commit' in error_text.lower():
                enhanced += "\n\n💡 No files are staged for commit. Use 'git add <file>' to stage files first."
            elif 'nothing to commit' in error_text.lower():
                enhanced += "\n\n💡 There are no changes to commit. All changes are already committed."

        # Package manager errors
        elif command.startswith(('pip', 'npm', 'yarn')):
            if 'not found' in error_text.lower() or 'no such file' in error_text.lower():
                enhanced += "\n\n💡 Package not found. Check the package name or ensure you have internet connection."
            elif 'permission denied' in error_text.lower():
                enhanced += "\n\n💡 Permission denied. You may need to use a virtual environment or check write permissions."

        # Python execution errors
        elif command.startswith('python'):
            if 'no such file' in error_text.lower():
                enhanced += "\n\n💡 Python file not found. Check the file path and ensure the file exists."
            elif 'modulenotfounderror' in error_text.lower():
                enhanced += "\n\n💡 Python module not found. Install required packages using pip."

        # File not found errors
        elif 'no such file or directory' in error_text.lower():
            enhanced += "\n\n💡 File or directory not found. Check the path and ensure it exists."

        return enhanced

    @property
    def is_dangerous(self) -> bool:
        return True

    @property
    def requires_confirmation(self) -> bool:
        return False  # Already validated via whitelist


class ShellToolV2(TerminalToolV2):
    """Alias for TerminalToolV2 with a different name."""

    @property
    def name(self) -> str:
        return "run_shell_command"

    @property
    def description(self) -> str:
        return "Execute shell commands (alias for terminal tool). " + super().description
