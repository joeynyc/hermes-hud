"""Memory panel — shows all memory entries color-coded by type."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.widgets import Static

from ..models import MemoryState

# Category styling
CATEGORY_STYLES = {
    "correction": ("red bold", "✦"),
    "environment": ("cyan", "⚙"),
    "preference": ("green", "♦"),
    "project": ("yellow", "◆"),
    "todo": ("magenta", "☐"),
    "other": ("dim", "·"),
}


class MemoryPanel(Static):
    """Panel showing memory entries categorized and color-coded."""

    DEFAULT_CSS = """
    MemoryPanel {
        height: auto;
        padding: 1 2;
        border: solid $secondary;
    }
    """

    def __init__(self, memory: MemoryState, user: MemoryState, **kwargs):
        super().__init__(**kwargs)
        self.memory = memory
        self.user = user

    def compose(self) -> ComposeResult:
        yield Static("[bold]◎ MEMORY & LEARNING[/bold]")
        yield Static("")

        # Summary
        mem_cats = self.memory.count_by_category()
        usr_cats = self.user.count_by_category()
        corrections = mem_cats.get("correction", 0) + usr_cats.get("correction", 0)
        yield Static(
            f"  {self.memory.entry_count + self.user.entry_count} total entries │ "
            f"[red bold]{corrections} corrections absorbed[/red bold]"
        )
        yield Static("")

        # Memory entries
        yield Static("  [bold underline]Agent Memory[/bold underline] "
                     f"[dim]({self.memory.capacity_pct:.0f}% capacity)[/dim]")
        yield from self._render_entries(self.memory.entries)

        yield Static("")

        # User profile entries
        yield Static("  [bold underline]User Profile[/bold underline] "
                     f"[dim]({self.user.capacity_pct:.0f}% capacity)[/dim]")
        yield from self._render_entries(self.user.entries)

        yield Static("")

        # Legend
        legend_parts = []
        for cat, (style, icon) in CATEGORY_STYLES.items():
            legend_parts.append(f"[{style}]{icon} {cat}[/{style}]")
        yield Static("  " + "  ".join(legend_parts))

    @staticmethod
    def _render_entries(entries):
        for entry in entries:
            style, icon = CATEGORY_STYLES.get(entry.category, ("dim", "·"))
            text = escape(entry.text.replace("\n", " "))
            if len(text) > 100:
                text = text[:97] + "..."
            yield Static(f"  [{style}]{icon} {text}[/{style}]")
