"""Workspace setup and management utilities."""

import logging
from pathlib import Path
from typing import Dict
from config.settings import settings

logger = logging.getLogger(__name__)


def setup_workspace() -> Dict[str, Path]:
    """Setup workspace directory structure.

    Creates organized subdirectories for different types of generated content.

    Returns:
        Dict mapping directory names to Path objects
    """
    base_dir = Path(settings.working_directory)

    directories = {
        "base": base_dir,
        "generated_web": base_dir / "generated_web",
        "generated_code": base_dir / "generated_code",
        "pentest_output": base_dir / "pentest_output",
        "downloads": base_dir / "downloads",
        "temp": base_dir / "temp",
        "state": base_dir / ".state",
    }

    # Create all directories
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        if name != "base":  # Don't log base directory
            logger.debug(f"Workspace directory ready: {name} -> {path}")

    # Create .gitignore in workspace
    gitignore_path = base_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Workspace - Git ignore
*.tmp
*.temp
.state/
temp/
downloads/
"""
        gitignore_path.write_text(gitignore_content)
        logger.debug(f"Created workspace .gitignore")

    return directories


def get_output_directory(output_type: str) -> Path:
    """Get output directory for specific content type.

    Args:
        output_type: Type of output ('web', 'code', 'temp', 'downloads')

    Returns:
        Path to output directory
    """
    base_dir = Path(settings.working_directory)

    type_mapping = {
        "web": "generated_web",
        "code": "generated_code",
        "temp": "temp",
        "downloads": "downloads",
    }

    folder_name = type_mapping.get(output_type, output_type)
    output_dir = base_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def clean_workspace(keep_generated: bool = True):
    """Clean workspace temporary files.

    Args:
        keep_generated: If True, keep generated_web and generated_code folders
    """
    base_dir = Path(settings.working_directory)

    # Always clean temp and downloads
    for folder in ["temp", "downloads"]:
        folder_path = base_dir / folder
        if folder_path.exists():
            for file in folder_path.iterdir():
                if file.is_file():
                    file.unlink()
                    logger.debug(f"Deleted: {file}")
            logger.info(f"Cleaned {folder}/")

    # Optionally clean generated content
    if not keep_generated:
        for folder in ["generated_web", "generated_code"]:
            folder_path = base_dir / folder
            if folder_path.exists():
                for file in folder_path.iterdir():
                    if file.is_file():
                        file.unlink()
                logger.info(f"Cleaned {folder}/")
