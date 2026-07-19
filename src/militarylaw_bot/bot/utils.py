"""Shared utilities for bot handlers."""

from __future__ import annotations

from pathlib import Path


def get_data_path(relative_path: str) -> Path:
    """Get path to data directory, supporting both local and Docker environments."""
    # Check if running in Docker (/app/data exists)
    if Path("/app/data").exists():
        return Path("/app/data") / relative_path

    # Local development: data is at project root
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "data" / relative_path


def get_db_path(db_name: str = "suitability/military_medicine.db") -> str:
    """Get database path."""
    return str(get_data_path(db_name))


def get_tables_dir() -> str:
    """Get tables directory path."""
    return str(get_data_path("suitability/tables"))
