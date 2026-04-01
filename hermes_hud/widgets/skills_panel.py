"""Skills panel — category breakdown and recently modified."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from ..models import SkillsState


class SkillsPanel(Static):
    """Panel showing skill library overview."""

    DEFAULT_CSS = """
    SkillsPanel {
        height: auto;
        padding: 1 2;
        border: solid $accent;
    }
    """

    def __init__(self, skills: SkillsState, **kwargs):
        super().__init__(**kwargs)
        self.skills = skills

    def compose(self) -> ComposeResult:
        yield Static("[bold]⚙ SKILL LIBRARY[/bold]")
        yield Static("")

        yield Static(
            f"  [bold]{self.skills.total}[/bold] skills │ "
            f"[bold green]{self.skills.custom_count}[/bold green] custom │ "
            f"{self.skills.total - self.skills.custom_count} bundled │ "
            f"{len(self.skills.category_counts())} categories"
        )
        yield Static("")

        # Category bar chart
        yield Static("  [bold underline]Categories[/bold underline]")
        cat_counts = self.skills.category_counts()
        max_count = max(cat_counts.values()) if cat_counts else 1
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            bar_len = int(count / max_count * 25)
            bar = "▓" * bar_len
            yield Static(f"  {cat:<24} [cyan]{bar}[/cyan] {count}")

        yield Static("")

        # Recently modified
        yield Static("  [bold underline]Recently Modified[/bold underline]")
        for skill in self.skills.recently_modified(5):
            custom_tag = " [green]★ custom[/green]" if skill.is_custom else ""
            yield Static(
                f"  {skill.modified_at:%Y-%m-%d %H:%M} │ "
                f"[bold]{skill.name}[/bold] ({skill.category}){custom_tag}"
            )
