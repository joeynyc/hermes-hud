"""Projects panel — shows all projects and their git status."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from collectors.projects import ProjectInfo, ProjectsState


ACTIVITY_STYLES = {
    "active": ("green bold", "▶"),
    "recent": ("yellow", "◆"),
    "stale": ("dim", "◇"),
    "unknown": ("dim", "·"),
    "no git": ("dim italic", "─"),
}


class ProjectsPanel(Static):
    """Panel showing all projects and their status."""

    DEFAULT_CSS = """
    ProjectsPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, projects: ProjectsState, **kwargs):
        super().__init__(**kwargs)
        self.projects = projects

    def compose(self) -> ComposeResult:
        yield Static("[bold]◆ PROJECTS[/bold]")
        yield Static("")

        ps = self.projects

        # Summary
        yield Static(
            f"  [bold]{ps.total}[/bold] projects │ "
            f"[bold]{ps.git_repos}[/bold] git repos │ "
            f"[green bold]{ps.active_count} active[/green bold] │ "
            f"[yellow]{ps.dirty_count} dirty[/yellow]"
        )
        yield Static(f"  [dim]{ps.projects_dir}[/dim]")
        yield Static("")

        # Projects sorted by activity
        sorted_projects = ps.sorted_by_recent()

        # Active projects first with full detail
        active = [p for p in sorted_projects if p.is_git and p.activity_level == "active"]
        recent = [p for p in sorted_projects if p.is_git and p.activity_level == "recent"]
        stale = [p for p in sorted_projects if p.is_git and p.activity_level == "stale"]
        no_git = [p for p in sorted_projects if not p.is_git]

        if active:
            yield Static("  [green bold]▶ ACTIVE[/green bold]")
            for p in active:
                yield from self._render_project(p, "green")
            yield Static("")

        if recent:
            yield Static("  [yellow]◆ RECENT[/yellow]")
            for p in recent:
                yield from self._render_project(p, "yellow")
            yield Static("")

        if stale:
            yield Static("  [dim]◇ STALE[/dim]")
            for p in stale:
                yield from self._render_project_compact(p)
            yield Static("")

        if no_git:
            yield Static("  [dim]─ NO GIT[/dim]")
            for p in no_git:
                langs = f" [{', '.join(p.languages)}]" if p.languages else ""
                mod = f" (modified {p.last_modified:%b %d})" if p.last_modified else ""
                yield Static(f"    [dim]{p.name}{langs}{mod}[/dim]")

    def _render_project(self, p: ProjectInfo, color: str) -> list:
        """Render a project with full detail."""
        # Name + branch + status
        dirty_tag = f" [red]({p.dirty_files} dirty)[/red]" if p.dirty_files > 0 else " [green](clean)[/green]"
        langs = f" [dim]{', '.join(p.languages)}[/dim]" if p.languages else ""

        yield Static(
            f"    [{color} bold]{p.name}[/{color} bold]"
            f"  [dim]({p.branch})[/dim]{dirty_tag}{langs}"
        )

        # Last commit
        if p.last_commit_msg:
            msg = p.last_commit_msg[:70]
            if len(p.last_commit_msg) > 70:
                msg += "..."
            yield Static(
                f"      [dim]{p.last_commit_ago} │[/dim] {msg}"
            )

        # Stats
        markers = []
        if p.total_commits:
            markers.append(f"{p.total_commits} commits")
        if p.has_readme:
            markers.append("README")
        if p.has_package_json:
            markers.append("npm")
        if p.has_requirements or p.has_pyproject:
            markers.append("pip")
        if markers:
            yield Static(f"      [dim]{' │ '.join(markers)}[/dim]")

    def _render_project_compact(self, p: ProjectInfo) -> list:
        """Render a stale project in compact form."""
        dirty_tag = f" [red]({p.dirty_files} dirty)[/red]" if p.dirty_files > 0 else ""
        ago = f" — {p.last_commit_ago}" if p.last_commit_ago else ""

        yield Static(
            f"    [dim]{p.name} ({p.branch}){dirty_tag}{ago}[/dim]"
        )
