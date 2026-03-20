"""File manager — read/write files and manage project directory structure."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def ensure_dir(path: Path) -> None:
    """Create directory and parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_file(project_dir: Path, relative_path: str, content: str) -> Path:
    """Write content to a file within the project directory.

    Creates parent directories as needed. Returns the absolute path.
    """
    full_path = project_dir / relative_path
    ensure_dir(full_path.parent)
    full_path.write_text(content, encoding="utf-8")
    logger.info(f"[FileManager] Wrote {len(content)} chars to {relative_path}")
    return full_path


def read_file(project_dir: Path, relative_path: str) -> Optional[str]:
    """Read a file from the project directory. Returns None if not found."""
    full_path = project_dir / relative_path
    if not full_path.exists():
        logger.warning(f"[FileManager] File not found: {relative_path}")
        return None
    content = full_path.read_text(encoding="utf-8")
    logger.debug(f"[FileManager] Read {len(content)} chars from {relative_path}")
    return content


def list_files(project_dir: Path, pattern: str = "**/*.py") -> list[str]:
    """List files matching a glob pattern in the project directory."""
    return [
        str(p.relative_to(project_dir))
        for p in project_dir.glob(pattern)
        if p.is_file()
    ]


def file_exists(project_dir: Path, relative_path: str) -> bool:
    """Check if a file exists in the project directory."""
    return (project_dir / relative_path).exists()
