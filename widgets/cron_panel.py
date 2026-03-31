"""Cron jobs panel — shows what Hermes is doing autonomously."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from collectors.cron import CronJob, CronState


def _format_time(iso_str: str | None) -> str:
    """Format ISO timestamp to readable string."""
    if not iso_str:
        return "never"
    try:
        # Strip timezone for display
        clean = iso_str.split(".")[0].replace("T", " ")
        return clean
    except Exception:
        return str(iso_str)


def _state_style(job: CronJob) -> tuple[str, str]:
    """Return (style, icon) for a job's state."""
    if not job.enabled:
        return "dim", "⏸"
    if job.state == "paused":
        return "yellow", "⏸"
    if job.last_error:
        return "red bold", "✗"
    if job.state == "running":
        return "cyan bold", "▶"
    if job.state == "scheduled":
        return "green", "◆"
    return "dim", "·"


class CronPanel(Static):
    """Panel showing all cron jobs and their status."""

    DEFAULT_CSS = """
    CronPanel {
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, cron: CronState, **kwargs):
        super().__init__(**kwargs)
        self.cron = cron

    def compose(self) -> ComposeResult:
        yield Static("[bold]⏱ AUTONOMOUS JOBS[/bold]")
        yield Static("")

        if not self.cron.jobs:
            yield Static("  [dim]No cron jobs configured.[/dim]")
            return

        # Summary
        yield Static(
            f"  [bold]{self.cron.total}[/bold] total │ "
            f"[green]{self.cron.active} active[/green] │ "
            f"[yellow]{self.cron.paused} paused[/yellow]"
            + (f" │ [red bold]errors detected[/red bold]" if self.cron.has_errors else "")
        )
        if self.cron.updated_at:
            yield Static(f"  [dim]Last updated: {_format_time(self.cron.updated_at)}[/dim]")
        yield Static("")

        # Job list
        for job in self.cron.jobs:
            style, icon = _state_style(job)

            yield Static(f"  [{style}]{'─' * 70}[/{style}]")
            yield Static(
                f"  [{style}]{icon} {job.name}[/{style}]"
                f"  [dim]({job.id})[/dim]"
            )
            yield Static("")

            # Schedule and delivery
            repeat_str = "forever" if job.repeat_total is None else f"{job.repeat_completed}/{job.repeat_total}"
            yield Static(
                f"    Schedule:  [bold]{job.schedule_display}[/bold] │ "
                f"Repeat: {repeat_str} │ "
                f"Deliver: {job.deliver}"
            )

            # Model/provider override
            if job.model or job.provider:
                model_str = f"{job.provider or 'default'}/{job.model or 'default'}"
                yield Static(f"    Model:     {model_str}")

            # Skills
            if job.skills:
                yield Static(f"    Skills:    {', '.join(job.skills)}")

            # Timing
            yield Static(
                f"    Created:   {_format_time(job.created_at)}"
            )
            yield Static(
                f"    Next run:  [bold cyan]{_format_time(job.next_run_at)}[/bold cyan]"
            )
            if job.last_run_at:
                status_style = "green" if job.last_status == "success" else "red"
                yield Static(
                    f"    Last run:  {_format_time(job.last_run_at)} "
                    f"[{status_style}]({job.last_status or 'unknown'})[/{status_style}]"
                )
            else:
                yield Static(f"    Last run:  [dim]not yet run[/dim]")

            # Error
            if job.last_error:
                yield Static(f"    [red bold]Error: {job.last_error}[/red bold]")

            # Prompt preview
            prompt_preview = job.prompt[:120]
            if len(job.prompt) > 120:
                prompt_preview += "..."
            yield Static(f"    Prompt:    [dim]{prompt_preview}[/dim]")

            # Paused reason
            if job.paused_reason:
                yield Static(f"    [yellow]Paused: {job.paused_reason}[/yellow]")

            yield Static("")
