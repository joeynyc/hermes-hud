"""Overview panel — top-level stats and capacity gauges."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ProgressBar, Label

from models import HUDState


class CapacityBar(Static):
    """A labeled capacity bar."""

    def __init__(self, label: str, current: int, maximum: int, **kwargs):
        super().__init__(**kwargs)
        self.bar_label = label
        self.current = current
        self.maximum = maximum

    def compose(self) -> ComposeResult:
        pct = (self.current / self.maximum * 100) if self.maximum > 0 else 0
        filled = int(pct / 100 * 30)
        empty = 30 - filled

        if pct >= 95:
            color = "red"
        elif pct >= 75:
            color = "yellow"
        else:
            color = "green"

        bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
        yield Static(f"  {self.bar_label}: {bar} {self.current}/{self.maximum} ({pct:.0f}%)")


class OverviewPanel(Static):
    """Top-level overview panel."""

    DEFAULT_CSS = """
    OverviewPanel {
        height: auto;
        padding: 1 2;
        border: solid $primary;
    }
    """

    def __init__(self, state: HUDState, **kwargs):
        super().__init__(**kwargs)
        self.state = state

    def compose(self) -> ComposeResult:
        s = self.state

        # Date range
        dr = s.sessions.date_range
        if dr[0]:
            days_active = (dr[1] - dr[0]).days + 1
            date_str = f"{dr[0]:%b %d} → {dr[1]:%b %d} ({days_active} days)"
        else:
            date_str = "no sessions"
            days_active = 0

        yield Static(f"[bold]☤ HERMES SELF-IMPROVEMENT HUD[/bold]")
        yield Static("")
        yield Static(
            f"  [bold cyan]{s.config.provider}[/bold cyan]/{s.config.model} "
            f"│ backend: {s.config.backend} "
            f"│ toolsets: {', '.join(s.config.toolsets)}"
        )
        yield Static("")
        yield Static(
            f"  [bold]{s.sessions.total_sessions}[/bold] sessions │ "
            f"[bold]{s.sessions.total_messages}[/bold] messages │ "
            f"[bold]{s.sessions.total_tool_calls}[/bold] tool calls │ "
            f"[bold]{s.skills.total}[/bold] skills │ "
            f"{date_str}"
        )
        yield Static("")

        # Memory capacity
        yield CapacityBar("MEMORY ", s.memory.total_chars, s.memory.max_chars)
        yield CapacityBar("USER   ", s.user.total_chars, s.user.max_chars)
