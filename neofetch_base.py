#!/usr/bin/env python3.11
"""Shared utilities for all neofetch variants."""

import sys
import os
import time
import random
import re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collect import collect_all
from collectors.health import collect_health
from collectors.projects import collect_projects
from collectors.cron import collect_cron
from collectors.corrections import collect_corrections

# ── Shared ANSI constants ──

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
WHITE = "\033[37m"
BRIGHT_WHITE = "\033[97m"
GREY = "\033[38;5;240m"
MID_GREY = "\033[38;5;245m"
LIGHT_GREY = "\033[38;5;250m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
CYAN = "\033[36m"
BRIGHT_CYAN = "\033[96m"
BLUE = "\033[34m"
BRIGHT_BLUE = "\033[94m"
MAGENTA = "\033[35m"
BRIGHT_MAGENTA = "\033[95m"


# ── Data collection ──

@dataclass
class NeofetchData:
    state: object
    health: object
    projects: object
    cron: object
    corrections: object
    days: int = 0
    dr: tuple = (None, None)


def collect_neofetch_data() -> NeofetchData:
    """Collect all data needed by neofetch variants."""
    state = collect_all()
    health = collect_health()
    projects = collect_projects()
    cron = collect_cron()
    corrections = collect_corrections()
    dr = state.sessions.date_range
    days = (dr[1] - dr[0]).days + 1 if dr[0] else 0
    return NeofetchData(state=state, health=health, projects=projects,
                        cron=cron, corrections=corrections, days=days, dr=dr)


# ── Shared helper functions ──

def type_print(text, delay=0.005, jitter=0.005):
    """Print character by character with optional jitter."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if char not in (' ', '\n', '\033', '[', ';', 'm') and not char.isdigit():
            time.sleep(delay + random.uniform(0, jitter))
    print()


def scan_print(text, delay=0.012):
    """Print line with brief pause."""
    print(text)
    time.sleep(delay)


def gradient_bar(pct, width=20, gradient=None, fill="▓", empty="░"):
    """Render a gradient progress bar."""
    filled = int(pct / 100 * width)
    empty_count = width - filled
    if gradient is None:
        gradient = [GREY]
    bar = ""
    for i in range(filled):
        idx = int(i / max(width - 1, 1) * (len(gradient) - 1))
        bar += f"{gradient[idx]}{fill}"
    bar += f"{GREY}{empty * empty_count}{RESET}"
    return bar


def color_bar(pct, width=20, colors=None, fill="█", empty="░"):
    """Render a single-color progress bar based on percentage thresholds."""
    filled = int(pct / 100 * width)
    empty_count = width - filled
    if colors is None:
        colors = {0: GREEN, 75: YELLOW, 95: RED}
    color = GREEN
    for threshold in sorted(colors.keys()):
        if pct >= threshold:
            color = colors[threshold]
    return f"{color}{fill * filled}{GREY}{empty * empty_count}{RESET}"


def tool_bars(tool_usage, n=5, width=18, gradient=None, fill="▓"):
    """Return (tool, count, bar_str) tuples for top N tools."""
    top = sorted(tool_usage.items(), key=lambda x: -x[1])[:n]
    if not top:
        return []
    max_val = top[0][1]
    result = []
    for tool, count in top:
        bar_len = int(count / max_val * width)
        if gradient and len(gradient) > 1:
            bar = ""
            for j in range(bar_len):
                idx = int(j / max(bar_len - 1, 1) * (len(gradient) - 1))
                bar += f"{gradient[idx]}{fill}"
            bar += RESET
        else:
            color = gradient[0] if gradient else GREY
            bar = f"{color}{fill * bar_len}{RESET}"
        result.append((tool, count, bar))
    return result


def daily_bars(daily_stats, width=28, gradient=None, fill="▓"):
    """Return (date, messages, bar_str) tuples for daily activity."""
    if not daily_stats:
        return []
    max_msgs = max(d.messages for d in daily_stats)
    result = []
    for ds in daily_stats:
        bar_len = int(ds.messages / max(max_msgs, 1) * width)
        if gradient and len(gradient) > 1:
            bar = ""
            for j in range(bar_len):
                idx = int(j / max(bar_len - 1, 1) * (len(gradient) - 1))
                bar += f"{gradient[idx]}{fill}"
            bar += RESET
        else:
            # Single color based on intensity
            color = gradient[0] if gradient else GREY
            bar = f"{color}{fill * bar_len}{RESET}"
        result.append((ds.date, ds.messages, bar))
    return result


def active_projects(projects_data):
    """Return active git projects."""
    return [p for p in projects_data.projects if p.is_git and p.activity_level == "active"]


def format_cron_schedule(schedule_display):
    """Clean up cron schedule display strings."""
    sched = schedule_display
    if sched.startswith("every "):
        sched = sched[6:]
    m = re.match(r'^(\d+)m$', sched)
    if m:
        mins = int(m.group(1))
        if mins >= 60 and mins % 60 == 0:
            sched = f"{mins // 60}h"
    return sched


def health_summary(health_data):
    """Return (is_healthy, issue_count)."""
    issues = health_data.keys_missing + sum(1 for s in health_data.services if not s.running)
    return health_data.all_healthy, issues
