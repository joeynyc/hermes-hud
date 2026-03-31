"""Collect live agent processes, cron agents, and recent session activity."""

from __future__ import annotations

import os
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from collectors.utils import parse_timestamp


@dataclass
class AgentProcess:
    name: str           # hermes, claude, codex, opencode, llama-server
    binary: str         # actual binary name for pgrep
    running: bool = False
    pid: Optional[int] = None
    uptime: Optional[str] = None      # human-readable
    uptime_seconds: int = 0
    cwd: Optional[str] = None         # working directory
    cmdline: Optional[str] = None     # truncated command line
    cpu_pct: Optional[float] = None
    mem_mb: Optional[float] = None


@dataclass
class RecentSession:
    session_id: str
    source: str         # cli, telegram, cron
    title: Optional[str] = None
    started_at: Optional[datetime] = None
    message_count: int = 0
    tool_call_count: int = 0
    model: Optional[str] = None
    duration_minutes: Optional[float] = None


@dataclass
class AgentsState:
    processes: list[AgentProcess] = field(default_factory=list)
    recent_sessions: list[RecentSession] = field(default_factory=list)

    @property
    def live_count(self) -> int:
        return sum(1 for p in self.processes if p.running)

    @property
    def total_processes(self) -> int:
        return len(self.processes)

    def live(self) -> list[AgentProcess]:
        return [p for p in self.processes if p.running]

    def idle(self) -> list[AgentProcess]:
        return [p for p in self.processes if not p.running]


# Agent processes to scan for
AGENT_PROCESSES = [
    ("hermes", "hermes"),
    ("claude", "claude"),
    ("codex", "codex"),
    ("opencode", "opencode"),
    ("llama-server", "llama-server"),
]


def _get_process_info(name: str, binary: str) -> list[AgentProcess]:
    """Find all processes matching the binary name."""
    agents = []
    try:
        # Get PIDs
        result = subprocess.run(
            ["pgrep", "-f", binary],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            agents.append(AgentProcess(name=name, binary=binary, running=False))
            return agents

        pids = [int(p) for p in result.stdout.strip().split("\n") if p.strip()]

        for pid in pids:
            agent = AgentProcess(name=name, binary=binary, running=True, pid=pid)

            # Get uptime from /proc
            try:
                stat_path = Path(f"/proc/{pid}/stat")
                if stat_path.exists():
                    # Get process start time in clock ticks
                    stat_data = stat_path.read_text().split()
                    start_ticks = int(stat_data[21])

                    # Get system uptime
                    uptime_data = Path("/proc/uptime").read_text().split()
                    system_uptime = float(uptime_data[0])

                    # Get clock ticks per second
                    clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])

                    # Calculate process age in seconds
                    process_start_seconds = start_ticks / clk_tck
                    age_seconds = system_uptime - process_start_seconds
                    agent.uptime_seconds = int(age_seconds)
                    agent.uptime = _format_uptime(int(age_seconds))
            except (OSError, ValueError, IndexError, KeyError):
                pass

            # Get working directory
            try:
                cwd_link = Path(f"/proc/{pid}/cwd")
                if cwd_link.exists():
                    cwd = str(cwd_link.resolve())
                    # Shorten home paths
                    home = os.path.expanduser("~")
                    if cwd.startswith(home):
                        cwd = "~" + cwd[len(home):]
                    agent.cwd = cwd
            except (OSError, PermissionError):
                pass

            # Get command line (truncated)
            try:
                cmdline_path = Path(f"/proc/{pid}/cmdline")
                if cmdline_path.exists():
                    cmdline = cmdline_path.read_bytes().decode("utf-8", errors="replace")
                    cmdline = cmdline.replace("\x00", " ").strip()
                    if len(cmdline) > 80:
                        cmdline = cmdline[:77] + "..."
                    agent.cmdline = cmdline
            except (OSError, PermissionError):
                pass

            # Get CPU and memory
            try:
                status_path = Path(f"/proc/{pid}/status")
                if status_path.exists():
                    for line in status_path.read_text().split("\n"):
                        if line.startswith("VmRSS:"):
                            # VmRSS is in kB
                            kb = int(line.split()[1])
                            agent.mem_mb = round(kb / 1024, 1)
                            break
            except (OSError, ValueError, PermissionError):
                pass

            agents.append(agent)

        return agents

    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        agents.append(AgentProcess(name=name, binary=binary, running=False))
        return agents


def _format_uptime(seconds: int) -> str:
    """Format seconds into human-readable uptime."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h{m}m" if m else f"{h}h"
    else:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        return f"{d}d{h}h" if h else f"{d}d"


def _get_recent_sessions(hermes_dir: str, limit: int = 10) -> list[RecentSession]:
    """Get recent sessions from state.db."""
    db_path = Path(hermes_dir) / "state.db"
    if not db_path.exists():
        return []

    sessions = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.id,
                s.source,
                s.title,
                s.started_at,
                s.ended_at,
                s.model,
                COUNT(m.id) as msg_count,
                SUM(CASE WHEN m.tool_calls IS NOT NULL AND m.tool_calls != '[]' THEN 1 ELSE 0 END) as tool_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.started_at DESC
            LIMIT ?
        """, (limit,))

        for row in cursor.fetchall():
            started = None
            duration = None
            started = parse_timestamp(row["started_at"])
            if started:
                ended = parse_timestamp(row["ended_at"])
                if ended:
                    duration = round((ended - started).total_seconds() / 60, 1)

            sessions.append(RecentSession(
                session_id=row["id"],
                source=row["source"] or "unknown",
                title=row["title"],
                started_at=started,
                message_count=row["msg_count"] or 0,
                tool_call_count=row["tool_count"] or 0,
                model=row["model"],
                duration_minutes=duration,
            ))

        conn.close()
    except Exception:
        pass

    return sessions


def collect_agents(hermes_dir: str | None = None) -> AgentsState:
    """Collect all agent data."""
    if hermes_dir is None:
        hermes_dir = os.path.expanduser("~/.hermes")

    # Scan for agent processes
    processes = []
    seen_pids = set()

    for name, binary in AGENT_PROCESSES:
        found = _get_process_info(name, binary)
        for agent in found:
            # Deduplicate: the hermes pgrep might catch itself or child processes
            if agent.pid and agent.pid in seen_pids:
                continue
            if agent.pid:
                seen_pids.add(agent.pid)

                # Skip the current process (this HUD)
                if agent.pid == os.getpid():
                    continue
                # Skip parent process
                if agent.pid == os.getppid():
                    continue

            processes.append(agent)

    # Get recent sessions
    recent_sessions = _get_recent_sessions(hermes_dir)

    return AgentsState(
        processes=processes,
        recent_sessions=recent_sessions,
    )
