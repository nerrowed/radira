"""Configuration settings for AI Autonomous Agent with Pydantic validation."""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import validator, Field
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
WORKSPACE_DIR = BASE_DIR / "workspace"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
WORKSPACE_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings with Pydantic validation.

    This class provides:
    - Type safety for all configuration values
    - Validation of required fields
    - Default values with documentation
    - Environment variable parsing
    """

    # ==================== Base Paths ====================
    base_dir: Path = Field(default=BASE_DIR, description="Base project directory")
    logs_dir: Path = Field(default=LOGS_DIR, description="Logs directory")
    workspace_dir: Path = Field(default=WORKSPACE_DIR, description="Workspace directory")

    # ==================== Groq API Configuration ====================
    groq_api_key: str = Field(
        ...,  # Required field
        env="GROQ_API_KEY",
        description="Groq API key for LLM access"
    )
    groq_model: str = Field(
        default="llama-3.1-70b-versatile",
        env="GROQ_MODEL",
        description="Default Groq model to use"
    )
    groq_fast_model: str = Field(
        default="gemma2-9b-it",
        env="GROQ_FAST_MODEL",
        description="Fast model for simple tasks"
    )

    # ==================== Agent Configuration ====================
    agent_name: str = Field(
        default="AutonomousAgent",
        env="AGENT_NAME",
        description="Agent name"
    )
    agent_mode: str = Field(
        default="autonomous",
        env="AGENT_MODE",
        description="Agent mode (autonomous, interactive, etc)"
    )
    max_iterations: int = Field(
        default=10,
        ge=1,  # Greater than or equal to 1
        le=50,  # Less than or equal to 50
        env="MAX_ITERATIONS",
        description="Maximum iterations for task execution"
    )
    enable_self_improve: bool = Field(
        default=True,
        env="ENABLE_SELF_IMPROVE",
        description="Enable self-improvement features"
    )
    iteration_delay_seconds: float = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        env="ITERATION_DELAY_SECONDS",
        description="Delay between iterations (seconds)"
    )

    # ==================== Token Budget Configuration ====================
    max_tokens_per_response: int = Field(
        default=2048,  # Increased from 1024 for better responses
        ge=256,
        le=8192,
        env="MAX_TOKENS_PER_RESPONSE",
        description="Maximum tokens per LLM response"
    )
    max_total_tokens_per_task: int = Field(
        default=20000,
        ge=1000,
        le=100000,
        env="MAX_TOTAL_TOKENS_PER_TASK",
        description="Total token budget per task"
    )
    history_keep_last_n: int = Field(
        default=5,  # Increased from 3 for better context
        ge=1,
        le=20,
        env="HISTORY_KEEP_LAST_N",
        description="Number of recent iterations to keep in context"
    )

    # ==================== Orchestrator Configuration ====================
    use_dual_orchestrator: bool = Field(
        default=True,
        env="USE_DUAL_ORCHESTRATOR",
        description="Use new dual orchestrator"
    )
    enable_task_classification: bool = Field(
        default=True,
        env="ENABLE_TASK_CLASSIFICATION",
        description="Enable task routing"
    )
    enable_answer_validation: bool = Field(
        default=True,
        env="ENABLE_ANSWER_VALIDATION",
        description="Enable auto-stop when answer sufficient"
    )

    # ==================== System Access Configuration ====================
    allow_system_access: bool = Field(
        default=False,  # Changed to False for safety
        env="ALLOW_SYSTEM_ACCESS",
        description="Allow system-level access (DANGER: set to False in production)"
    )
    sandbox_mode: bool = Field(
        default=True,
        env="SANDBOX_MODE",
        description="Enable sandbox mode for safety"
    )
    working_directory: str = Field(
        default=str(WORKSPACE_DIR),
        env="WORKING_DIRECTORY",
        description="Working directory for file operations"
    )

    # ==================== Safety Configuration ====================
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        env="MAX_FILE_SIZE_MB",
        description="Maximum file size in MB"
    )
    allowed_extensions: str = Field(
        default=".py,.txt,.md,.json,.yaml,.yml,.sh,.js,.ts,.html,.css,.jsx,.tsx,.vue",
        env="ALLOWED_EXTENSIONS",
        description="Comma-separated list of allowed file extensions"
    )
    blocked_paths: str = Field(
        default="/etc,/sys,/proc,/root,C:/Windows,C:/System32",
        env="BLOCKED_PATHS",
        description="Comma-separated list of blocked paths"
    )
    command_timeout_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        env="COMMAND_TIMEOUT_SECONDS",
        description="Command execution timeout in seconds"
    )

    # ==================== Database Configuration ====================
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    postgres_url: str = Field(
        default="postgresql://user:password@localhost:5432/agent_db",
        env="POSTGRES_URL",
        description="PostgreSQL connection URL"
    )
    chroma_db_path: str = Field(
        default=str(BASE_DIR / "chroma_db"),
        env="CHROMA_DB_PATH",
        description="ChromaDB storage path"
    )

    # ==================== API Server Configuration ====================
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        env="API_PORT",
        description="API server port"
    )
    api_reload: bool = Field(
        default=True,
        env="API_RELOAD",
        description="Enable API auto-reload in development"
    )

    # ==================== Logging Configuration ====================
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: str = Field(
        default=str(LOGS_DIR / "agent.log"),
        description="Log file path"
    )

    # ==================== Retry & Rate Limiting Configuration ====================
    api_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        env="API_MAX_RETRIES",
        description="Maximum API retry attempts"
    )
    api_retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        env="API_RETRY_DELAY",
        description="Initial retry delay in seconds (exponential backoff)"
    )
    api_timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        env="API_TIMEOUT_SECONDS",
        description="API request timeout in seconds"
    )
    rate_limit_requests_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        env="RATE_LIMIT_REQUESTS_PER_MINUTE",
        description="Maximum API requests per minute"
    )

    # ==================== Validators ====================

    @validator('groq_api_key')
    def validate_groq_api_key(cls, v):
        """Validate Groq API key is provided and not placeholder."""
        if not v:
            raise ValueError(
                "GROQ_API_KEY is required. Please set it in .env file."
            )
        if v == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY contains placeholder value. "
                "Please set your actual Groq API key in .env file."
            )
        if len(v) < 20:  # Groq API keys are typically longer
            raise ValueError(
                "GROQ_API_KEY appears to be invalid (too short). "
                "Please check your API key."
            )
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper

    @validator('working_directory')
    def validate_working_directory(cls, v):
        """Validate working directory exists or can be created."""
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(
                    f"Cannot create working directory {v}: {e}"
                )
        return v

    @validator('allowed_extensions')
    def validate_allowed_extensions(cls, v):
        """Ensure allowed extensions start with dot."""
        extensions = [ext.strip() for ext in v.split(',')]
        for ext in extensions:
            if not ext.startswith('.'):
                raise ValueError(
                    f"Extension must start with dot: {ext}"
                )
        return v

    @validator('api_port')
    def validate_api_port(cls, v):
        """Validate API port is in valid range."""
        if v < 1024:
            raise ValueError(
                "API port should be >= 1024 to avoid requiring root privileges"
            )
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True  # Validate on assignment too


# ==================== Create Global Settings Instance ====================

try:
    settings = Settings()
except Exception as e:
    # Provide helpful error message if settings fail to load
    print(f"❌ Configuration Error: {e}")
    print("\nPlease check your .env file and ensure all required values are set.")
    print("See .env.example for reference.")
    raise


# ==================== Backward Compatibility Constants ====================
# Keep old constants for backward compatibility with existing code

GROQ_API_KEY = settings.groq_api_key
GROQ_MODEL = settings.groq_model
AGENT_NAME = settings.agent_name
AGENT_MODE = settings.agent_mode
MAX_ITERATIONS = settings.max_iterations
ENABLE_SELF_IMPROVE = settings.enable_self_improve
ALLOW_SYSTEM_ACCESS = settings.allow_system_access
SANDBOX_MODE = settings.sandbox_mode
WORKING_DIRECTORY = settings.working_directory
MAX_FILE_SIZE_MB = settings.max_file_size_mb
ALLOWED_EXTENSIONS = settings.allowed_extensions
BLOCKED_PATHS = settings.blocked_paths
REDIS_URL = settings.redis_url
POSTGRES_URL = settings.postgres_url
LOG_LEVEL = settings.log_level
LOG_FILE = settings.log_file


# ==================== Helper Functions ====================

def get_allowed_extensions_list() -> List[str]:
    """Get list of allowed file extensions.

    Returns:
        List of extensions with dots (e.g., ['.py', '.txt'])
    """
    return [ext.strip() for ext in settings.allowed_extensions.split(',')]


def get_blocked_paths_list() -> List[Path]:
    """Get list of blocked paths as Path objects.

    Returns:
        List of Path objects for blocked paths
    """
    return [Path(p.strip()) for p in settings.blocked_paths.split(',')]


def is_path_blocked(path: str) -> bool:
    """Check if a path is blocked.

    Args:
        path: Path to check

    Returns:
        True if path is blocked
    """
    path_obj = Path(path).resolve()
    blocked = get_blocked_paths_list()

    for blocked_path in blocked:
        try:
            # Check if path is under blocked directory
            path_obj.relative_to(blocked_path)
            return True
        except ValueError:
            # Not under this blocked path
            continue

    return False


def reload_settings():
    """Reload settings from environment variables.

    Useful for testing or dynamic configuration changes.
    """
    global settings
    from dotenv import load_dotenv
    load_dotenv(override=True)
    settings = Settings()
