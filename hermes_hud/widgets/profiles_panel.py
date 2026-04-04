"""Profiles panel — display all Hermes agent profiles with stats."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..models import ProfileInfo, ProfilesState


def _capacity_bar(pct: float, width: int = 20) -> str:
    """Render a capacity bar like [████████░░░░] 68%."""
    clamped = max(0.0, min(100.0, pct))
    filled = int(clamped / 100 * width)
    empty = width - filled

    if clamped >= 90:
        color = "red"
    elif clamped >= 70:
        color = "yellow"
    else:
        color = "green"

    bar = "█" * filled + "░" * empty
    return f"[{color}]\\[{bar}][/{color}] {clamped:.0f}%"


def _time_ago(dt: datetime | None) -> str:
    """Format a datetime as a human-readable 'ago' string."""
    if dt is None:
        return "never"
    delta = datetime.now() - dt
    secs = int(delta.total_seconds())
    if secs < 0:
        return "just now"
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        h = secs // 3600
        m = (secs % 3600) // 60
        return f"{h}h{m}m ago" if m else f"{h}h ago"
    days = secs // 86400
    return f"{days}d ago"


def _format_tokens(n: int) -> str:
    """Format token count with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _status_dot(status: str) -> str:
    """Return a colored status indicator."""
    if status in ("active", "running"):
        return "[green]◉[/green]"
    if status in ("inactive", "stopped"):
        return "[red]○[/red]"
    if status == "n/a":
        return "[dim]·[/dim]"
    return "[yellow]?[/yellow]"


def _render_profile_card(p: ProfileInfo) -> str:
    """Render a single profile as a text card."""
    lines = []

    # ── Header ──
    name_display = p.name
    if p.is_default:
        name_display += "  [dim](default)[/dim]"

    badge = ""
    if p.is_local:
        badge = "[cyan]local[/cyan]"
    else:
        badge = f"[magenta]{p.provider}[/magenta]"

    # Active indicator
    active_parts = []
    if p.gateway_status == "active":
        active_parts.append("[green]gateway up[/green]")
    if p.server_status == "running":
        active_parts.append("[green]server up[/green]")
    if not active_parts:
        if p.gateway_status == "inactive" and p.server_status in ("stopped", "n/a"):
            active_parts.append("[dim]inactive[/dim]")

    active_str = "  ".join(active_parts)

    lines.append(f"  [bold]{name_display}[/bold]  {badge}  {active_str}")
    lines.append("")

    # ── Model & Backend ──
    model_line = f"    Model    [bold]{p.model or 'not set'}[/bold]"
    if p.provider:
        model_line += f"  [dim]via {p.provider}[/dim]"
    lines.append(model_line)

    if p.base_url:
        lines.append(f"    Backend  [dim]{p.base_url}[/dim]  {_status_dot(p.server_status)}")
    if p.context_length:
        lines.append(f"    Context  [dim]{p.context_length:,} tokens[/dim]")
    if p.skin:
        lines.append(f"    Skin     [dim]{p.skin}[/dim]")

    # ── Personality ──
    if p.soul_summary:
        summary = p.soul_summary
        if len(summary) > 80:
            summary = summary[:77] + "..."
        lines.append(f"    Soul     [italic dim]{summary}[/italic dim]")

    lines.append("")

    # ── Usage Stats ──
    lines.append(f"    Sessions [bold]{p.session_count}[/bold]  "
                 f"Messages [bold]{p.message_count}[/bold]  "
                 f"Tools [bold]{p.tool_call_count}[/bold]")

    tok_in = _format_tokens(p.total_input_tokens)
    tok_out = _format_tokens(p.total_output_tokens)
    tok_total = _format_tokens(p.total_tokens)
    lines.append(f"    Tokens   [dim]{tok_total} total ({tok_in} in / {tok_out} out)[/dim]")

    last = _time_ago(p.last_active)
    lines.append(f"    Active   [dim]{last}[/dim]")

    lines.append("")

    # ── Memory ──
    mem_bar = _capacity_bar(p.memory_capacity_pct, 15)
    user_bar = _capacity_bar(p.user_capacity_pct, 15)
    lines.append(f"    Memory   {mem_bar}  [dim]{p.memory_entries} entries, {p.memory_chars}/{p.memory_max_chars} chars[/dim]")
    lines.append(f"    User     {user_bar}  [dim]{p.user_entries} entries, {p.user_chars}/{p.user_max_chars} chars[/dim]")

    lines.append("")

    # ── Skills & Cron ──
    lines.append(f"    Skills   [bold]{p.skill_count}[/bold]  "
                 f"Cron jobs [bold]{p.cron_job_count}[/bold]")

    # ── Toolsets ──
    if p.toolsets:
        ts_display = ", ".join(p.toolsets)
        lines.append(f"    Toolsets  [dim]{ts_display}[/dim]")

    # ── Compression ──
    if p.compression_enabled:
        comp = f"[green]on[/green]"
        if p.compression_model:
            comp += f"  [dim]{p.compression_model}[/dim]"
        lines.append(f"    Compress  {comp}")

    # ── Services ──
    gw_dot = _status_dot(p.gateway_status)
    srv_dot = _status_dot(p.server_status)
    lines.append(f"    Gateway  {gw_dot} {p.gateway_status}  "
                 f"Server {srv_dot} {p.server_status}")

    # ── API Keys ──
    if p.api_keys:
        keys_str = ", ".join(p.api_keys)
        lines.append(f"    Keys     [dim]{keys_str}[/dim]")

    # ── Alias ──
    if p.has_alias:
        lines.append(f"    Alias    [green]~/.local/bin/{p.name}[/green]")

    return "\n".join(lines)


class ProfilesPanel(Widget):
    """Display all Hermes profiles with detailed stats."""

    DEFAULT_CSS = """
    ProfilesPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, profiles: ProfilesState, **kwargs):
        super().__init__(**kwargs)
        self.profiles = profiles

    def compose(self) -> ComposeResult:
        lines = []

        # ── Header ──
        total = self.profiles.total
        active = self.profiles.active_count
        local = len(self.profiles.local_profiles())

        lines.append(
            f"  [bold]PROFILES[/bold]  "
            f"[dim]{total} total, {active} active, {local} local[/dim]"
        )
        lines.append("")

        if not self.profiles.profiles:
            lines.append("  [dim]No profiles found. Create one with:[/dim]")
            lines.append("  [dim]  hermes profile create <name>[/dim]")
        else:
            for i, profile in enumerate(self.profiles.profiles):
                if i > 0:
                    lines.append("")
                    lines.append("  [dim]─────────────────────────────────────────────────────[/dim]")
                    lines.append("")
                lines.append(_render_profile_card(profile))

        lines.append("")
        yield Static("\n".join(lines))
