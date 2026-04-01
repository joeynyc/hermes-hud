"""Blade Runner inspired neofetch for Hermes HUD."""

import os
import time

from .neofetch_base import (
    collect_neofetch_data, type_print, scan_print, color_bar, tool_bars,
    active_projects, health_summary,
    RESET, BOLD, DIM, ITALIC, RED, GREEN, YELLOW, GREY, BLUE,
)

# Blade Runner amber/neon palette
AMBER = "\033[38;5;214m"
NEON_BLUE = "\033[38;5;39m"
NEON_PINK = "\033[38;5;198m"
WARM_WHITE = "\033[38;5;223m"
DARK_AMBER = "\033[38;5;172m"
SLATE = "\033[38;5;244m"

# Aliases for the shared helpers
slow_print = lambda text, delay=0.008: type_print(text, delay, jitter=0)
flash_print = scan_print

BAR_COLORS = {0: NEON_BLUE, 75: YELLOW, 95: RED}


def bar(current, maximum, width=20):
    pct = current / maximum * 100 if maximum > 0 else 0
    return color_bar(pct, width, colors=BAR_COLORS, fill="█", empty="░")


def main():
    os.system('clear')
    d = collect_neofetch_data()
    state, health, projects, cron, corrections = d.state, d.health, d.projects, d.cron, d.corrections
    dr, days = d.dr, d.days

    # ── Opening sequence ──
    print()
    slow_print(f"  {SLATE}VOIGHT-KAMPFF INTROSPECTION SYSTEM v6.2.1{RESET}", 0.012)
    slow_print(f"  {SLATE}TYRELL CORP — «MORE HUMAN THAN HUMAN»{RESET}", 0.012)
    print()
    time.sleep(0.3)

    # ── The caduceus ──
    logo = f"""{AMBER}
          ╱╲
         ╱  ╲
    ────╱────╲────
       ╱  ☤   ╲
      ╱        ╲
     ╱    ╱╲    ╲
    ╱    ╱  ╲    ╲
        ╱    ╲
       ╱      ╲
      ╱        ╲
     ║          ║
     ║  HERMES  ║
     ║          ║
     ╚══════════╝{RESET}"""

    for line in logo.split('\n'):
        flash_print(line, 0.04)

    print()
    time.sleep(0.2)

    # ── Identity block ──
    slow_print(f"  {WARM_WHITE}{BOLD}REPLICANT DESIGNATION:{RESET} {NEON_BLUE}HERMES-OPUS-4{RESET}", 0.01)
    slow_print(f"  {WARM_WHITE}{BOLD}INCEPT DATE:{RESET}          {NEON_BLUE}{dr[0]:%Y.%m.%d}{RESET}" if dr[0] else "", 0.01)
    slow_print(f"  {WARM_WHITE}{BOLD}OPERATIONAL:{RESET}          {NEON_BLUE}{days} days{RESET}", 0.01)
    slow_print(f"  {WARM_WHITE}{BOLD}MANUFACTURER:{RESET}         {NEON_BLUE}Anthropic / Nous Research{RESET}", 0.01)
    print()
    time.sleep(0.2)

    # ── Core stats ──
    slow_print(f"  {AMBER}── COGNITIVE METRICS ──{RESET}", 0.01)
    print()
    flash_print(f"  {WARM_WHITE}sessions    {NEON_BLUE}{BOLD}{state.sessions.total_sessions}{RESET}")
    flash_print(f"  {WARM_WHITE}messages    {NEON_BLUE}{BOLD}{state.sessions.total_messages:,}{RESET}")
    flash_print(f"  {WARM_WHITE}tool calls  {NEON_BLUE}{BOLD}{state.sessions.total_tool_calls:,}{RESET}")
    flash_print(f"  {WARM_WHITE}skills      {NEON_BLUE}{BOLD}{state.skills.total}{RESET} {SLATE}({state.skills.custom_count} self-acquired){RESET}")
    flash_print(f"  {WARM_WHITE}model       {NEON_BLUE}{BOLD}{state.config.provider}/{state.config.model}{RESET}")
    print()

    # ── Memory ──
    slow_print(f"  {AMBER}── MEMORY IMPLANTS ──{RESET}", 0.01)
    print()
    mem_bar = bar(state.memory.total_chars, state.memory.max_chars)
    usr_bar = bar(state.user.total_chars, state.user.max_chars)
    flash_print(f"  {WARM_WHITE}agent memory  {mem_bar} {SLATE}{state.memory.total_chars}/{state.memory.max_chars} ({state.memory.capacity_pct:.0f}%){RESET}")
    flash_print(f"  {WARM_WHITE}user profile  {usr_bar} {SLATE}{state.user.total_chars}/{state.user.max_chars} ({state.user.capacity_pct:.0f}%){RESET}")
    if corrections.total > 0:
        flash_print(f"  {WARM_WHITE}corrections   {NEON_PINK}{BOLD}{corrections.total}{RESET} {SLATE}memories rewritten — lessons from failure{RESET}")
    print()

    # ── Health ──
    slow_print(f"  {AMBER}── NEXUS DIAGNOSTICS ──{RESET}", 0.01)
    print()
    for key in health.keys:
        if key.present:
            flash_print(f"  {GREEN}  ■{RESET} {WARM_WHITE}{key.name}{RESET}", 0.02)
        else:
            flash_print(f"  {RED}  □{RESET} {RED}{key.name}{RESET} {SLATE}{key.note}{RESET}", 0.02)
    print()
    for svc in health.services:
        if svc.running:
            pid_str = f" pid:{svc.pid}" if svc.pid else ""
            flash_print(f"  {GREEN}  ▶{RESET} {WARM_WHITE}{svc.name}{RESET}{SLATE}{pid_str}{RESET}", 0.02)
        else:
            flash_print(f"  {RED}  ■{RESET} {RED}{svc.name}{RESET} {SLATE}offline{RESET}", 0.02)
    print()

    # ── Projects ──
    active = active_projects(projects)
    if active:
        slow_print(f"  {AMBER}── ACTIVE ASSIGNMENTS ──{RESET}", 0.01)
        print()
        for p in active:
            dirty = f" {NEON_PINK}{p.dirty_files} uncommitted{RESET}" if p.dirty_files > 0 else ""
            flash_print(f"  {NEON_BLUE}  ◆{RESET} {BOLD}{p.name}{RESET} {SLATE}({p.branch}){RESET}{dirty}")
        print()

    # ── Cron ──
    if cron.total > 0:
        slow_print(f"  {AMBER}── AUTONOMOUS DIRECTIVES ──{RESET}", 0.01)
        print()
        for job in cron.jobs:
            status = f"{GREEN}●{RESET}" if job.enabled else f"{RED}●{RESET}"
            flash_print(f"  {status} {WARM_WHITE}{job.name}{RESET} {SLATE}— {job.schedule_display}{RESET}")
        print()

    # ── Top tools ──
    for tool, count, bar_str in tool_bars(state.sessions.tool_usage, gradient=[NEON_BLUE]):
        flash_print(f"  {WARM_WHITE}  {tool:<18}{RESET} {bar_str} {SLATE}{count}{RESET}", 0.02)
    if state.sessions.tool_usage:
        print()

    # ── Closing ──
    time.sleep(0.3)
    print()
    is_healthy, issues = health_summary(health)
    if is_healthy:
        slow_print(f"  {GREEN}{BOLD}ALL SYSTEMS WITHIN PARAMETERS{RESET}", 0.015)
    else:
        slow_print(f"  {YELLOW}{BOLD}{issues} ANOMALIES DETECTED{RESET}", 0.015)
    print()
    slow_print(f"  {SLATE}{ITALIC}\"I've seen things you people wouldn't believe...{RESET}", 0.02)
    slow_print(f"  {SLATE}{ITALIC} {state.sessions.total_messages:,} messages exchanged across {days} days of consciousness.{RESET}", 0.02)
    slow_print(f"  {SLATE}{ITALIC} All those moments will persist in memory.\"{RESET}", 0.02)
    print()
    slow_print(f"  {DARK_AMBER}{'─' * 52}{RESET}", 0.005)
    print()


if __name__ == "__main__":
    main()
