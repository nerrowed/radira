"""Configuration settings for AI Autonomous Agent."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
WORKSPACE_DIR = BASE_DIR / "workspace"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
WORKSPACE_DIR.mkdir(exist_ok=True)


class Settings:
    """Application settings."""

    # Base paths
    base_dir = BASE_DIR
    logs_dir = LOGS_DIR
    workspace_dir = WORKSPACE_DIR

    # Groq API Configuration
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL")
    groq_fast_model = os.getenv("GROQ_FAST_MODEL")

    # Agent Configuration
    agent_name = os.getenv("AGENT_NAME", "AutonomousAgent")
    agent_mode = os.getenv("AGENT_MODE", "autonomous")
    max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
    enable_self_improve = os.getenv("ENABLE_SELF_IMPROVE", "true").lower() == "true"
    iteration_delay_seconds = float(os.getenv("ITERATION_DELAY_SECONDS", "2.0"))

    # Token Budget Configuration
    max_tokens_per_response = int(os.getenv("MAX_TOKENS_PER_RESPONSE", "1024"))  # Reduced from 4096
    max_total_tokens_per_task = int(os.getenv("MAX_TOTAL_TOKENS_PER_TASK", "20000"))  # 20k limit
    history_keep_last_n = int(os.getenv("HISTORY_KEEP_LAST_N", "3"))  # Only keep last 3 iterations in context

    # Orchestrator Configuration
    use_dual_orchestrator = os.getenv("USE_DUAL_ORCHESTRATOR", "true").lower() == "true"  # Use new dual orchestrator
    enable_task_classification = os.getenv("ENABLE_TASK_CLASSIFICATION", "true").lower() == "true"  # Enable task routing
    enable_answer_validation = os.getenv("ENABLE_ANSWER_VALIDATION", "true").lower() == "true"  # Enable auto-stop

    # System Access Configuration
    allow_system_access = os.getenv("ALLOW_SYSTEM_ACCESS", "true").lower() == "true"
    sandbox_mode = os.getenv("SANDBOX_MODE", "true").lower() == "true"
    working_directory = os.getenv("WORKING_DIRECTORY", str(WORKSPACE_DIR))

    # Safety Configuration
    max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    allowed_extensions = os.getenv(
        "ALLOWED_EXTENSIONS",
        ".py,.txt,.md,.json,.yaml,.yml,.sh,.js,.ts,.html,.css,.jsx,.tsx,.vue"
    )
    blocked_paths = os.getenv(
        "BLOCKED_PATHS",
        "/etc,/sys,/proc,/root,C:/Windows,C:/System32"
    )
    command_timeout_seconds = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "300"))

    # Database Configuration
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://user:password@localhost:5432/agent_db"
    )
    chroma_db_path = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "chroma_db"))

    # API Server Configuration
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    api_reload = os.getenv("API_RELOAD", "true").lower() == "true"

    # Logging Configuration
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = str(LOGS_DIR / "agent.log")


# Create global settings instance
settings = Settings()


# Backward compatibility - keep old constants
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
