"""Health panel — API keys, services, system status."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from collectors.health import HealthState


class HealthPanel(Static):
    """Panel showing system health status."""

    DEFAULT_CSS = """
    HealthPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, health: HealthState, **kwargs):
        super().__init__(**kwargs)
        self.health = health

    def compose(self) -> ComposeResult:
        h = self.health

        # Overall status
        if h.all_healthy:
            yield Static("[bold green]⚿ SYSTEM HEALTH — ALL OK[/bold green]")
        else:
            problems = h.keys_missing + sum(1 for s in h.services if not s.running)
            yield Static(f"[bold yellow]⚿ SYSTEM HEALTH — {problems} ISSUE{'S' if problems != 1 else ''}[/bold yellow]")
        yield Static("")

        # Model & Provider
        yield Static(
            f"  Model: [bold]{h.config_provider}/{h.config_model}[/bold]"
        )
        db_size = f"{h.state_db_size / 1024 / 1024:.1f} MB" if h.state_db_size else "?"
        yield Static(
            f"  State DB: {'[green]exists[/green]' if h.state_db_exists else '[red]missing[/red]'}"
            f" ({db_size})"
        )
        yield Static("")

        # API Keys
        yield Static("  [bold underline]API Keys[/bold underline]")
        for key in h.keys:
            if key.present:
                yield Static(f"  [green]✔ {key.name}[/green]")
            else:
                note = f" — {key.note}" if key.note else ""
                yield Static(f"  [red]✗ {key.name}[/red][dim]{note}[/dim]")
        yield Static(
            f"  [dim]{h.keys_ok} configured, {h.keys_missing} missing[/dim]"
        )
        yield Static("")

        # Services
        yield Static("  [bold underline]Services[/bold underline]")
        for svc in h.services:
            if svc.running:
                pid_str = f" (pid {svc.pid})" if svc.pid else ""
                yield Static(f"  [green]✔ {svc.name}{pid_str}[/green]")
            else:
                note = f" — {svc.note}" if svc.note else ""
                yield Static(f"  [red]✗ {svc.name}[/red][dim]{note}[/dim]")
        yield Static("")

        # Quick diagnostics
        yield Static("  [bold underline]Diagnostics[/bold underline]")

        if not h.hermes_dir_exists:
            yield Static("  [red bold]✗ ~/.hermes directory not found![/red bold]")

        missing_critical = [k for k in h.keys if not k.present and k.name in (
            "ANTHROPIC_API_KEY", "TELEGRAM_BOT_TOKEN"
        )]
        if missing_critical:
            for k in missing_critical:
                yield Static(f"  [red bold]⚠ {k.name} missing — core functionality affected[/red bold]")

        missing_optional = [k for k in h.keys if not k.present and k.name not in (
            "ANTHROPIC_API_KEY", "TELEGRAM_BOT_TOKEN"
        )]
        if missing_optional:
            names = ", ".join(k.name for k in missing_optional)
            yield Static(f"  [yellow]◐ Optional keys not set: {names}[/yellow]")

        dead_services = [s for s in h.services if not s.running and "unavailable" not in (s.note or "")]
        if dead_services:
            for s in dead_services:
                yield Static(f"  [yellow]◐ {s.name} not running[/yellow]")

        if h.all_healthy and not missing_optional:
            yield Static("  [green]All systems nominal.[/green]")
        elif h.all_healthy:
            yield Static("  [green]Core systems OK. Optional keys above can be added when needed.[/green]")
