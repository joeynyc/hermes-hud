"""Agents panel — live agent processes, cron agents, recent sessions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..collectors.agents import AgentsState
from ..collectors.cron import CronState


class AgentsPanel(Widget):
    """Display live agents, cron agents, and recent session activity."""

    DEFAULT_CSS = """
    AgentsPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, agents: AgentsState, cron: CronState, **kwargs):
        super().__init__(**kwargs)
        self.agents = agents
        self.cron = cron

    def compose(self) -> ComposeResult:
        lines = []

        # ── Header ──
        live = self.agents.live()
        idle = self.agents.idle()
        lines.append(f"  [bold]AGENT PROCESSES[/bold]  [dim]{self.agents.live_count} live, {len(idle)} idle[/dim]")
        lines.append("")

        # ── Live agents ──
        if live:
            for agent in live:
                uptime_str = f"  [dim]up {agent.uptime}[/dim]" if agent.uptime else ""
                cwd_str = f"  [dim]{agent.cwd}[/dim]" if agent.cwd else ""
                mem_str = f"  [dim]{agent.mem_mb} MB[/dim]" if agent.mem_mb else ""
                pid_str = f" [dim]\\[{agent.pid}][/dim]" if agent.pid else ""

                lines.append(
                    f"  [green]  ▸[/green] [bold]{agent.name}[/bold]{pid_str}"
                    f"  [green]alive[/green]{uptime_str}{mem_str}{cwd_str}"
                )

                if agent.cmdline:
                    # Truncate and dim the command line
                    cmd = agent.cmdline
                    if len(cmd) > 70:
                        cmd = cmd[:67] + "..."
                    lines.append(f"  [dim]    {cmd}[/dim]")
        else:
            lines.append("  [dim]  No agent processes running[/dim]")

        lines.append("")

        # ── Idle agents ──
        if idle:
            for agent in idle:
                lines.append(f"  [dim]  ▸ {agent.name}    not running[/dim]")
            lines.append("")

        # ── Cron agents (autonomous) ──
        if self.cron.total > 0:
            lines.append(f"  [bold]AUTONOMOUS JOBS[/bold]  [dim]{self.cron.active} active, {self.cron.paused} paused[/dim]")
            lines.append("")

            for job in self.cron.jobs:
                if job.enabled and job.state == "scheduled":
                    dot = "[green]◉[/green]"
                    status = "[green]active[/green]"
                elif job.state == "paused" or not job.enabled:
                    dot = "[yellow]○[/yellow]"
                    status = "[yellow]paused[/yellow]"
                else:
                    dot = "[dim]○[/dim]"
                    status = f"[dim]{job.state}[/dim]"

                # Schedule display
                sched = job.schedule_display
                if sched.startswith("every "):
                    sched = sched[6:]
                import re
                m = re.match(r"^(\d+)m$", sched)
                if m:
                    mins = int(m.group(1))
                    if mins >= 60 and mins % 60 == 0:
                        sched = f"{mins // 60}h"

                # Last run info
                last_str = ""
                if job.last_run_at:
                    last_str = f"  [dim]last: {job.last_run_at[:16]}[/dim]"

                err_str = ""
                if job.last_error:
                    err_str = "  [bold red]✗ error[/bold red]"

                lines.append(
                    f"  {dot} [bold]{job.name}[/bold]  {status}"
                    f"  [dim]every {sched}[/dim]{last_str}{err_str}"
                )

                if job.deliver and job.deliver != "local":
                    lines.append(f"  [dim]    → delivers to {job.deliver}[/dim]")

                if job.skills:
                    lines.append(f"  [dim]    skills: {', '.join(job.skills)}[/dim]")

            lines.append("")

        # ── Recent sessions ──
        if self.agents.recent_sessions:
            lines.append(f"  [bold]RECENT ACTIVITY[/bold]  [dim]last {len(self.agents.recent_sessions)} sessions[/dim]")
            lines.append("")

            for sess in self.agents.recent_sessions:
                # Source badge
                src = sess.source
                if src == "telegram":
                    src_badge = "[cyan]tg[/cyan]"
                elif src == "cli":
                    src_badge = "[green]cli[/green]"
                elif src == "cron":
                    src_badge = "[yellow]cron[/yellow]"
                else:
                    src_badge = f"[dim]{src}[/dim]"

                # Timestamp
                ts = ""
                if sess.started_at:
                    ts = f"{sess.started_at:%m-%d %H:%M}"

                # Title (truncate)
                title = sess.title or "untitled"
                if len(title) > 40:
                    title = title[:37] + "..."

                # Duration
                dur = ""
                if sess.duration_minutes:
                    if sess.duration_minutes < 1:
                        dur = " [dim]<1m[/dim]"
                    elif sess.duration_minutes < 60:
                        dur = f" [dim]{sess.duration_minutes:.0f}m[/dim]"
                    else:
                        h = int(sess.duration_minutes // 60)
                        m = int(sess.duration_minutes % 60)
                        dur = f" [dim]{h}h{m}m[/dim]"

                # Stats
                stats = f"[dim]{sess.message_count} msgs[/dim]"
                if sess.tool_call_count:
                    stats += f" [dim]{sess.tool_call_count} tools[/dim]"

                lines.append(
                    f"  [dim]{ts}[/dim]  {src_badge:>8}  {title:<42}  {stats}{dur}"
                )

            lines.append("")

        yield Static("\n".join(lines))
