"""Diff panel — shows changes since last snapshot."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from ..snapshot import load_snapshots, diff_report


class DiffPanel(Static):
    """Panel showing changes since last snapshot."""

    DEFAULT_CSS = """
    DiffPanel {
        height: auto;
        padding: 1 2;
        border: solid $secondary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]◐ GROWTH DELTA[/bold]")
        yield Static("")

        snapshots = load_snapshots()

        if len(snapshots) < 2:
            yield Static("  [dim]Only one snapshot available. Run snapshot.py daily to track changes.[/dim]")
            yield Static(f"  [dim]Snapshots: {len(snapshots)}[/dim]")
            if snapshots:
                s = snapshots[0]
                yield Static(f"  [dim]First snapshot: {s.get('timestamp', 'unknown')}[/dim]")
            return

        current = snapshots[-1]
        previous = snapshots[-2]

        yield Static(
            f"  Comparing: [dim]{previous.get('timestamp', '?')}[/dim] → "
            f"[bold]{current.get('timestamp', '?')}[/bold]"
        )
        yield Static(f"  [dim]({len(snapshots)} snapshots total)[/dim]")
        yield Static("")

        # Render diff
        fields = [
            ("sessions", "Sessions", "cyan"),
            ("messages", "Messages", "cyan"),
            ("tool_calls", "Tool calls", "cyan"),
            ("skills", "Skills", "green"),
            ("custom_skills", "Custom skills", "green bold"),
            ("memory_entries", "Memory entries", "red"),
            ("user_entries", "User entries", "red"),
            ("tokens", "Tokens", "yellow"),
        ]

        for key, label, color in fields:
            cur = current.get(key, 0)
            prev = previous.get(key, 0)
            delta = cur - prev
            if delta > 0:
                yield Static(f"  [{color}]↑ {label}: {prev:,} → {cur:,} (+{delta:,})[/{color}]")
            elif delta < 0:
                yield Static(f"  [red]↓ {label}: {prev:,} → {cur:,} ({delta:,})[/red]")
            else:
                yield Static(f"  [dim]= {label}: {cur:,} (unchanged)[/dim]")

        # Category changes
        cur_cats = set(current.get("categories", []))
        prev_cats = set(previous.get("categories", []))
        new_cats = cur_cats - prev_cats
        lost_cats = prev_cats - cur_cats
        if new_cats:
            yield Static(f"  [green bold]★ New categories: {', '.join(sorted(new_cats))}[/green bold]")
        if lost_cats:
            yield Static(f"  [red]✗ Lost categories: {', '.join(sorted(lost_cats))}[/red]")
