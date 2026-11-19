"""Shared utilities for Hermes HUD collectors."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def default_hermes_dir(hermes_dir: str | None = None) -> str:
    """Return the hermes directory.

    Priority: explicit arg > HERMES_HOME env var > ~/.hermes
    """
    if hermes_dir:
        return hermes_dir
    return os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))


def default_projects_dir(projects_dir: str | None = None) -> str:
    """Return the projects directory.

    Priority: explicit arg > HERMES_HUD_PROJECTS_DIR env var > ~/projects
    """
    if projects_dir:
        return projects_dir
    return os.environ.get("HERMES_HUD_PROJECTS_DIR", os.path.expanduser("~/projects"))


def read_text_safe(path, default: str = "") -> str:
    """Read a UTF-8 text file, returning default if missing, unreadable,
    a directory, or not valid UTF-8."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return default


def safe_get(row, key, default=None):
    """Safely access a column from a sqlite3.Row or tuple.

    Returns default if the column is missing, access fails, or value is None.
    """
    try:
        val = row[key]
        return val if val is not None else default
    except (IndexError, KeyError):
        return default


def parse_timestamp(value) -> Optional[datetime]:
    """Parse a timestamp from various formats (unix int/float, ISO string).

    Returns None if parsing fails.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromtimestamp(float(value))
            except ValueError:
                return datetime.fromisoformat(value)
    except (ValueError, TypeError, OSError, OverflowError):
        pass
    return None


def _numeric_timestamp(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
    return None


def timestamp_to_utc_day(value) -> Optional[str]:
    """Return the UTC day, or the stated day for a naive ISO timestamp."""
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    try:
        timestamp = _numeric_timestamp(value)
        if timestamp is not None:
            return datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.date().isoformat()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def timestamp_to_local_hour(value) -> Optional[int]:
    """Return a valid timestamp's local hour, preserving naive ISO wall time."""
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    try:
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone()
        return parsed.hour
    except (ValueError, TypeError, OSError, OverflowError):
        return None
