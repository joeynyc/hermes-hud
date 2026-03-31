"""Sessions panel — activity timeline and tool usage."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from models import SessionsState


class SessionsPanel(Static):
    """Panel showing session activity and tool usage."""

    DEFAULT_CSS = """
    SessionsPanel {
        height: auto;
        padding: 1 2;
        border: solid $warning;
    }
    """

    def __init__(self, sessions: SessionsState, **kwargs):
        super().__init__(**kwargs)
        self.sessions = sessions

    def compose(self) -> ComposeResult:
        yield Static("[bold]▣ SESSION ACTIVITY[/bold]")
        yield Static("")

        # Platform breakdown
        sources = self.sessions.by_source()
        source_str = " │ ".join(f"{k}: [bold]{v}[/bold]" for k, v in sorted(sources.items(), key=lambda x: -x[1]))
        yield Static(f"  Platforms: {source_str}")
        yield Static(f"  Total tokens: [bold]{self.sessions.total_tokens:,}[/bold]")
        yield Static("")

        # Daily activity sparkline
        yield Static("  [bold underline]Daily Activity[/bold underline]")
        if self.sessions.daily_stats:
            max_msgs = max(d.messages for d in self.sessions.daily_stats)
            for ds in self.sessions.daily_stats:
                bar_len = int(ds.messages / max(max_msgs, 1) * 35)
                bar = "█" * bar_len
                # Color by intensity
                if ds.messages > max_msgs * 0.7:
                    color = "green"
                elif ds.messages > max_msgs * 0.3:
                    color = "yellow"
                else:
                    color = "dim"
                yield Static(
                    f"  {ds.date} [{color}]{bar}[/{color}] "
                    f"{ds.messages} msgs / {ds.tool_calls} tools"
                )

        yield Static("")

        # Recent sessions
        yield Static("  [bold underline]Recent Sessions[/bold underline]")
        for s in self.sessions.sessions[:8]:
            title = (s.title or "Untitled")[:50]
            yield Static(
                f"  {s.started_at:%m-%d %H:%M} │ "
                f"[bold]{title}[/bold] "
                f"[dim]({s.message_count} msgs, {s.tool_call_count} tools, {s.source})[/dim]"
            )

        yield Static("")

        # Top tools
        if self.sessions.tool_usage:
            yield Static("  [bold underline]Top Tools Used[/bold underline]")
            top_tools = sorted(self.sessions.tool_usage.items(), key=lambda x: -x[1])[:10]
            max_usage = top_tools[0][1] if top_tools else 1
            for tool, count in top_tools:
                bar_len = int(count / max_usage * 20)
                bar = "▓" * bar_len
                yield Static(f"  {tool:<20} [magenta]{bar}[/magenta] {count}")
