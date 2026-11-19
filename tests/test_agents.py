"""Tests for live agent collection."""

from __future__ import annotations

import concurrent.futures
import threading

from hermes_hud.collectors import agents as agents_module
from hermes_hud.collectors.agents import AgentProcess


def test_process_scans_are_bounded_concurrent_and_results_stay_ordered(monkeypatch):
    specs = [("first", "first-bin"), ("second", "second-bin"), ("third", "third-bin")]
    barrier = threading.Barrier(len(specs))
    calls = []
    workers = []

    def fake_executor(*, max_workers):
        workers.append(max_workers)
        return concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def fake_process_info(name, binary):
        calls.append((name, binary))
        barrier.wait(timeout=2)
        if name == "first":
            return [
                AgentProcess(name, binary, running=True, pid=101),
                AgentProcess(name, binary, running=True, pid=9001),
            ]
        if name == "second":
            return [
                AgentProcess(name, binary, running=True, pid=101),
                AgentProcess(name, binary, running=True, pid=9002),
                AgentProcess(name, binary, running=True, pid=202),
            ]
        return [AgentProcess(name, binary, running=False)]

    monkeypatch.setattr(agents_module, "AGENT_PROCESSES", specs)
    monkeypatch.setattr(agents_module, "ThreadPoolExecutor", fake_executor)
    monkeypatch.setattr(agents_module, "_get_process_info", fake_process_info)
    monkeypatch.setattr(agents_module, "_list_tmux_panes", lambda: [])
    monkeypatch.setattr(agents_module, "_get_recent_sessions", lambda hermes_dir: [])
    monkeypatch.setattr(agents_module.os, "getpid", lambda: 9001)
    monkeypatch.setattr(agents_module.os, "getppid", lambda: 9002)

    state = agents_module.collect_agents("/missing")

    assert workers == [4]
    assert sorted(calls) == sorted(specs)
    assert [(agent.name, agent.pid, agent.running) for agent in state.processes] == [
        ("first", 101, True),
        ("second", 202, True),
        ("third", None, False),
    ]


def test_process_scan_fallback_is_preserved(monkeypatch):
    def missing_pgrep(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(agents_module.subprocess, "run", missing_pgrep)

    result = agents_module._get_process_info_linux("missing", "missing-bin")

    assert len(result) == 1
    assert result[0].name == "missing"
    assert result[0].binary == "missing-bin"
    assert result[0].running is False
    assert result[0].pid is None
