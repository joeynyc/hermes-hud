"""Corrections panel — timeline of mistakes and lessons learned."""

from __future__ import annotations

import textwrap

from textual.app import ComposeResult
from textual.widgets import Static

from collectors.corrections import Correction, CorrectionsState


SEVERITY_STYLES = {
    "critical": ("red bold", "⚠"),
    "major": ("yellow bold", "✦"),
    "minor": ("dim", "·"),
}


class CorrectionsPanel(Static):
    """Panel showing correction events and lessons learned."""

    DEFAULT_CSS = """
    CorrectionsPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, corrections: CorrectionsState, **kwargs):
        super().__init__(**kwargs)
        self.corrections = corrections

    def compose(self) -> ComposeResult:
        c = self.corrections

        yield Static("[bold]✦ CORRECTIONS & LESSONS LEARNED[/bold]")
        yield Static("")

        # Summary
        sev = c.by_severity()
        src = c.by_source()

        yield Static(
            f"  [bold]{c.total}[/bold] corrections absorbed │ "
            f"[red bold]{sev.get('critical', 0)} critical[/red bold] │ "
            f"[yellow]{sev.get('major', 0)} major[/yellow] │ "
            f"[dim]{sev.get('minor', 0)} minor[/dim]"
        )
        source_parts = []
        for s, count in sorted(src.items(), key=lambda x: -x[1]):
            source_parts.append(f"{s}: {count}")
        yield Static(f"  [dim]Sources: {' │ '.join(source_parts)}[/dim]")
        yield Static("")

        if not c.corrections:
            yield Static("  [dim]No corrections recorded yet. This is either impressive or suspicious.[/dim]")
            return

        # Explanation
        yield Static(
            "  [dim italic]These are moments where I was wrong, corrected, or learned"
            " something the hard way.[/dim italic]"
        )
        yield Static(
            "  [dim italic]Critical = user caught a concrete error. Major = gotcha/pitfall absorbed."
            " Minor = limitation noted.[/dim italic]"
        )
        yield Static("")

        # Critical first, then major, then minor
        for severity_level in ["critical", "major", "minor"]:
            items = [x for x in c.corrections if x.severity == severity_level]
            if not items:
                continue

            style, icon = SEVERITY_STYLES[severity_level]
            yield Static(f"  [{style}]{'─' * 60}[/{style}]")
            yield Static(f"  [{style}]{icon} {severity_level.upper()} ({len(items)})[/{style}]")
            yield Static("")

            for cor in items:
                ts_str = cor.timestamp.strftime("%Y-%m-%d %H:%M") if cor.timestamp else ""

                # Header line
                source_tag = f"[dim]({cor.source})[/dim]"
                time_tag = f"[dim]{ts_str}[/dim] " if ts_str else ""
                yield Static(f"  [{style}]{icon}[/{style}] {time_tag}{source_tag}")

                # Detail — show the full correction text wrapped
                for line in textwrap.fill(cor.detail, width=90).split("\n"):
                    yield Static(f"    [{style}]{line}[/{style}]")

                # Session context
                if cor.session_title:
                    yield Static(f"    [dim]↳ session: {cor.session_title}[/dim]")

                yield Static("")
