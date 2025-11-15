"""Enhanced logging configuration with rotation and structured logging support.

Provides log rotation to prevent unbounded log file growth and optional JSON formatting.
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


def setup_logging(
    log_dir: str = "logs",
    log_file: str = "agent.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = False,
    console_level: str = "INFO",
    file_level: str = "DEBUG"
) -> None:
    """Setup logging with rotation and optional JSON formatting.

    Args:
        log_dir: Directory for log files
        log_file: Name of log file
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        json_format: Use JSON formatting for file logs
        console_level: Logging level for console output
        file_level: Logging level for file output
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with color support (using rich if available)
    try:
        from rich.logging import RichHandler

        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False,  # Rich handles time display
            show_path=False
        )
    except ImportError:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

    console_handler.setLevel(getattr(logging, console_level.upper()))
    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))

    # Set formatter
    if json_format:
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(f"Logging configured: dir={log_dir}, file={log_file}, max_size={max_bytes/1024/1024}MB, backups={backup_count}")


def setup_production_logging() -> None:
    """Setup production-ready logging with JSON format and rotation."""
    setup_logging(
        log_dir="logs",
        log_file="radira.log",
        max_bytes=50 * 1024 * 1024,  # 50MB per file
        backup_count=10,  # Keep 10 backup files
        json_format=True,
        console_level="INFO",
        file_level="DEBUG"
    )


def setup_development_logging() -> None:
    """Setup development-friendly logging with rich formatting."""
    setup_logging(
        log_dir="logs",
        log_file="dev.log",
        max_bytes=10 * 1024 * 1024,  # 10MB per file
        backup_count=3,
        json_format=False,
        console_level="DEBUG",
        file_level="DEBUG"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
