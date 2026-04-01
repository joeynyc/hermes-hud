"""Integration tests — end-to-end data flow through the whole system."""

import pytest
from datetime import datetime


class TestCollectAll:
    """Test the full collect_all() pipeline."""

    def test_collect_all_returns_hud_state(self, env_override):
        from hermes_hud.collect import collect_all
        from hermes_hud.models import HUDState

        state = collect_all()
        assert isinstance(state, HUDState)

    def test_state_has_all_fields(self, env_override):
        from hermes_hud.collect import collect_all

        state = collect_all()
        assert state.memory is not None
        assert state.user is not None
        assert state.skills is not None
        assert state.sessions is not None
        assert state.config is not None
        assert state.timeline is not None
        assert isinstance(state.collected_at, datetime)

    def test_state_data_populated(self, env_override):
        from hermes_hud.collect import collect_all

        state = collect_all()
        assert state.memory.entry_count > 0
        assert state.user.entry_count > 0
        assert state.skills.total > 0
        assert state.sessions.total_sessions > 0
        assert state.config.model is not None


class TestSnapshot:
    """Test snapshot save/load/diff cycle."""

    def test_take_snapshot(self, env_override, tmp_path, monkeypatch):
        import hermes_hud.snapshot as snap_mod
        monkeypatch.setattr(snap_mod, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))

        from hermes_hud.snapshot import take_snapshot

        snap = take_snapshot()
        # HUDSnapshot fields
        assert snap.memory_entry_count > 0
        assert snap.skill_count > 0
        assert snap.session_count > 0

    def test_snapshot_save_and_load(self, env_override, tmp_path, monkeypatch):
        import hermes_hud.snapshot as snap_mod
        snap_dir = str(tmp_path / "snapshots")
        monkeypatch.setattr(snap_mod, "SNAPSHOT_DIR", snap_dir)

        from hermes_hud.snapshot import take_snapshot, save_snapshot, load_snapshots

        snap = take_snapshot()
        save_snapshot(snap)
        loaded = load_snapshots()
        assert len(loaded) >= 1

    def test_diff_report_two_snapshots(self, env_override, tmp_path, monkeypatch):
        import hermes_hud.snapshot as snap_mod
        import time
        snap_dir = str(tmp_path / "snapshots")
        monkeypatch.setattr(snap_mod, "SNAPSHOT_DIR", snap_dir)

        from hermes_hud.snapshot import take_snapshot, save_snapshot, load_snapshots, diff_report

        snap1 = take_snapshot()
        save_snapshot(snap1)
        time.sleep(0.01)
        snap2 = take_snapshot()
        save_snapshot(snap2)

        loaded = load_snapshots()
        assert len(loaded) >= 2
        # diff_report takes two dicts (current and previous)
        report = diff_report(loaded[-1], loaded[-2])
        assert isinstance(report, (dict, str))


class TestAppInstantiation:
    """Test that the Textual app can be created."""

    def test_app_creates(self, env_override):
        from hermes_hud.hud import HermesHUD

        app = HermesHUD()
        assert app is not None
        assert app.TITLE == "\u2624 Hermes HUD"

    def test_app_has_themes(self, env_override):
        from hermes_hud.hud import HERMES_THEMES

        assert len(HERMES_THEMES) == 4
        names = [t.name for t in HERMES_THEMES]
        assert "hermes-ai" in names
        assert "hermes-blade-runner" in names
        assert "hermes-fsociety" in names
        assert "hermes-anime" in names

    def test_app_has_bindings(self, env_override):
        from hermes_hud.hud import HermesHUD

        app = HermesHUD()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "q" in binding_keys
        assert "r" in binding_keys
        assert "1" in binding_keys
        assert "7" in binding_keys


class TestCLIEntryPoint:
    """Test that the CLI entry point handles args."""

    def test_help_flag(self, env_override, capsys):
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["hermes-hud", "--help"]):
            from hermes_hud.hud import main
            main()

        captured = capsys.readouterr()
        assert "Usage: hermes-hud" in captured.out
        assert "HERMES_HOME" in captured.out

    def test_text_mode(self, env_override, capsys):
        import sys
        from unittest.mock import patch

        with patch.object(sys, "argv", ["hermes-hud", "--text"]):
            from hermes_hud.hud import main
            main()

        captured = capsys.readouterr()
        assert "HUDState" in captured.out


class TestModels:
    """Test dataclass models."""

    def test_memory_state_capacity(self):
        from hermes_hud.models import MemoryState, MemoryEntry

        state = MemoryState(
            entries=[
                MemoryEntry(text="hello world", category="test", char_count=11),
            ],
            total_chars=11,
            max_chars=100,
            source="memory",
        )
        assert state.capacity_pct == 11.0
        assert state.entry_count == 1

    def test_sessions_state_by_source(self):
        from hermes_hud.models import SessionsState, SessionInfo
        from datetime import datetime

        now = datetime.now()
        state = SessionsState(
            sessions=[
                SessionInfo(id="1", source="cli", title="s1", started_at=now,
                            ended_at=now, message_count=5, tool_call_count=2,
                            input_tokens=100, output_tokens=50),
                SessionInfo(id="2", source="cli", title="s2", started_at=now,
                            ended_at=now, message_count=5, tool_call_count=2,
                            input_tokens=100, output_tokens=50),
                SessionInfo(id="3", source="telegram", title="s3", started_at=now,
                            ended_at=now, message_count=5, tool_call_count=2,
                            input_tokens=100, output_tokens=50),
            ],
            daily_stats=[],
            tool_usage={},
        )
        by_src = state.by_source()
        assert by_src["cli"] == 2
        assert by_src["telegram"] == 1

    def test_skills_state_category_counts(self):
        from hermes_hud.models import SkillsState, SkillInfo
        from datetime import datetime

        state = SkillsState(skills=[
            SkillInfo(name="a", category="devops", description="", path="",
                      modified_at=datetime.now(), file_size=100, is_custom=False),
            SkillInfo(name="b", category="devops", description="", path="",
                      modified_at=datetime.now(), file_size=100, is_custom=True),
            SkillInfo(name="c", category="mlops", description="", path="",
                      modified_at=datetime.now(), file_size=100, is_custom=False),
        ])
        cats = state.category_counts()
        assert cats["devops"] == 2
        assert cats["mlops"] == 1
        assert state.custom_count == 1
