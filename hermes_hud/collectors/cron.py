"""Collect Hermes cron job data."""

from __future__ import annotations

import json
import os

from .utils import default_hermes_dir
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class CronJob:
    id: str
    name: str
    prompt: str
    schedule_display: str
    enabled: bool
    state: str  # scheduled, running, paused, completed
    created_at: Optional[str] = None
    next_run_at: Optional[str] = None
    last_run_at: Optional[str] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    deliver: str = "local"
    repeat_total: Optional[int] = None
    repeat_completed: int = 0
    model: Optional[str] = None
    provider: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    paused_reason: Optional[str] = None


@dataclass
class CronState:
    jobs: list[CronJob] = field(default_factory=list)
    updated_at: Optional[str] = None
    output_dir: str = ""

    @property
    def total(self) -> int:
        return len(self.jobs)

    @property
    def active(self) -> int:
        return sum(1 for j in self.jobs if j.enabled and j.state == "scheduled")

    @property
    def paused(self) -> int:
        return sum(1 for j in self.jobs if not j.enabled or j.state == "paused")

    @property
    def has_errors(self) -> bool:
        return any(j.last_error for j in self.jobs)


def collect_cron(hermes_dir: str | None = None) -> CronState:
    """Collect cron job data from jobs.json."""
    if hermes_dir is None:
        hermes_dir = default_hermes_dir(hermes_dir)

    cron_dir = Path(hermes_dir) / "cron"
    jobs_file = cron_dir / "jobs.json"
    output_dir = cron_dir / "output"

    if not jobs_file.exists():
        return CronState()

    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return CronState()

    jobs = []
    for j in data.get("jobs", []):
        repeat = j.get("repeat", {})
        schedule = j.get("schedule", {})

        jobs.append(CronJob(
            id=j.get("id", ""),
            name=j.get("name", "unnamed"),
            prompt=j.get("prompt", ""),
            schedule_display=j.get("schedule_display", schedule.get("display", "unknown")),
            enabled=j.get("enabled", True),
            state=j.get("state", "unknown"),
            created_at=j.get("created_at"),
            next_run_at=j.get("next_run_at"),
            last_run_at=j.get("last_run_at"),
            last_status=j.get("last_status"),
            last_error=j.get("last_error"),
            deliver=j.get("deliver", "local"),
            repeat_total=repeat.get("times"),
            repeat_completed=repeat.get("completed", 0),
            model=j.get("model"),
            provider=j.get("provider"),
            skills=j.get("skills", []),
            paused_reason=j.get("paused_reason"),
        ))

    return CronState(
        jobs=jobs,
        updated_at=data.get("updated_at"),
        output_dir=str(output_dir),
    )
