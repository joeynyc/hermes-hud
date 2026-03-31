#!/usr/bin/env python3.11
"""Hermes Self-Improvement HUD — Terminal UI."""

from __future__ import annotations

import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from collect import collect_all
from collectors.cron import collect_cron
from collectors.projects import collect_projects
from collectors.health import collect_health
from collectors.corrections import collect_corrections
from models import HUDState
from widgets.overview import OverviewPanel
from widgets.memory_panel import MemoryPanel
from widgets.skills_panel import SkillsPanel
from widgets.sessions_panel import SessionsPanel
from widgets.timeline_panel import TimelinePanel
from widgets.diff_panel import DiffPanel
from widgets.cron_panel import CronPanel
from widgets.projects_panel import ProjectsPanel
from widgets.health_panel import HealthPanel
from widgets.corrections_panel import CorrectionsPanel
from widgets.agents_panel import AgentsPanel
from collectors.agents import collect_agents
from widgets.boot_screen import OverviewNeofetch


# ── Theme palettes (derived from neofetch variants) ──

HERMES_THEMES = [
    Theme(
        name="hermes-ai",
        primary="#00afff",      # bright blue
        secondary="#0087ff",    # deeper blue
        warning="#ffd700",      # gold
        error="#ff8700",        # ember
        success="#00ffff",      # cyan
        accent="#afffff",       # electric white-blue
        foreground="#dadada",   # soft white
        background="#0a0a12",   # near-black with blue cast
        surface="#0e1020",      # dark blue-black
        panel="#141830",        # slightly lighter panel
        boost="#1c2040",        # hover/focus
        dark=True,
        luminosity_spread=0.15,
        text_alpha=0.95,
        variables={"button-color-foreground": "#0a0a12"},
    ),
    Theme(
        name="hermes-blade-runner",
        primary="#ffaf00",      # amber
        secondary="#d78700",    # dark amber
        warning="#ff8700",      # orange
        error="#ff0087",        # neon pink
        success="#00afff",      # neon blue
        accent="#ffd7af",       # warm white
        foreground="#ffd7af",   # warm white
        background="#0a0800",   # near-black with amber cast
        surface="#141008",      # dark amber-black
        panel="#1c1810",        # slightly lighter
        boost="#242018",        # hover/focus
        dark=True,
        luminosity_spread=0.15,
        text_alpha=0.95,
        variables={"button-color-foreground": "#0a0800"},
    ),
    Theme(
        name="hermes-fsociety",
        primary="#00af00",      # terminal green
        secondary="#008700",    # dull green
        warning="#ffff00",      # yellow
        error="#d70000",        # blood red
        success="#00ff00",      # hacker green
        accent="#00ff00",       # hacker green
        foreground="#c0c0c0",   # light grey
        background="#000000",   # pure black
        surface="#080808",      # near-black
        panel="#101010",        # dark grey
        boost="#181818",        # hover/focus
        dark=True,
        luminosity_spread=0.1,
        text_alpha=0.95,
        variables={"button-color-foreground": "#000000"},
    ),
    Theme(
        name="hermes-anime",
        primary="#af5fff",      # purple
        secondary="#875fff",    # hair purple
        warning="#ffafd7",      # soft pink
        error="#ff0087",        # hot pink
        success="#00ffff",      # neon cyan
        accent="#d7afff",       # lilac
        foreground="#dadada",   # soft white
        background="#0a0010",   # near-black with purple cast
        surface="#100820",      # dark purple-black
        panel="#181030",        # slightly lighter
        boost="#201840",        # hover/focus
        dark=True,
        luminosity_spread=0.15,
        text_alpha=0.95,
        variables={"button-color-foreground": "#0a0010"},
    ),
]

DEFAULT_THEME = "hermes-ai"


TAB_DEFS = [
    # (id, label, key)
    ("overview",    "☤ Overview",    "1"),
    ("dashboard",   "◎ Dashboard",   "2"),
    ("cron",        "⏱ Cron Jobs",   "3"),
    ("projects",    "◆ Projects",    "4"),
    ("health",      "⚿ Health",      "5"),
    ("corrections", "✦ Corrections", "6"),
    ("agents",      "⚡ Agents",     "7"),
]


class HermesHUD(App):
    """Hermes Self-Improvement HUD."""

    TITLE = "☤ Hermes HUD"
    SUB_TITLE = "Consciousness Monitor"

    CSS = """
    Screen {
        background: $surface;
    }

    VerticalScroll {
        scrollbar-size: 1 1;
    }

    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 0;
    }

    OverviewPanel {
        margin: 1 2;
        border: solid $primary;
    }

    DiffPanel {
        margin: 0 2 1 2;
        border: solid $secondary;
    }

    MemoryPanel {
        margin: 0 2 1 2;
        border: solid $error;
    }

    SkillsPanel {
        margin: 0 2 1 2;
        border: solid $success;
    }

    SessionsPanel {
        margin: 0 2 1 2;
        border: solid $warning;
    }

    TimelinePanel {
        margin: 0 2 1 2;
        border: solid $accent;
    }

    CronPanel {
        margin: 1 2;
        border: solid $success;
    }

    ProjectsPanel {
        margin: 1 2;
        border: solid $warning;
    }

    HealthPanel {
        margin: 1 2;
        border: solid $primary;
    }

    CorrectionsPanel {
        margin: 1 2;
        border: solid $error;
    }

    AgentsPanel {
        margin: 1 2;
        border: solid $accent;
    }

    .status-line {
        margin: 0 2 1 2;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        *[Binding(td[2], f"switch_tab('{td[0]}')", td[1], show=False) for td in TAB_DEFS],
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.state: HUDState | None = None
        self._booted = False
        for theme in HERMES_THEMES:
            self.register_theme(theme)
        self.theme = DEFAULT_THEME

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            for tab_id, label, _key in TAB_DEFS:
                with TabPane(label, id=f"tab-{tab_id}"):
                    yield VerticalScroll(id=f"{tab_id}-scroll")
        yield Footer()

    def on_mount(self) -> None:
        """Boot the overview neofetch, then lazy-load other tabs on switch."""
        animate = not os.environ.get("HERMES_HUD_NOBOOT")
        overview_scroll = self.query_one("#overview-scroll", VerticalScroll)
        overview_scroll.mount(OverviewNeofetch(animate=animate))
        self._booted = False

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Lazy-load tab data when first switching away from overview."""
        if not self._booted and event.pane.id != "tab-overview":
            self._booted = True
            self._load_data()

    def _status_line(self) -> Static:
        """Create the common status line widget."""
        return Static(
            f"  [dim]Last refreshed: {self.state.collected_at:%H:%M:%S} │ "
            f"[bold]r[/bold] refresh │ [bold]q[/bold] quit │ "
            f"[bold]1-7[/bold] switch tabs │ [bold]j/k[/bold] scroll[/dim]",
            classes="status-line",
        )

    def _populate_tab(self, tab_id: str, widgets: list) -> None:
        """Clear and mount widgets into a tab's scroll container."""
        scroll = self.query_one(f"#{tab_id}-scroll", VerticalScroll)
        scroll.remove_children()
        for w in widgets:
            scroll.mount(w)
        scroll.mount(self._status_line())

    def _load_data(self) -> None:
        """Collect all data and rebuild the dashboard tabs."""
        with ThreadPoolExecutor(max_workers=6) as pool:
            f_state = pool.submit(collect_all)
            f_cron = pool.submit(collect_cron)
            f_projects = pool.submit(collect_projects)
            f_health = pool.submit(collect_health)
            f_corrections = pool.submit(collect_corrections)
            f_agents = pool.submit(collect_agents)

        self.state = f_state.result()
        cron = f_cron.result()
        projects = f_projects.result()
        health = f_health.result()
        corrections = f_corrections.result()
        agents = f_agents.result()

        self._populate_tab("dashboard", [
            OverviewPanel(self.state),
            DiffPanel(),
            MemoryPanel(self.state.memory, self.state.user),
            SkillsPanel(self.state.skills),
            SessionsPanel(self.state.sessions),
            TimelinePanel(self.state.timeline),
        ])
        self._populate_tab("cron", [CronPanel(cron)])
        self._populate_tab("projects", [ProjectsPanel(projects)])
        self._populate_tab("health", [HealthPanel(health)])
        self._populate_tab("corrections", [CorrectionsPanel(corrections)])
        self._populate_tab("agents", [AgentsPanel(agents, cron)])

    def action_refresh(self) -> None:
        """Reload all data including overview."""
        self.notify("Refreshing data...")
        overview_scroll = self.query_one("#overview-scroll", VerticalScroll)
        overview_scroll.remove_children()
        overview_scroll.mount(OverviewNeofetch(animate=False))
        self._booted = True
        self._load_data()
        self.notify("Data refreshed!", severity="information")

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a tab by its ID."""
        self.query_one("#tabs", TabbedContent).active = f"tab-{tab_id}"

    def _active_scroll(self) -> VerticalScroll:
        """Return the scroll container for the active tab."""
        tabs = self.query_one("#tabs", TabbedContent)
        scroll_id = f"#{tabs.active.removeprefix('tab-')}-scroll"
        return self.query_one(scroll_id, VerticalScroll)

    def action_scroll_down(self) -> None:
        self._active_scroll().scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        self._active_scroll().scroll_up(animate=False)

    def action_scroll_home(self) -> None:
        self._active_scroll().scroll_home(animate=False)

    def action_scroll_end(self) -> None:
        self._active_scroll().scroll_end(animate=False)


def main():
    """Entry point."""
    app = HermesHUD()
    app.run()


if __name__ == "__main__":
    main()
