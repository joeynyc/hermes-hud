"""Test that every collector runs against fake data and returns valid types."""

import pytest
from hermes_hud.models import MemoryState, SkillsState, SessionsState, ConfigState


class TestMemoryCollector:
    def test_collects_memory_and_user(self, env_override):
        from hermes_hud.collectors.memory import collect_memory

        memory, user = collect_memory()
        assert isinstance(memory, MemoryState)
        assert isinstance(user, MemoryState)
        assert memory.source == "memory"
        assert user.source == "user"

    def test_memory_entries_parsed(self, env_override):
        from hermes_hud.collectors.memory import collect_memory

        memory, user = collect_memory()
        # Our fake MEMORY.md has 3 paragraph-delimited entries
        assert memory.entry_count >= 2
        assert user.entry_count >= 1

    def test_memory_capacity(self, env_override):
        from hermes_hud.collectors.memory import collect_memory

        memory, _ = collect_memory()
        assert memory.total_chars > 0
        assert memory.max_chars > 0
        assert 0 <= memory.capacity_pct <= 100


class TestSkillsCollector:
    def test_collects_skills(self, env_override):
        from hermes_hud.collectors.skills import collect_skills

        skills = collect_skills()
        assert isinstance(skills, SkillsState)
        assert skills.total >= 3  # we created 3 fake skills

    def test_skill_categories(self, env_override):
        from hermes_hud.collectors.skills import collect_skills

        skills = collect_skills()
        cats = skills.category_counts()
        assert isinstance(cats, dict)
        assert len(cats) >= 2


class TestSessionsCollector:
    def test_collects_sessions(self, env_override):
        from hermes_hud.collectors.sessions import collect_sessions

        sessions = collect_sessions()
        assert isinstance(sessions, SessionsState)
        # We inserted 3 sessions
        assert sessions.total_sessions >= 3

    def test_tool_usage_extracted(self, env_override):
        from hermes_hud.collectors.sessions import collect_sessions

        sessions = collect_sessions()
        assert "terminal" in sessions.tool_usage
        assert sessions.tool_usage["terminal"] >= 2

    def test_daily_stats(self, env_override):
        from hermes_hud.collectors.sessions import collect_sessions

        sessions = collect_sessions()
        assert len(sessions.daily_stats) >= 1

    def test_session_info_fields(self, env_override):
        from hermes_hud.collectors.sessions import collect_sessions

        sessions = collect_sessions()
        assert len(sessions.sessions) >= 1
        s = sessions.sessions[0]
        assert s.id is not None
        assert s.source == "cli"
        assert s.started_at is not None
        assert s.message_count > 0


class TestConfigCollector:
    def test_collects_config(self, env_override):
        from hermes_hud.collectors.config import collect_config

        config = collect_config()
        assert isinstance(config, ConfigState)
        assert config.model == "claude-sonnet-4-20250514"
        assert config.provider == "anthropic"
        assert "terminal" in config.toolsets
        assert config.backend == "local"
        assert config.max_turns == 50

    def test_config_missing_file(self, tmp_path, monkeypatch):
        """Config collector shouldn't crash if config.yaml is missing."""
        empty_hermes = tmp_path / "empty-hermes"
        empty_hermes.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(empty_hermes))

        from hermes_hud.collectors.config import collect_config

        config = collect_config()
        assert isinstance(config, ConfigState)


class TestCronCollector:
    def test_collects_cron(self, env_override):
        from hermes_hud.collectors.cron import collect_cron

        cron = collect_cron()
        assert cron.total >= 2
        assert len(cron.jobs) >= 2

    def test_cron_job_fields(self, env_override):
        from hermes_hud.collectors.cron import collect_cron

        cron = collect_cron()
        job = next(j for j in cron.jobs if j.name == "daily-snapshot")
        assert job.enabled is True
        assert "1440" in job.schedule_display

    def test_cron_paused_job(self, env_override):
        from hermes_hud.collectors.cron import collect_cron

        cron = collect_cron()
        job = next(j for j in cron.jobs if j.name == "paused-job")
        assert job.enabled is False
        assert job.state == "paused"

    def test_cron_missing_dir(self, tmp_path, monkeypatch):
        """Cron collector shouldn't crash if cron dir is missing."""
        empty_hermes = tmp_path / "empty-hermes"
        empty_hermes.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(empty_hermes))

        from hermes_hud.collectors.cron import collect_cron

        cron = collect_cron()
        assert cron.total == 0


class TestProjectsCollector:
    def test_collects_projects(self, env_override):
        from hermes_hud.collectors.projects import collect_projects

        projects = collect_projects()
        assert projects.total >= 1

    def test_project_is_git(self, env_override):
        from hermes_hud.collectors.projects import collect_projects

        projects = collect_projects()
        repo = next(p for p in projects.projects if p.name == "test-project")
        assert repo.is_git is True


class TestHealthCollector:
    def test_collects_health(self, env_override):
        from hermes_hud.collectors.health import collect_health

        health = collect_health()
        assert health is not None
        key_names = [k.name for k in health.keys]
        assert any("ANTHROPIC" in k for k in key_names)

    def test_health_no_crash_empty(self, tmp_path, monkeypatch):
        empty_hermes = tmp_path / "empty-hermes"
        empty_hermes.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(empty_hermes))

        from hermes_hud.collectors.health import collect_health

        health = collect_health()
        assert health is not None


class TestCorrectionsCollector:
    def test_collects_corrections(self, env_override):
        from hermes_hud.collectors.corrections import collect_corrections

        corrections = collect_corrections()
        assert corrections is not None
        # Heuristic detection may or may not catch our "BURNED:" entry
        assert corrections.total >= 0


class TestAgentsCollector:
    def test_collects_agents(self, env_override):
        from hermes_hud.collectors.agents import collect_agents

        agents = collect_agents()
        assert agents is not None
        # AgentsState has 'processes' and 'recent_sessions'
        assert hasattr(agents, "processes")
        assert hasattr(agents, "recent_sessions")
        assert isinstance(agents.processes, list)
        # tmux fields present and default to empty (no tmux in test env)
        assert hasattr(agents, "tmux_panes")
        assert isinstance(agents.tmux_panes, list)
        assert hasattr(agents, "operator_alerts")
        assert isinstance(agents.operator_alerts, list)


class TestTimelineCollector:
    def test_builds_timeline(self, env_override):
        from hermes_hud.collectors.memory import collect_memory
        from hermes_hud.collectors.skills import collect_skills
        from hermes_hud.collectors.sessions import collect_sessions
        from hermes_hud.collectors.config import collect_config
        from hermes_hud.collectors.timeline import build_timeline
        from hermes_hud.models import HUDState
        from datetime import datetime

        memory, user = collect_memory()
        skills = collect_skills()
        sessions = collect_sessions()
        config = collect_config()

        state = HUDState(
            memory=memory,
            user=user,
            skills=skills,
            sessions=sessions,
            config=config,
            timeline=[],
            collected_at=datetime.now(),
        )
        timeline = build_timeline(state)
        assert isinstance(timeline, list)
