"""Terminal command execution tool with safety controls."""

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


class TerminalTool(BaseTool):
    """Tool for safe terminal command execution."""

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
        'cd', 'pwd', 'mkdir', 'rmdir',
        # Text processing
        'echo', 'printf', 'sed', 'awk', 'cut', 'sort', 'uniq',
        # Network tools (safe)
        'ping', 'curl', 'wget', 'telnet',
        # System info (read-only)
        'uname', 'whoami', 'date', 'uptime', 'hostname',
        # Docker (if enabled)
        'docker', 'docker-compose',
        # Pentest tools (CEH certified user)
        'nmap', 'sqlmap', 'ffuf', 'gospider', 'nuclei', 'subfinder', 'httpx', 'amass', 'nikto', 'dirb', 'gobuster', 'wfuzz',
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
        return "terminal"

    @property
    def description(self) -> str:
        return "Execute safe terminal commands like git, npm, python, etc. with output capture"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "command": {
                "type": "string",
                "description": "Command to execute (will be validated for safety)",
                "required": True
            },
            "check_output": {
                "type": "boolean",
                "description": "Whether to return command output (default: true)",
                "required": False
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
            "Install package: {'command': 'pip install requests'}",
            "Run Python script: {'command': 'python script.py'}",
            "Check Node version: {'command': 'node --version'}"
        ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute terminal command.

        Args:
            command: Command string to execute
            check_output: Whether to return output

        Returns:
            ToolResult with command output or error
        """
        command = kwargs.get("command", "")
        check_output = kwargs.get("check_output", True)

        if not command:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No command provided"
            )

        # Validate command safety
        is_safe, reason = self._validate_command(command)
        if not is_safe:
            logger.warning(f"Blocked unsafe command: {command} - {reason}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Command blocked for safety: {reason}"
            )

        # Execute command
        try:
            result = self._execute_command(command, check_output)
            return result
        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Command timeout after {self.timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Command execution failed: {str(e)}"
            )

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
            return False, f"Command '{base_cmd}' is blacklisted"

        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf /',
            'rm -rf *',
            '> /dev/sda',
            'dd if=',
            ':(){:|:&};:',  # Fork bomb
            'mkfs.',
        ]

        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False, f"Dangerous pattern detected: {pattern}"

        # Check whitelist
        if base_cmd not in self.WHITELIST:
            return False, f"Command '{base_cmd}' not in whitelist. Allowed: {', '.join(sorted(self.WHITELIST))}"

        # Additional checks for specific commands
        if base_cmd == 'rm' and ('-rf' in command or '-fr' in command):
            return False, "Recursive force delete not allowed"

        if base_cmd in ['curl', 'wget'] and any(x in command for x in ['|', '>', '>>']):
            return False, "Command output redirection not allowed for network tools"

        return True, None

    def _execute_command(self, command: str, check_output: bool = True) -> ToolResult:
        """Execute command using subprocess.

        Args:
            command: Command to execute
            check_output: Whether to capture output

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
                stdout=subprocess.PIPE if check_output else None,
                stderr=subprocess.PIPE if check_output else None,
                cwd=str(self.working_dir),
                env=env,
                text=True
            )
        else:
            # On Unix, use shell=True for complex commands
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE if check_output else None,
                stderr=subprocess.PIPE if check_output else None,
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
            output_text = stdout.strip() if stdout else "Command completed successfully"
            if stderr:
                output_text += f"\n[stderr]: {stderr.strip()}"

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
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Command failed with exit code {process.returncode}: {error_text}",
                metadata={
                    "command": command,
                    "return_code": process.returncode,
                    "working_dir": str(self.working_dir)
                }
            )

    @property
    def is_dangerous(self) -> bool:
        return True

    @property
    def requires_confirmation(self) -> bool:
        return False  # Already validated via whitelist


class ShellTool(TerminalTool):
    """Alias for TerminalTool with a different name."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute shell commands (alias for terminal tool)"
