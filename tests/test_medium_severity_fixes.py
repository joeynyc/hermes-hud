"""Regression tests for the medium-severity audit fixes.

4. _load_data must survive a collector failure (empty panel, not app crash).
5. collect_cron must tolerate alternate jobs.json shapes (bare list,
   null repeat/schedule/skills/string fields).
6. collect_config must normalize null/string toolsets and null sections
   so OverviewPanel's ', '.join never sees None.
7. build_timeline must not crash on an empty daily-stats date.
8. _check_pid_file must tolerate classic bare-integer pid files.
9. collect_sessions must skip rows with NULL started_at (no 1970 epoch
   sessions) and accept ISO-string timestamps.
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


# ── Fix 4: collector failure degrades gracefully ───────────────────────

def test_load_data_survives_collector_failure(env_override, monkeypatch):
    import hermes_hud.hud as hud_mod

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(hud_mod, "collect_cron", boom)
    monkeypatch.setattr(hud_mod, "collect_health", boom)
    monkeypatch.setenv("HERMES_HUD_NOBOOT", "1")

    async def run():
        app = hud_mod.HermesHUD()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("2")  # triggers _load_data
            await pilot.pause()
            assert app.is_running, "a failing collector must not crash the app"

    asyncio.run(run())


# ── Fix 5: cron jobs.json shape tolerance ───────────────────────────────

def test_collect_cron_tolerates_bare_list_and_nulls(tmp_path):
    from hermes_hud.collectors.cron import collect_cron

    cron_dir = tmp_path / "cron"
    cron_dir.mkdir()

    # bare list at top level, job with explicit nulls everywhere
    cron_dir.joinpath("jobs.json").write_text(json.dumps([
        {
            "id": None, "name": None, "prompt": None,
            "schedule_display": None, "schedule": None,
            "repeat": None, "skills": None, "deliver": None,
            "state": None, "enabled": True,
        },
        "not-a-dict",
    ]))

    state = collect_cron(str(tmp_path))
    assert state.total == 1
    job = state.jobs[0]
    assert job.name == "unnamed"
    assert job.schedule_display == "unknown"
    assert job.skills == []
    assert job.deliver == "local"


def test_collect_cron_tolerates_non_dict_top_level(tmp_path):
    from hermes_hud.collectors.cron import collect_cron

    cron_dir = tmp_path / "cron"
    cron_dir.mkdir()
    cron_dir.joinpath("jobs.json").write_text('"just a string"')

    assert collect_cron(str(tmp_path)).total == 0


# ── Fix 6: config toolsets/model normalization ──────────────────────────

def test_collect_config_normalizes_null_and_string_values(tmp_path):
    from hermes_hud.collectors.config import collect_config
    from hermes_hud.models import HUDState
    from hermes_hud.widgets import overview

    (tmp_path / "config.yaml").write_text(
        "model:\n"        # null section
        "toolsets:\n"     # null list
        "terminal:\n"
    )
    config = collect_config(str(tmp_path))
    assert config.toolsets == []
    assert config.model == ""
    assert config.provider == ""

    # OverviewPanel composes without TypeError on the joined toolsets
    recorded = []

    class Recorder:
        def __init__(self, content="", **kw):
            recorded.append(str(content))

    real = overview.Static
    overview.Static = Recorder
    try:
        list(overview.OverviewPanel(HUDState(config=config)).compose())
    finally:
        overview.Static = real
    assert recorded, "panel must render"

    # a scalar toolsets value becomes a one-element list
    (tmp_path / "config.yaml").write_text("toolsets: terminal\n")
    assert collect_config(str(tmp_path)).toolsets == ["terminal"]


# ── Fix 7: timeline survives an empty daily-stats date ──────────────────

def test_build_timeline_handles_empty_date():
    from hermes_hud.collectors.timeline import build_timeline
    from hermes_hud.models import DailyStats, HUDState, SessionInfo, SessionsState

    sessions = SessionsState(
        sessions=[SessionInfo(id="s1", source="cli", title="t",
                              started_at=datetime(2026, 6, 1), ended_at=None,
                              message_count=1, tool_call_count=0,
                              input_tokens=0, output_tokens=0)],
        daily_stats=[DailyStats(date="", sessions=1, messages=99, tool_calls=0)],
    )
    events = build_timeline(HUDState(sessions=sessions))  # must not raise
    assert not any(e.title.startswith("Most active day") for e in events)


# ── Fix 8: bare-integer pid files ────────────────────────────────────────

def test_check_pid_file_handles_bare_integer(tmp_path):
    from hermes_hud.collectors.health import _check_pid_file

    pid_file = tmp_path / "gateway.pid"
    pid_file.write_text("99999999\n")  # classic pid file: just the number

    status = _check_pid_file("Gateway", pid_file)  # must not raise
    assert status.running is False
    assert status.pid == 99999999

    pid_file.write_text('"nonsense"')  # valid JSON, wrong shape
    status = _check_pid_file("Gateway", pid_file)
    assert status.running is False


# ── Fix 9: session timestamp robustness ─────────────────────────────────

def test_collect_sessions_skips_null_and_accepts_iso(fake_hermes_home, monkeypatch):
    conn = sqlite3.connect(f"{fake_hermes_home}/state.db")
    conn.execute(
        "INSERT INTO sessions (id, source, title, started_at, message_count,"
        " tool_call_count, input_tokens, output_tokens) VALUES (?,?,?,?,?,?,?,?)",
        ("sess-null", "cli", "null start", None, 7, 0, 0, 0),
    )
    conn.execute(
        "INSERT INTO sessions (id, source, title, started_at, message_count,"
        " tool_call_count, input_tokens, output_tokens) VALUES (?,?,?,?,?,?,?,?)",
        ("sess-iso", "cli", "iso start", "2026-01-02T03:04:05", 3, 0, 0, 0),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("HERMES_HOME", fake_hermes_home)

    from hermes_hud.collectors.sessions import collect_sessions

    state = collect_sessions()
    ids = {s.id for s in state.sessions}
    assert "sess-null" not in ids, "NULL started_at must be skipped, not dated 1970"
    assert "sess-iso" in ids, "ISO-string started_at must be parsed, not dropped"
    iso = next(s for s in state.sessions if s.id == "sess-iso")
    assert iso.started_at == datetime(2026, 1, 2, 3, 4, 5)
    assert not any(s.started_at.year == 1970 for s in state.sessions)
    assert all(ds.date for ds in state.daily_stats), "empty date buckets must be skipped"


def _replace_activity_sessions(hermes_home, sessions):
    conn = sqlite3.connect(f"{hermes_home}/state.db")
    conn.execute("DROP TABLE sessions")
    conn.execute("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY, source TEXT, title TEXT,
            started_at, ended_at, message_count INTEGER DEFAULT 0,
            tool_call_count INTEGER DEFAULT 0, input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0, cache_read_tokens INTEGER DEFAULT 0,
            cache_write_tokens INTEGER DEFAULT 0, reasoning_tokens INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0, model TEXT, model_config TEXT
        )
    """)
    conn.execute("DELETE FROM messages")
    conn.execute("ALTER TABLE messages ADD COLUMN timestamp REAL")
    conn.executemany(
        "INSERT INTO sessions (id, source, title, started_at, message_count)"
        " VALUES (?, 'cli', ?, ?, ?)",
        [(session_id, session_id, started_at, messages)
         for session_id, started_at, messages in sessions],
    )
    conn.commit()
    conn.close()


def _collect_activity_at_timezone(hermes_home, monkeypatch, timezone_name):
    from hermes_hud.collectors.patterns import collect_patterns
    from hermes_hud.collectors.sessions import collect_sessions

    if not hasattr(time, "tzset"):
        pytest.skip("the platform does not support process timezone overrides")

    try:
        with monkeypatch.context() as timezone_patch:
            timezone_patch.setenv("TZ", timezone_name)
            time.tzset()
            return collect_sessions(str(hermes_home)), collect_patterns(str(hermes_home))
    finally:
        time.tzset()


def test_iso_sessions_populate_daily_and_hourly_activity(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("iso-morning", "2026-01-02T08:00:00", 6),
        ("iso-evening", "2026-01-02T17:00:00", 8),
    ])

    sessions, patterns = _collect_activity_at_timezone(fake_hermes_home, monkeypatch, "UTC")
    actual = {
        "session_count": sessions.total_sessions,
        "daily": [(d.date, d.sessions, d.messages) for d in sessions.daily_stats],
        "hourly": [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
                   if h.sessions or h.messages],
    }
    assert actual == {
        "session_count": 2,
        "daily": [("2026-01-02", 2, 14)],
        "hourly": [(8, 1, 6), (17, 1, 8)],
    }


def test_numeric_sessions_keep_utc_daily_and_local_hourly_buckets(fake_hermes_home, monkeypatch):
    timestamp = datetime(2026, 1, 2, 8, tzinfo=timezone.utc).timestamp()
    _replace_activity_sessions(fake_hermes_home, [("numeric", timestamp, 4)])

    sessions, patterns = _collect_activity_at_timezone(
        fake_hermes_home, monkeypatch, "America/Los_Angeles"
    )
    assert [(d.date, d.sessions, d.messages) for d in sessions.daily_stats] == [
        ("2026-01-02", 1, 4),
    ]
    assert sessions.sessions[0].started_at.hour == 0
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(0, 1, 4)]


def test_iso_timezone_offsets_use_local_hour_buckets(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("iso-offset", "2026-01-02T01:00:00+00:00", 4),
    ])

    sessions, patterns = _collect_activity_at_timezone(
        fake_hermes_home, monkeypatch, "America/Los_Angeles"
    )
    assert [(d.date, d.sessions, d.messages) for d in sessions.daily_stats] == [
        ("2026-01-02", 1, 4),
    ]
    local_time = sessions.sessions[0].started_at.astimezone(ZoneInfo("America/Los_Angeles"))
    assert (local_time.date().isoformat(), local_time.hour) == ("2026-01-01", 17)
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(17, 1, 4)]


def test_mixed_iso_and_numeric_sessions_share_daily_bucket(fake_hermes_home, monkeypatch):
    numeric = datetime(2026, 1, 2, 8, tzinfo=timezone.utc).timestamp()
    _replace_activity_sessions(fake_hermes_home, [
        ("numeric", numeric, 6),
        ("iso", "2026-01-02T17:00:00+00:00", 8),
    ])

    sessions, patterns = _collect_activity_at_timezone(
        fake_hermes_home, monkeypatch, "America/Los_Angeles"
    )
    assert [(d.date, d.sessions, d.messages) for d in sessions.daily_stats] == [
        ("2026-01-02", 2, 14),
    ]
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(0, 1, 6), (9, 1, 8)]


def test_numeric_string_fractional_and_zero_timestamps_are_preserved(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("numeric-string", "0", 2),
        ("fractional", 0.5, 3),
        ("zero", 0, 4),
    ])

    sessions, patterns = _collect_activity_at_timezone(fake_hermes_home, monkeypatch, "UTC")
    assert sessions.total_sessions == 3
    assert [(d.date, d.sessions, d.messages) for d in sessions.daily_stats] == [
        ("1970-01-01", 3, 9),
    ]
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(0, 3, 9)]


def test_daily_stats_preserve_sql_sum_null_semantics(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("null-input", datetime(2026, 1, 2, 8, tzinfo=timezone.utc).timestamp(), 4),
        ("normal", datetime(2026, 1, 2, 10, tzinfo=timezone.utc).timestamp(), 6),
    ])
    conn = sqlite3.connect(f"{fake_hermes_home}/state.db")
    conn.execute(
        "UPDATE sessions SET input_tokens = NULL, output_tokens = 500, tool_call_count = 2 "
        "WHERE id = 'null-input'"
    )
    conn.execute(
        "UPDATE sessions SET input_tokens = 100, output_tokens = 50, tool_call_count = 1 "
        "WHERE id = 'normal'"
    )
    conn.commit()
    conn.close()

    sessions, _ = _collect_activity_at_timezone(fake_hermes_home, monkeypatch, "UTC")
    assert [(d.date, d.sessions, d.messages, d.tool_calls, d.tokens)
            for d in sessions.daily_stats] == [("2026-01-02", 2, 10, 3, 150)]


def test_naive_iso_hour_is_not_shifted_by_local_timezone(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("naive-iso", "2026-01-02T08:00:00", 5),
    ])

    sessions, patterns = _collect_activity_at_timezone(
        fake_hermes_home, monkeypatch, "America/Los_Angeles"
    )
    assert sessions.sessions[0].started_at.hour == 8
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(8, 1, 5)]


def test_invalid_session_timestamps_are_excluded_from_activity(fake_hermes_home, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("valid", "2026-01-02T08:00:00", 5),
        ("invalid", "not-a-timestamp", 99),
        ("invalid-date", "2026-02-31T08:00:00", 88),
        ("missing", None, 77),
        ("out-of-range", 1e20, 50),
    ])

    sessions, patterns = _collect_activity_at_timezone(fake_hermes_home, monkeypatch, "UTC")
    assert [session.id for session in sessions.sessions] == ["valid"]
    assert [(d.date, d.sessions, d.messages) for d in sessions.daily_stats] == [
        ("2026-01-02", 1, 5),
    ]
    assert [(h.hour, h.sessions, h.messages) for h in patterns.hourly_activity
            if h.sessions or h.messages] == [(8, 1, 5)]


def test_iso_activity_is_rendered_in_textual_panels(fake_hermes_home, env_override, monkeypatch):
    _replace_activity_sessions(fake_hermes_home, [
        ("iso-morning", "2026-01-02T08:00:00", 6),
        ("iso-evening", "2026-01-02T17:00:00", 8),
    ])
    monkeypatch.setenv("HERMES_HUD_NOBOOT", "1")

    from hermes_hud.collectors.patterns import collect_patterns
    from hermes_hud.collectors.sessions import collect_sessions
    from hermes_hud.hud import HermesHUD
    from hermes_hud.widgets.patterns_panel import PatternsPanel
    from hermes_hud.widgets.sessions_panel import SessionsPanel

    session_state = collect_sessions()
    patterns_state = collect_patterns()
    print("Synthetic collector activity:", {
        "sessions": session_state.total_sessions,
        "daily": [(d.date, d.sessions, d.messages) for d in session_state.daily_stats],
        "hourly": [(h.hour, h.sessions, h.messages) for h in patterns_state.hourly_activity
                   if h.sessions or h.messages],
    })

    async def run():
        app = HermesHUD()
        async with app.run_test(size=(160, 48)) as pilot:
            await pilot.press("2")
            await pilot.pause()
            session_panel = app.query_one(SessionsPanel)
            patterns_panel = app.query_one(PatternsPanel)
            session_text = "\n".join(
                getattr(widget.render(), "plain", str(widget.render()))
                for widget in session_panel.query("Static")
            )
            patterns_text = "\n".join(
                getattr(widget.render(), "plain", str(widget.render()))
                for widget in patterns_panel.query("Static")
            )
            print("Sessions widget activity:", [line.strip() for line in session_text.splitlines()
                                                 if "msgs /" in line])
            print("Patterns widget chart:", [line.strip() for line in patterns_text.splitlines()
                                             if "08" in line or "17" in line or "Peak:" in line])
            assert "2026-01-02" in session_text
            assert "14 msgs / 0 tools" in session_text
            assert "08█" in patterns_text and "17█" in patterns_text

    asyncio.run(run())
