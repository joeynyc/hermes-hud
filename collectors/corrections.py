"""Collect correction events — times Hermes was wrong and learned from it."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Correction:
    timestamp: Optional[datetime]
    source: str  # memory, user, session
    summary: str
    detail: str = ""
    session_title: Optional[str] = None
    severity: str = "minor"  # minor, major, critical


@dataclass
class CorrectionsState:
    corrections: list[Correction] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.corrections)

    def by_source(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self.corrections:
            counts[c.source] = counts.get(c.source, 0) + 1
        return counts

    def by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self.corrections:
            counts[c.severity] = counts.get(c.severity, 0) + 1
        return counts


# Patterns that indicate corrections in memory
CORRECTION_KEYWORDS = [
    (r"gotcha", "major"),
    (r"don't .+ as a problem", "major"),
    (r"caught me", "critical"),
    (r"verify before", "critical"),
    (r"Read .+ before making", "major"),
    (r"supersedes", "minor"),
    (r"not usable", "minor"),
    (r"doesn't work", "minor"),
    (r"won't help", "minor"),
    (r"not yet confirmed", "minor"),
    (r"was stuck", "minor"),
    (r"may need manual", "minor"),
    (r"blocks patches", "minor"),
]

# Patterns in session transcripts indicating pushback/correction
SESSION_CORRECTION_PATTERNS = [
    r"that'?s (?:not |in)?correct",
    r"you'?re wrong",
    r"no,?\s+(?:it|that|the)",
    r"actually,?\s+",
    r"that'?s not (?:right|true|how)",
    r"verify (?:that|this|before)",
    r"are you sure",
    r"double.?check",
    r"(?:incorrect|wrong) (?:about|recommendation|suggestion)",
    r"push.?back",
]


def _extract_memory_corrections(hermes_dir: str) -> list[Correction]:
    """Extract corrections from memory files."""
    from collectors.memory import collect_memory

    memory_state, user_state = collect_memory(hermes_dir)
    corrections = []

    for state, source in [(memory_state, "memory"), (user_state, "user")]:
        for entry in state.entries:
            if entry.category != "correction":
                continue
            for pattern, severity in CORRECTION_KEYWORDS:
                if re.search(pattern, entry.text, re.IGNORECASE):
                    summary = entry.text[:80]
                    if len(entry.text) > 80:
                        summary += "..."
                    corrections.append(Correction(
                        timestamp=None,
                        source=source,
                        summary=summary,
                        detail=entry.text,
                        severity=severity,
                    ))
                    break

    return corrections


def _extract_session_corrections(hermes_dir: str) -> list[Correction]:
    """Mine session transcripts for correction events."""
    corrections = []
    db_path = Path(hermes_dir) / "state.db"

    if not db_path.exists():
        return corrections

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Search user messages for correction patterns
        for pattern in SESSION_CORRECTION_PATTERNS:
            cursor.execute("""
                SELECT m.content, m.timestamp, s.title, s.id
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE m.role = 'user'
                AND m.content IS NOT NULL
                AND m.content REGEXP ?
                ORDER BY m.timestamp DESC
                LIMIT 5
            """, (pattern,))
            # REGEXP might not be available, fall back to LIKE
            pass

        # Simpler approach: search with FTS if available, else LIKE
        for pattern_word in ["wrong", "incorrect", "verify", "actually", "not right", "not correct", "not true", "push back"]:
            try:
                cursor.execute("""
                    SELECT m.content, m.timestamp, s.title, s.id
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.id
                    WHERE m.role = 'user'
                    AND m.content LIKE ?
                    ORDER BY m.timestamp DESC
                    LIMIT 3
                """, (f"%{pattern_word}%",))

                for row in cursor.fetchall():
                    content = row["content"] or ""
                    # Filter out false positives (very short or very long messages)
                    if len(content) < 10 or len(content) > 2000:
                        continue

                    # Extract context around the keyword
                    lower = content.lower()
                    idx = lower.find(pattern_word.lower())
                    if idx >= 0:
                        start = max(0, idx - 40)
                        end = min(len(content), idx + len(pattern_word) + 60)
                        context = content[start:end].strip()
                        if start > 0:
                            context = "..." + context
                        if end < len(content):
                            context += "..."
                    else:
                        context = content[:100]

                    corrections.append(Correction(
                        timestamp=datetime.fromtimestamp(row["timestamp"]),
                        source="session",
                        summary=context,
                        detail=content[:300],
                        session_title=row["title"],
                        severity="minor",
                    ))
            except sqlite3.OperationalError:
                continue

        conn.close()
    except Exception:
        pass

    # Deduplicate by summary
    seen = set()
    unique = []
    for c in corrections:
        key = c.summary[:50]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def collect_corrections(hermes_dir: str | None = None) -> CorrectionsState:
    """Collect all correction events."""
    if hermes_dir is None:
        hermes_dir = os.path.expanduser("~/.hermes")

    corrections = []
    corrections.extend(_extract_memory_corrections(hermes_dir))
    corrections.extend(_extract_session_corrections(hermes_dir))

    # Sort: timestamped first (newest), then un-timestamped
    corrections.sort(key=lambda c: (
        0 if c.timestamp else 1,
        -(c.timestamp.timestamp() if c.timestamp else 0),
    ))

    return CorrectionsState(corrections=corrections)
