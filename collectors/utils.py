"""Shared utilities for Hermes HUD collectors."""

import os
from datetime import datetime
from typing import Optional


def default_hermes_dir(hermes_dir: str | None = None) -> str:
    """Return the hermes directory, defaulting to ~/.hermes."""
    return hermes_dir or os.path.expanduser("~/.hermes")


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
    except (ValueError, TypeError, OSError):
        pass
    return None
