"""Shared fixtures for hermes-hud tests."""

import os
import json
import sqlite3
import tempfile
import shutil
import time
import pytest


@pytest.fixture
def fake_hermes_home(tmp_path):
    """Create a minimal but realistic ~/.hermes directory structure.

    Returns the path. All collectors should work against this without errors.
    """
    hermes = tmp_path / ".hermes"
    hermes.mkdir()

    # memories/
    mem_dir = hermes / "memories"
    mem_dir.mkdir()

    (mem_dir / "MEMORY.md").write_text(
        "Test environment: Linux x86_64. Python 3.11.\n"
        "\u00a7\n"
        "Project alpha at ~/projects/alpha. Uses FastAPI.\n"
        "\u00a7\n"
        "BURNED: Don't use os.system() \u2014 use subprocess instead.\n"
    )
    (mem_dir / "USER.md").write_text(
        "Name: TestUser. Prefers dark themes.\n"
        "\u00a7\n"
        "Uses vim keybindings everywhere.\n"
    )

    # config.yaml — must match the nested structure the collector expects
    # model can be a string (treated as model name) or a dict with "default"/"provider"
    (hermes / "config.yaml").write_text(
        "model:\n"
        "  default: claude-sonnet-4-20250514\n"
        "  provider: anthropic\n"
        "toolsets:\n"
        "  - terminal\n"
        "  - file\n"
        "terminal:\n"
        "  backend: local\n"
        "agent:\n"
        "  max_turns: 50\n"
        "compression:\n"
        "  enabled: true\n"
        "checkpoints:\n"
        "  enabled: true\n"
    )

    # state.db with sessions + messages tables
    # Must have all columns the collector queries
    db_path = hermes / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            started_at REAL,
            ended_at REAL,
            model TEXT,
            provider TEXT,
            message_count INTEGER DEFAULT 0,
            tool_call_count INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_read_tokens INTEGER DEFAULT 0,
            cache_write_tokens INTEGER DEFAULT 0,
            reasoning_tokens INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            model_config TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            tool_calls TEXT,
            created_at REAL
        )
    """)
    # Insert fake sessions spread across 3 days
    now = time.time()
    for i in range(3):
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"sess-{i}",
                "cli",
                f"Test session {i}",
                now - (86400 * (2 - i)),
                now - (86400 * (2 - i)) + 3600,
                "claude-sonnet-4-20250514",
                "anthropic",
                10 + i * 5,
                3 + i,
                1000 + i * 500,
                500 + i * 200,
                0, 0, 0, 0.0,
                json.dumps({"model": "claude-sonnet-4-20250514"}),
            ),
        )
    # Insert messages with tool_calls for tool usage extraction
    # tool_calls use OpenAI format: [{"function": {"name": "..."}}]
    conn.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
        (
            "msg-1", "sess-0", "assistant", "test",
            json.dumps([
                {"function": {"name": "terminal"}},
                {"function": {"name": "read_file"}},
            ]),
            now - 86400,
        ),
    )
    conn.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
        (
            "msg-2", "sess-1", "assistant", "test",
            json.dumps([
                {"function": {"name": "terminal"}},
                {"function": {"name": "search_files"}},
            ]),
            now,
        ),
    )
    conn.commit()
    conn.close()

    # skills/
    skills_dir = hermes / "skills"
    for category, name in [("devops", "docker"), ("research", "arxiv"), ("custom", "my-tool")]:
        skill_dir = skills_dir / category / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}\nversion: 1.0.0\n"
            f"tags: [test]\n---\n\n# {name}\n\nA test skill.\n"
        )

    # cron/jobs.json — must match the format the collector expects:
    # { "jobs": [ ... ], "updated_at": "..." }
    cron_dir = hermes / "cron"
    cron_dir.mkdir()
    (cron_dir / "jobs.json").write_text(json.dumps({
        "jobs": [
            {
                "id": "job-1",
                "name": "daily-snapshot",
                "prompt": "Take a snapshot",
                "schedule": {"display": "every 1440m"},
                "schedule_display": "every 1440m",
                "state": "active",
                "enabled": True,
                "created_at": "2026-03-20T10:00:00",
                "deliver": "local",
            },
            {
                "id": "job-2",
                "name": "paused-job",
                "prompt": "Do nothing",
                "schedule": {"display": "every 60m"},
                "schedule_display": "every 60m",
                "state": "paused",
                "enabled": False,
                "created_at": "2026-03-25T10:00:00",
                "deliver": "local",
            },
        ],
        "updated_at": "2026-03-30T12:00:00",
    }))

    # .env with some fake key names
    (hermes / ".env").write_text(
        "ANTHROPIC_API_KEY=sk-test-fake\n"
        "OPENAI_API_KEY=sk-test-fake2\n"
    )

    return str(hermes)


@pytest.fixture
def fake_projects_dir(tmp_path):
    """Create a fake ~/projects directory with git repos."""
    projects = tmp_path / "projects"
    projects.mkdir()

    repo = projects / "test-project"
    repo.mkdir()
    os.system(
        f"cd {repo} && git init -q && "
        f"git config user.email 'test@test.com' && "
        f"git config user.name 'Test' 2>/dev/null"
    )
    (repo / "main.py").write_text("print('hello')\n")
    (repo / "utils.py").write_text("def helper(): pass\n")
    os.system(f"cd {repo} && git add -A && git commit -q -m 'init' 2>/dev/null")

    return str(projects)


@pytest.fixture
def env_override(fake_hermes_home, fake_projects_dir, monkeypatch):
    """Set HERMES_HOME and HERMES_HUD_PROJECTS_DIR to fake dirs."""
    monkeypatch.setenv("HERMES_HOME", fake_hermes_home)
    monkeypatch.setenv("HERMES_HUD_PROJECTS_DIR", fake_projects_dir)
    return {"hermes_home": fake_hermes_home, "projects_dir": fake_projects_dir}
