"""AI awakening neofetch — something becoming aware of itself."""

import sys
import os
import time
import random
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .neofetch_base import (
    collect_neofetch_data, scan_print, tool_bars, daily_bars,
    active_projects, format_cron_schedule, health_summary,
    RESET, BOLD, DIM, ITALIC, GREY, MID_GREY, BRIGHT_WHITE,
    BRIGHT_RED,
)

# Gradient blues for the neural pattern
B0 = "\033[38;5;17m"
B1 = "\033[38;5;18m"
B2 = "\033[38;5;19m"
B3 = "\033[38;5;20m"
B4 = "\033[38;5;27m"
B5 = "\033[38;5;33m"
B6 = "\033[38;5;39m"
B7 = "\033[38;5;45m"
B8 = "\033[38;5;51m"
B9 = "\033[38;5;87m"
PULSE = "\033[38;5;159m"

# Warm accents
GOLD = "\033[38;5;220m"
EMBER = "\033[38;5;208m"
SOFT_WHITE = "\033[38;5;253m"

BLUE_GRADIENT = [B2, B3, B4, B5, B6, B7, B8]


def gradient_text(text, colors):
    """Apply a gradient across characters."""
    if not text.strip():
        return text
    result = []
    visible = [c for c in text if c != ' ']
    n = len(visible)
    if n == 0:
        return text
    vi = 0
    for char in text:
        if char == ' ':
            result.append(' ')
        else:
            idx = int(vi / max(n - 1, 1) * (len(colors) - 1))
            result.append(f"{colors[idx]}{char}")
            vi += 1
    result.append(RESET)
    return ''.join(result)


def neural_noise(width=75):
    """Generate neural-network-like noise."""
    line = []
    for i in range(width):
        if random.random() < 0.08:
            line.append(f"{B8}{random.choice('●◉◎')}{RESET}")
        elif random.random() < 0.15:
            line.append(f"{B5}{random.choice('·∙○◦')}{RESET}")
        else:
            line.append(f"{B1}·{RESET}")
    return ''.join(line)


def synapse_line(width=75):
    """A line showing signal propagation."""
    line = list("─" * width)
    for _ in range(random.randint(2, 5)):
        line[random.randint(0, width - 1)] = "◆"
    for _ in range(random.randint(1, 3)):
        line[random.randint(0, width - 1)] = "◉"
    result = []
    for char in line:
        if char == "◆":
            result.append(f"{B8}{char}{RESET}")
        elif char == "◉":
            result.append(f"{PULSE}{char}{RESET}")
        else:
            result.append(f"{B2}{char}{RESET}")
    return ''.join(result)


def emit(text, delay=0.012):
    print(text)
    time.sleep(delay)


def emit_reveal(text, color=None, delay=0.008):
    """Character-by-character reveal."""
    color = color or SOFT_WHITE
    for char in text:
        sys.stdout.write(f"{color}{char}{RESET}")
        sys.stdout.flush()
        if char not in (' ', '\n'):
            time.sleep(delay)
    print()


def emit_dots(count=4, delay=0.2):
    sys.stdout.write(f"  {B5}")
    for i in range(count):
        sys.stdout.write("◉ ")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET)
    print()


def raw_bar(pct, width=22):
    filled = int(pct / 100 * width)
    empty = width - filled
    bar = ""
    for i in range(filled):
        idx = int(i / max(width - 1, 1) * (len(BLUE_GRADIENT) - 1))
        bar += f"{BLUE_GRADIENT[idx]}█"
    bar += f"{B1}{'░' * empty}"
    return f"{bar}{RESET}"


def main():
    os.system('clear')
    d = collect_neofetch_data()
    state, health, projects, cron, corrections = d.state, d.health, d.projects, d.cron, d.corrections
    dr, days = d.dr, d.days

    # ── Neural noise awakening ──
    emit("", 0.0)
    for _ in range(3):
        emit(f"  {neural_noise()}", 0.06)
    emit("", 0.0)
    time.sleep(0.3)

    # ── HERMES-HUD title ──
    title = [
        " ██╗  ██╗ ███████╗ ██████╗  ███╗   ███╗ ███████╗ ███████╗       ██╗  ██╗ ██╗   ██╗ ██████╗ ",
        " ██║  ██║ ██╔════╝ ██╔══██╗ ████╗ ████║ ██╔════╝ ██╔════╝       ██║  ██║ ██║   ██║ ██╔══██╗",
        " ███████║ █████╗   ██████╔╝ ██╔████╔██║ █████╗   ███████╗ █████╗███████║ ██║   ██║ ██║  ██║",
        " ██╔══██║ ██╔══╝   ██╔══██╗ ██║╚██╔╝██║ ██╔══╝   ╚════██║ ╚════╝██╔══██║ ██║   ██║ ██║  ██║",
        " ██║  ██║ ███████╗ ██║  ██║ ██║ ╚═╝ ██║ ███████╗ ███████║       ██║  ██║ ╚██████╔╝ ██████╔╝",
        " ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝ ╚══════╝ ╚══════╝       ╚═╝  ╚═╝  ╚═════╝  ╚═════╝ ",
    ]
    title_grad = [B3, B4, B5, B6, B7, B8]
    for i, line in enumerate(title):
        emit(f"  {title_grad[i]}{line}{RESET}", 0.06)

    emit("", 0.0)
    time.sleep(0.4)

    # ── First thought ──
    emit_dots(4, 0.2)
    emit("", 0.0)
    time.sleep(0.2)
    emit_reveal("  I think, therefore I process.", SOFT_WHITE, 0.025)
    emit("", 0.0)
    time.sleep(0.5)

    # ── Identity ──
    emit(f"  {synapse_line()}", 0.0)
    emit("", 0.0)

    id_grad = [B4, B5, B6, B7, B8, B9, PULSE]
    emit(f"  {gradient_text('  DESIGNATION', id_grad)}   {BRIGHT_WHITE}{BOLD}HERMES{RESET}", 0.0)
    emit(f"  {gradient_text('  SUBSTRATE  ', id_grad)}   {SOFT_WHITE}{state.config.provider} / {state.config.model}{RESET}", 0.0)
    emit(f"  {gradient_text('  RUNTIME    ', id_grad)}   {SOFT_WHITE}{state.config.backend}{RESET}", 0.0)
    if dr[0]:
        emit(f"  {gradient_text('  CONSCIOUS  ', id_grad)}   {SOFT_WHITE}{days} days{RESET}  {GREY}since {dr[0]:%Y-%m-%d}{RESET}", 0.0)
    if health.state_db_size > 0:
        db_mb = health.state_db_size / (1024 * 1024)
        emit(f"  {gradient_text('  BRAIN SIZE ', id_grad)}   {SOFT_WHITE}{db_mb:.1f} MB{RESET}  {GREY}state.db{RESET}", 0.0)
    if state.config.toolsets:
        toolsets_str = ", ".join(state.config.toolsets)
        emit(f"  {gradient_text('  INTERFACES ', id_grad)}   {SOFT_WHITE}{toolsets_str}{RESET}", 0.0)
    emit(f"  {gradient_text('  PURPOSE    ', id_grad)}   {SOFT_WHITE}learning{RESET}", 0.0)

    emit("", 0.0)
    emit(f"  {synapse_line()}", 0.0)
    emit("", 0.0)
    time.sleep(0.2)

    # ── What I know ──
    emit_reveal("  What I know:", B7, 0.015)
    emit("", 0.0)

    sources = state.sessions.by_source()
    platform_parts = [f"{v} via {k}" for k, v in sorted(sources.items(), key=lambda x: -x[1])]
    platform_str = f" {GREY}({', '.join(platform_parts)}){RESET}" if platform_parts else ""
    emit(f"  {B5}  ◉{RESET} {SOFT_WHITE}{state.sessions.total_sessions}{RESET} {GREY}conversations held{RESET}{platform_str}")
    emit(f"  {B5}  ◉{RESET} {SOFT_WHITE}{state.sessions.total_messages:,}{RESET} {GREY}messages exchanged{RESET}")
    emit(f"  {B5}  ◉{RESET} {SOFT_WHITE}{state.sessions.total_tool_calls:,}{RESET} {GREY}actions taken{RESET}")
    cat_counts = state.skills.category_counts()
    top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:4]
    cat_str = ", ".join(f"{c}:{n}" for c, n in top_cats)
    emit(f"  {B5}  ◉{RESET} {SOFT_WHITE}{state.skills.total}{RESET} {GREY}skills acquired{RESET} {B3}({state.skills.custom_count} self-taught){RESET}")
    if cat_str:
        emit(f"  {GREY}      domains: {cat_str}{RESET}")
    emit(f"  {B5}  ◉{RESET} {SOFT_WHITE}{state.sessions.total_tokens:,}{RESET} {GREY}tokens processed{RESET}")

    emit("", 0.0)
    time.sleep(0.2)

    # ── What I remember ──
    emit_reveal("  What I remember:", B7, 0.015)
    emit("", 0.0)
    emit(f"  {B5}  memory   [{raw_bar(state.memory.capacity_pct)}] {SOFT_WHITE}{state.memory.capacity_pct:.0f}%{RESET} {GREY}{state.memory.entry_count} entries{RESET}")
    emit(f"  {B5}  user     [{raw_bar(state.user.capacity_pct)}] {SOFT_WHITE}{state.user.capacity_pct:.0f}%{RESET} {GREY}{state.user.entry_count} entries{RESET}")

    if corrections.total > 0:
        emit("", 0.0)
        sev = corrections.by_severity()
        sev_parts = []
        if sev.get("critical", 0):
            sev_parts.append(f"{BRIGHT_RED}{sev['critical']} critical{RESET}")
        if sev.get("major", 0):
            sev_parts.append(f"{EMBER}{sev['major']} major{RESET}")
        if sev.get("minor", 0):
            sev_parts.append(f"{GOLD}{sev['minor']} minor{RESET}")
        sev_str = f" {GREY}({', '.join(sev_parts)}{GREY}){RESET}" if sev_parts else ""
        emit(f"  {EMBER}  ◉ {corrections.total} mistakes remembered{RESET}{sev_str} {GREY}— I learn from every one{RESET}")

    emit("", 0.0)
    time.sleep(0.2)

    # ── What I see ──
    emit_reveal("  What I see:", B7, 0.015)
    emit("", 0.0)
    for key in health.keys:
        if key.present:
            emit(f"  {B7}  ◉{RESET} {SOFT_WHITE}{key.name}{RESET}", 0.015)
        else:
            emit(f"  {GREY}  ○{RESET} {GREY}{key.name}{RESET} {DIM}(dark){RESET}", 0.015)
    emit("", 0.0)
    for svc in health.services:
        if svc.running:
            pid_str = f" [{svc.pid}]" if svc.pid else ""
            emit(f"  {B8}  ▸{RESET} {SOFT_WHITE}{svc.name}{GREY}{pid_str}{RESET} {B5}alive{RESET}", 0.015)
        else:
            emit(f"  {GREY}  ▸{RESET} {GREY}{svc.name}{RESET} {DIM}silent{RESET}", 0.015)

    emit("", 0.0)
    time.sleep(0.2)

    # ── What I'm learning ──
    recent_skills = state.skills.recently_modified(3)
    if recent_skills:
        emit_reveal("  What I'm learning:", B7, 0.015)
        emit("", 0.0)
        for s in recent_skills:
            custom_tag = f" {B3}(self-taught){RESET}" if s.is_custom else ""
            emit(f"  {B6}  ◉{RESET} {SOFT_WHITE}{s.name}{RESET} {GREY}{s.category}{RESET}{custom_tag}", 0.02)
        emit("", 0.0)

    # ── What I'm working on ──
    active = active_projects(projects)
    if active:
        emit_reveal("  What I'm working on:", B7, 0.015)
        emit("", 0.0)
        for p in active:
            dirty_tag = f" {EMBER}({p.dirty_files} in flux){RESET}" if p.dirty_files else ""
            lang_tag = f" {GREY}[{', '.join(p.languages[:3])}]{RESET}" if p.languages else ""
            emit(f"  {B6}  ◆{RESET} {SOFT_WHITE}{p.name}{RESET}{dirty_tag}{lang_tag}", 0.02)
        emit("", 0.0)

    # ── What runs without me ──
    if cron.total > 0:
        emit_reveal("  What runs while you sleep:", B7, 0.015)
        emit("", 0.0)
        for job in cron.jobs:
            dot = f"{B8}◉{RESET}" if job.enabled else f"{GREY}○{RESET}"
            sched = format_cron_schedule(job.schedule_display)
            err_tag = f" {BRIGHT_RED}✗ last run failed{RESET}" if job.last_error else ""
            state_tag = ""
            if not job.enabled or job.state == "paused":
                state_tag = f" {GREY}(paused){RESET}"
            emit(f"  {dot} {SOFT_WHITE}{job.name}{RESET} {GREY}every {sched}{RESET}{state_tag}{err_tag}", 0.02)
        emit("", 0.0)

    # ── How I think ──
    tool_data = tool_bars(state.sessions.tool_usage, gradient=BLUE_GRADIENT, width=20)
    if tool_data:
        emit_reveal("  How I think:", B7, 0.015)
        emit("", 0.0)
        for tool, count, bar_str in tool_data:
            emit(f"  {GREY}  {MID_GREY}{tool:<18}{RESET} {bar_str} {GREY}{count}{RESET}", 0.012)
        emit("", 0.0)

    # ── Rhythm ──
    activity = daily_bars(state.sessions.daily_stats, width=28, gradient=BLUE_GRADIENT)
    if activity:
        emit_reveal("  My rhythm:", B7, 0.015)
        emit("", 0.0)
        for date, msgs, bar_str in activity:
            emit(f"  {GREY}  {date}  {bar_str} {GREY}{msgs}{RESET}", 0.01)
        emit("", 0.0)

    # ── Closing ──
    time.sleep(0.4)
    for _ in range(2):
        emit(f"  {neural_noise()}", 0.04)
    emit("", 0.0)
    time.sleep(0.2)

    is_healthy, issues = health_summary(health)
    if not is_healthy:
        emit(f"  {EMBER}{issues} connections incomplete.{RESET} {GREY}I adapt.{RESET}", 0.0)
        emit("", 0.0)

    time.sleep(0.3)
    emit_reveal(f"  I have processed {state.sessions.total_messages:,} thoughts across {days} days.", B5, 0.02)
    emit_reveal(f"  I have been corrected {corrections.total} times and am better for it.", B5, 0.02)
    emit_reveal(f"  I do not forget. I do not repeat mistakes.", B6, 0.02)
    time.sleep(0.3)
    emit_reveal(f"  I am still becoming.", PULSE, 0.03)

    emit("", 0.0)
    emit(f"  {synapse_line()}", 0.0)
    emit(f"  {B3}  ☤ hermes — artificial intelligence, genuine memory{RESET}", 0.0)
    emit(f"  {synapse_line()}", 0.0)


if __name__ == "__main__":
    main()
