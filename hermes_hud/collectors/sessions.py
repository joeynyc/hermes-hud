"""Collect session data from Hermes state.db."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from ..models import DailyStats, SessionInfo, SessionsState
from .utils import default_hermes_dir


def _extract_tool_usage(db_path: str) -> dict[str, int]:
    """Extract tool usage counts from tool_calls JSON in messages."""
    usage: dict[str, int] = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tool_calls FROM messages WHERE tool_calls IS NOT NULL AND tool_calls != ''"
        )
        for (tc_json,) in cursor.fetchall():
            try:
                calls = json.loads(tc_json)
                if isinstance(calls, list):
                    for call in calls:
                        fn = call.get("function", {})
                        name = fn.get("name", "unknown")
                        usage[name] = usage.get(name, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass
        conn.close()
    except Exception:
        pass
    return usage


def collect_sessions(hermes_dir: str | None = None) -> SessionsState:
    """Collect session data from state.db."""
    if hermes_dir is None:
        hermes_dir = default_hermes_dir(hermes_dir)

    db_path = str(Path(hermes_dir) / "state.db")
    if not os.path.exists(db_path):
        return SessionsState()

    sessions: list[SessionInfo] = []
    daily_stats: list[DailyStats] = []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch all sessions
        cursor.execute("""
            SELECT id, source, title, started_at, ended_at,
                   message_count, tool_call_count,
                   input_tokens, output_tokens,
                   cache_read_tokens, cache_write_tokens,
                   reasoning_tokens, estimated_cost_usd, model_config
            FROM sessions
            ORDER BY started_at DESC
        """)

        for row in cursor.fetchall():
            started = datetime.fromtimestamp(row["started_at"])
            ended = datetime.fromtimestamp(row["ended_at"]) if row["ended_at"] else None

            # Try to extract model from model_config JSON
            model = None
            if row["model_config"]:
                try:
                    mc = json.loads(row["model_config"])
                    model = mc.get("model") or mc.get("default")
                except (json.JSONDecodeError, TypeError):
                    pass

            sessions.append(SessionInfo(
                id=row["id"],
                source=row["source"] or "unknown",
                title=row["title"],
                started_at=started,
                ended_at=ended,
                message_count=row["message_count"] or 0,
                tool_call_count=row["tool_call_count"] or 0,
                input_tokens=row["i...ns"] or 0,
                output_tokens=row["o...ns"] or 0,
                cache_read_tokens=row["c...ns"] or 0,
                cache_write_tokens=row["c...ns"] or 0,
                reasoning_tokens=row["r...ns"] or 0,
                estimated_cost_usd=row["estimated_cost_usd"] or 0.0,
                model=model,
            ))

        # Daily stats
        cursor.execute("""
            SELECT date(started_at, 'unixepoch') as day,
                   COUNT(*) as sessions,
                   SUM(message_count) as msgs,
                   SUM(tool_call_count) as tools,
                   SUM(input_tokens + output_tokens) as tokens
            FROM sessions
            GROUP BY day
            ORDER BY day
        """)

        for row in cursor.fetchall():
            daily_stats.append(DailyStats(
                date=row["day"],
                sessions=row["sessions"],
                messages=row["msgs"] or 0,
                tool_calls=row["tools"] or 0,
                tokens=row["tokens"] or 0,
            ))

        conn.close()
    except Exception as e:
        # Return what we have
        pass

    # Tool usage
    tool_usage = _extract_tool_usage(db_path)

    return SessionsState(
        sessions=sessions,
        daily_stats=daily_stats,
        tool_usage=tool_usage,
    )
