"""Growth timeline — chronological narrative of Hermes learning."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from ..models import TimelineEvent

# Styling by event type
EVENT_STYLES = {
    "milestone": "bold yellow",
    "session": "dim",
    "skill_modified": "green",
    "memory_change": "red bold",
    "config_change": "cyan",
}


class TimelinePanel(Static):
    """Panel showing chronological growth events."""

    DEFAULT_CSS = """
    TimelinePanel {
        height: auto;
        padding: 1 2;
        border: solid $success;
    }
    """

    def __init__(self, events: list[TimelineEvent], **kwargs):
        super().__init__(**kwargs)
        self.events = events

    def compose(self) -> ComposeResult:
        yield Static("[bold]⚗ GROWTH TIMELINE[/bold]")
        yield Static("")

        # Filter to interesting events (skip individual sessions, show milestones + growth)
        interesting = [
            e for e in self.events
            if e.event_type in ("milestone", "skill_modified", "memory_change", "config_change")
        ]

        # Also include first and last session
        sessions = [e for e in self.events if e.event_type == "session"]

        # Show milestones and growth events
        if interesting:
            yield Static("  [bold underline]Key Growth Moments[/bold underline]")
            for event in interesting:
                style = EVENT_STYLES.get(event.event_type, "dim")
                yield Static(
                    f"  [{style}]{event.icon} {event.timestamp:%Y-%m-%d %H:%M} │ "
                    f"{event.title}[/{style}]"
                )
                if event.detail:
                    yield Static(f"    [dim]{event.detail}[/dim]")
        else:
            yield Static("  [dim]No notable growth events yet.[/dim]")

        yield Static("")

        # Session summary by day
        yield Static("  [bold underline]Session Log (by day)[/bold underline]")
        # Group sessions by date
        by_day: dict[str, list[TimelineEvent]] = {}
        for e in sessions:
            day = e.timestamp.strftime("%Y-%m-%d")
            by_day.setdefault(day, []).append(e)

        for day, day_events in sorted(by_day.items()):
            yield Static(
                f"  [bold]{day}[/bold] — {len(day_events)} session{'s' if len(day_events) != 1 else ''}"
            )
            for e in day_events[:3]:  # show up to 3 per day
                yield Static(f"    [dim]{e.icon} {e.title}[/dim]")
            if len(day_events) > 3:
                yield Static(f"    [dim]  ... and {len(day_events) - 3} more[/dim]")
