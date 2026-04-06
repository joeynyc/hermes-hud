"""Tests for tmux pane discovery, process matching, and operator alert detection."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from hermes_hud.collectors.agents import (
    AgentProcess,
    AgentsState,
    OperatorAlert,
    TmuxPane,
    _capture_pane_preview,
    _detect_operator_alerts,
    _find_alert_in_lines,
    _get_ttys_for_pids,
    _get_tty_for_pid,
    _list_tmux_panes,
    _match_processes_to_panes,
    _parse_etime,
)


# ── _parse_etime ──────────────────────────────────────────────────────────────

class TestParseEtime:
    def test_mm_ss(self):
        assert _parse_etime("01:30") == 90

    def test_hh_mm_ss(self):
        assert _parse_etime("01:02:03") == 3723

    def test_dd_hh_mm_ss(self):
        assert _parse_etime("1-02:03:04") == 1 * 86400 + 2 * 3600 + 3 * 60 + 4

    def test_zero(self):
        assert _parse_etime("00:00") == 0

    def test_invalid(self):
        assert _parse_etime("bogus") == 0


# ── _list_tmux_panes ──────────────────────────────────────────────────────────

SAMPLE_TMUX_OUTPUT = (
    "%0\t/dev/pts/2\tmain\t0\t0\tbash\t1000\n"
    "%1\t/dev/pts/3\tmain\t0\t1\tclaude\t1234\n"
    "%2\t/dev/pts/4\twork\t1\t0\tpython\t5678\n"
)


class TestListTmuxPanes:
    def _make_result(self, stdout="", returncode=0):
        r = MagicMock()
        r.returncode = returncode
        r.stdout = stdout
        return r

    def test_parse_valid_output(self):
        with patch("subprocess.run", return_value=self._make_result(SAMPLE_TMUX_OUTPUT)):
            panes = _list_tmux_panes()
        assert len(panes) == 3
        assert panes[0].pane_id == "%0"
        assert panes[0].tty == "/dev/pts/2"
        assert panes[0].session_name == "main"
        assert panes[0].window_index == 0
        assert panes[0].pane_index == 0
        assert panes[0].current_command == "bash"
        assert panes[0].pane_pid == 1000
        assert panes[1].pane_id == "%1"
        assert panes[1].current_command == "claude"
        assert panes[2].session_name == "work"

    def test_no_tmux_server(self):
        """tmux returns non-zero when no server is running."""
        with patch("subprocess.run", return_value=self._make_result("", returncode=1)):
            panes = _list_tmux_panes()
        assert panes == []

    def test_tmux_not_installed(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            panes = _list_tmux_panes()
        assert panes == []

    def test_tmux_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tmux", 5)):
            panes = _list_tmux_panes()
        assert panes == []

    def test_malformed_lines_skipped(self):
        bad_output = "%0\t/dev/pts/2\tmain\t0\t0\tbash\t1000\nBROKENLINE\n"
        with patch("subprocess.run", return_value=self._make_result(bad_output)):
            panes = _list_tmux_panes()
        assert len(panes) == 1

    def test_empty_output(self):
        with patch("subprocess.run", return_value=self._make_result("")):
            panes = _list_tmux_panes()
        assert panes == []


# ── _get_tty_for_pid ──────────────────────────────────────────────────────────

class TestGetTtysForPids:
    def _make_result(self, stdout="", returncode=0):
        r = MagicMock()
        r.returncode = returncode
        r.stdout = stdout
        return r

    def test_returns_mapping(self):
        output = "  1234 pts/3\n  5678 pts/4\n"
        with patch("subprocess.run", return_value=self._make_result(output)):
            result = _get_ttys_for_pids([1234, 5678])
        assert result == {1234: "pts/3", 5678: "pts/4"}

    def test_excludes_question_mark(self):
        output = "  1234 ?\n"
        with patch("subprocess.run", return_value=self._make_result(output)):
            result = _get_ttys_for_pids([1234])
        assert result == {}

    def test_empty_pids(self):
        assert _get_ttys_for_pids([]) == {}

    def test_failure_returns_empty(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert _get_ttys_for_pids([1234]) == {}

    def test_nonzero_returncode(self):
        with patch("subprocess.run", return_value=self._make_result("", returncode=1)):
            assert _get_ttys_for_pids([1234]) == {}


class TestGetTtyForPid:
    def test_delegates_to_batch(self):
        with patch("hermes_hud.collectors.agents._get_ttys_for_pids", return_value={1234: "pts/3"}):
            assert _get_tty_for_pid(1234) == "pts/3"

    def test_returns_none_when_not_found(self):
        with patch("hermes_hud.collectors.agents._get_ttys_for_pids", return_value={}):
            assert _get_tty_for_pid(1234) is None


# ── _match_processes_to_panes ─────────────────────────────────────────────────

class TestMatchProcessesToPanes:
    def _make_pane(self, pane_id, tty, session="main", win=0, idx=0):
        return TmuxPane(
            pane_id=pane_id,
            session_name=session,
            window_index=win,
            pane_index=idx,
            tty=tty,
            current_command="claude",
            pane_pid=9999,
        )

    def _make_agent(self, name="claude", pid=1234):
        return AgentProcess(name=name, binary=name, running=True, pid=pid)

    def test_match_by_tty(self):
        agent = self._make_agent(pid=1234)
        pane = self._make_pane("%0", "/dev/pts/3")
        with patch("hermes_hud.collectors.agents._get_ttys_for_pids", return_value={1234: "pts/3"}):
            _match_processes_to_panes([agent], [pane])
        assert agent.tty == "pts/3"
        assert agent.tmux_pane == "%0"
        assert agent.tmux_jump_hint == "main:0.0"
        assert pane.agent_pid == 1234
        assert pane.jump_hint == "main:0.0"

    def test_no_match_different_tty(self):
        agent = self._make_agent(pid=1234)
        pane = self._make_pane("%0", "/dev/pts/5")
        with patch("hermes_hud.collectors.agents._get_ttys_for_pids", return_value={1234: "pts/3"}):
            _match_processes_to_panes([agent], [pane])
        assert agent.tmux_pane is None
        assert pane.agent_pid is None

    def test_multiple_agents_multiple_panes(self):
        a1 = self._make_agent("claude", pid=100)
        a2 = self._make_agent("codex", pid=200)
        a3 = self._make_agent("hermes", pid=300)
        p1 = self._make_pane("%0", "/dev/pts/1")
        p2 = self._make_pane("%1", "/dev/pts/2")
        p3 = self._make_pane("%2", "/dev/pts/9")

        with patch("hermes_hud.collectors.agents._get_ttys_for_pids",
                   return_value={100: "pts/1", 200: "pts/2", 300: "pts/99"}):
            _match_processes_to_panes([a1, a2, a3], [p1, p2, p3])

        assert a1.tmux_pane == "%0"
        assert a2.tmux_pane == "%1"
        assert a3.tmux_pane is None  # pts/99 not in panes
        assert p1.agent_pid == 100
        assert p2.agent_pid == 200
        assert p3.agent_pid is None

    def test_idle_agents_skipped(self):
        agent = AgentProcess(name="claude", binary="claude", running=False, pid=1234)
        pane = self._make_pane("%0", "/dev/pts/3")
        with patch("hermes_hud.collectors.agents._get_ttys_for_pids") as mock_ttys:
            _match_processes_to_panes([agent], [pane])
        # No running agents → batch call with empty list → no lookup needed
        mock_ttys.assert_called_once_with([])
        assert pane.agent_pid is None


# ── _capture_pane_preview ─────────────────────────────────────────────────────

class TestCapturePanePreview:
    def _make_result(self, stdout="", returncode=0):
        r = MagicMock()
        r.returncode = returncode
        r.stdout = stdout
        return r

    def test_returns_lines(self):
        output = "line one\nline two\n\nline three\n"
        with patch("subprocess.run", return_value=self._make_result(output)):
            lines = _capture_pane_preview("%0")
        assert lines == ["line one", "line two", "line three"]

    def test_failure_returns_empty(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert _capture_pane_preview("%0") == []

    def test_nonzero_returncode(self):
        with patch("subprocess.run", return_value=self._make_result("", returncode=1)):
            assert _capture_pane_preview("%0") == []


# ── _find_alert_in_lines ─────────────────────────────────────────────────────

class TestFindAlertInLines:
    def test_approval(self):
        result = _find_alert_in_lines(["Allow write to /etc? (y/n)"])
        assert result is not None
        assert result[0] == "approval"

    def test_error(self):
        result = _find_alert_in_lines(["Traceback (most recent call last):"])
        assert result is not None
        assert result[0] == "error"

    def test_no_match(self):
        assert _find_alert_in_lines(["Processing...", "Done."]) is None

    def test_empty(self):
        assert _find_alert_in_lines([]) is None

    def test_first_match_wins(self):
        result = _find_alert_in_lines(["Allow this?", "Error occurred"])
        assert result is not None
        assert result[0] == "approval"

    def test_summary_truncated(self):
        long_line = "Allow " + "x" * 80
        result = _find_alert_in_lines([long_line])
        assert result is not None
        assert len(result[1]) <= 60


# ── _detect_operator_alerts ───────────────────────────────────────────────────

class TestDetectOperatorAlerts:
    def _make_pane(self, pane_id="%0", agent_pid=1234, preview=None):
        p = TmuxPane(
            pane_id=pane_id,
            session_name="main",
            window_index=0,
            pane_index=0,
            tty="/dev/pts/3",
            current_command="claude",
            pane_pid=9999,
            agent_pid=agent_pid,
            jump_hint="main:0.0",
        )
        p.preview_lines = preview or []
        return p

    def _make_agent(self, pid=1234, uptime=60):
        a = AgentProcess(name="claude", binary="claude", running=True, pid=pid)
        a.uptime_seconds = uptime
        return a

    def test_approval_pattern(self):
        pane = self._make_pane(preview=["Allow write to /etc/hosts? (y/n)"])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "approval"
        assert alerts[0].agent_name == "claude"
        assert alerts[0].jump_hint == "main:0.0"

    def test_error_pattern(self):
        pane = self._make_pane(preview=["Traceback (most recent call last):"])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "error"

    def test_question_pattern(self):
        pane = self._make_pane(preview=["Enter the database name:"])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "question"

    def test_clean_output_no_alerts(self):
        pane = self._make_pane(preview=["Processing files...", "Done."])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert alerts == []

    def test_one_alert_per_pane(self):
        """Even if multiple patterns match, only one alert per pane."""
        pane = self._make_pane(preview=["Allow this? (y/n)", "Traceback blah"])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert len(alerts) == 1

    def test_stuck_heuristic(self):
        """No preview lines + high uptime = stuck alert."""
        pane = self._make_pane(preview=[])
        agent = self._make_agent(uptime=400)
        alerts = _detect_operator_alerts([pane], [agent])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "stuck"

    def test_stuck_heuristic_low_uptime_ignored(self):
        """No preview lines + low uptime = no alert."""
        pane = self._make_pane(preview=[])
        agent = self._make_agent(uptime=60)
        alerts = _detect_operator_alerts([pane], [agent])
        assert alerts == []

    def test_unmatched_pane_skipped(self):
        """Panes with no agent_pid should not produce alerts."""
        pane = self._make_pane(agent_pid=None, preview=["Allow this? (y/n)"])
        agent = self._make_agent()
        alerts = _detect_operator_alerts([pane], [agent])
        assert alerts == []


# ── AgentsState new fields ────────────────────────────────────────────────────

class TestAgentsStateNewFields:
    def test_has_tmux_fields(self):
        state = AgentsState()
        assert hasattr(state, "tmux_panes")
        assert isinstance(state.tmux_panes, list)
        assert hasattr(state, "operator_alerts")
        assert isinstance(state.operator_alerts, list)

    def test_has_tmux_false_when_empty(self):
        state = AgentsState()
        assert state.has_tmux is False

    def test_has_tmux_true_when_panes(self):
        pane = TmuxPane("%0", "main", 0, 0, "/dev/pts/1", "bash", 1000)
        state = AgentsState(tmux_panes=[pane])
        assert state.has_tmux is True

    def test_matched_pane_count(self):
        p1 = TmuxPane("%0", "main", 0, 0, "/dev/pts/1", "claude", 1000, agent_pid=42)
        p2 = TmuxPane("%1", "main", 0, 1, "/dev/pts/2", "bash", 1001)
        state = AgentsState(tmux_panes=[p1, p2])
        assert state.matched_pane_count == 1

    def test_unmatched_interesting_panes_excludes_shells(self):
        p_agent = TmuxPane("%0", "main", 0, 0, "/dev/pts/1", "claude", 1000, agent_pid=42)
        p_shell = TmuxPane("%1", "main", 0, 1, "/dev/pts/2", "bash", 1001)
        p_interesting = TmuxPane("%2", "main", 0, 2, "/dev/pts/3", "python", 1002)
        state = AgentsState(tmux_panes=[p_agent, p_shell, p_interesting])
        unmatched = state.unmatched_interesting_panes
        assert len(unmatched) == 1
        assert unmatched[0].pane_id == "%2"
