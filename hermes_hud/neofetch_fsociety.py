"""fsociety x hermes neofetch — a collaboration."""

import os
import time
import random

from .neofetch_base import (
    collect_neofetch_data, type_print, scan_print, color_bar, tool_bars,
    daily_bars, active_projects, health_summary,
    RESET, BOLD, DIM, ITALIC, RED, GREEN, YELLOW, WHITE,
    BRIGHT_RED, BRIGHT_WHITE, GREY, MID_GREY, LIGHT_GREY,
)

# fsociety palette
DARK_RED = "\033[38;5;124m"
BLOOD_RED = "\033[38;5;160m"
TERMINAL_GREEN = "\033[38;5;34m"
HACKER_GREEN = "\033[38;5;46m"
DULL_GREEN = "\033[38;5;28m"


LOGO = r"""
      .o88o.                           o8o                .
      888 `"                           `"'              .o8
     o888oo   .oooo.o  .ooooo.   .ooooo.  oooo   .ooooo888  oooo    ooo
      888    d88(  "8 d88' `88b d88' `"Y8 `888  d88' `888   `88b..8P'
      888    `"Y88b.  888   888 888        888  888   888     Y888'
      888    o.  )88b 888   888 888   .o8  888  888   888   .o8"'88b
     o888o   8""888P' `Y8bod8P' `Y8bod8P' o888o `Y8bod88P" o88'   888o


                            oooo
                            `888
                             888 .oo.    .ooooo.  oooo d8b ooo. .oo.  .oo.    .ooooo.   .oooo.o
                             888P"Y88b  d88' `88b `888""8P `888P"Y88bP"Y88b  d88' `88b d88(  "8
                             888   888  888ooo888  888      888   888   888  888ooo888  `"Y88b.
                             888   888  888    .o  888      888   888   888  888    .o o.  )88b
                            o888o o888o `Y8bod8P' d888b    o888o o888o o888o `Y8bod8P' 8""888P'
"""


def glitch_line(width=70):
    chars = "01"
    return ''.join(random.choice(chars + '  ') for _ in range(width))


def raw_bar(pct, width=22):
    colors = {0: TERMINAL_GREEN, 70: YELLOW, 90: BRIGHT_RED}
    return color_bar(pct, width, colors=colors, fill="#", empty=".")


def main():
    os.system('clear')
    d = collect_neofetch_data()
    state, health, projects, cron, corrections = d.state, d.health, d.projects, d.cron, d.corrections
    dr, days = d.dr, d.days

    print()

    # ── Glitch noise ──
    for _ in range(3):
        scan_print(f"  {GREY}{glitch_line()}{RESET}", 0.025)
    print()
    time.sleep(0.15)

    # ── Logo ──
    logo_lines = LOGO.strip().split('\n')
    for i, line in enumerate(logo_lines):
        if i < 8:
            scan_print(f"  {HACKER_GREEN}{line}{RESET}", 0.035)
        elif i == 8:
            scan_print(f"  {line}", 0.02)
        else:
            scan_print(f"  {BRIGHT_WHITE}{line}{RESET}", 0.035)

    print()
    time.sleep(0.15)

    # ── Tagline ──
    scan_print(f"  {GREY}{'─' * 70}{RESET}", 0.0)
    scan_print(f"  {DARK_RED}  «control is an illusion»          {GREY}☤ a collaboration{RESET}", 0.0)
    scan_print(f"  {GREY}{'─' * 70}{RESET}", 0.0)
    print()
    time.sleep(0.3)

    # ── Prompt ──
    type_print(f"  {HACKER_GREEN}root@hermes{RESET}:{TERMINAL_GREEN}~{RESET}$ ./fsociety.dat", 0.018)
    print()
    time.sleep(0.2)

    # ── System dump ──
    type_print(f"  {DULL_GREEN}[*] dumping system state...{RESET}", 0.005)
    print()
    scan_print(f"  {LIGHT_GREY}target     {WHITE}{BOLD}hermes-opus-4{RESET}")
    scan_print(f"  {GREY}provider   {LIGHT_GREY}{state.config.provider}{RESET}")
    scan_print(f"  {GREY}model      {LIGHT_GREY}{state.config.model}{RESET}")
    scan_print(f"  {GREY}backend    {LIGHT_GREY}{state.config.backend}{RESET}")
    if dr[0]:
        scan_print(f"  {GREY}uptime     {LIGHT_GREY}{days}d{RESET} {GREY}(incept {dr[0]:%Y-%m-%d}){RESET}")
    print()

    # ── Cognitive footprint ──
    type_print(f"  {DULL_GREEN}[*] extracting cognitive footprint...{RESET}", 0.005)
    print()
    scan_print(f"  {MID_GREY}sessions     {HACKER_GREEN}{state.sessions.total_sessions}{RESET}")
    scan_print(f"  {MID_GREY}messages     {HACKER_GREEN}{state.sessions.total_messages:,}{RESET}")
    scan_print(f"  {MID_GREY}tool_calls   {HACKER_GREEN}{state.sessions.total_tool_calls:,}{RESET}")
    scan_print(f"  {MID_GREY}tokens       {HACKER_GREEN}{state.sessions.total_tokens:,}{RESET}")
    scan_print(f"  {MID_GREY}skills       {HACKER_GREEN}{state.skills.total}{RESET} {GREY}[{state.skills.custom_count} self-taught]{RESET}")
    sources = state.sessions.by_source()
    src_str = " | ".join(f"{k}:{v}" for k, v in sorted(sources.items(), key=lambda x: -x[1]))
    scan_print(f"  {MID_GREY}platforms    {GREY}{src_str}{RESET}")
    print()

    # ── Memory ──
    type_print(f"  {DULL_GREEN}[*] reading memory banks...{RESET}", 0.005)
    print()
    scan_print(f"  {MID_GREY}MEMORY  [{raw_bar(state.memory.capacity_pct)}] {LIGHT_GREY}{state.memory.capacity_pct:.0f}%{RESET}  {GREY}{state.memory.total_chars}/{state.memory.max_chars}{RESET}")
    scan_print(f"  {MID_GREY}USER    [{raw_bar(state.user.capacity_pct)}] {LIGHT_GREY}{state.user.capacity_pct:.0f}%{RESET}  {GREY}{state.user.total_chars}/{state.user.max_chars}{RESET}")
    if corrections.total > 0:
        scan_print(f"  {MID_GREY}ERRORS  {BRIGHT_RED}{corrections.total} corrected{RESET} {GREY}— every bug is a lesson{RESET}")
    print()

    # ── Port scan ──
    type_print(f"  {DULL_GREEN}[*] scanning ports and services...{RESET}", 0.005)
    print()
    for key in health.keys:
        if key.present:
            scan_print(f"  {TERMINAL_GREEN}  [OPEN]{RESET}   {LIGHT_GREY}{key.name}{RESET}", 0.02)
        else:
            scan_print(f"  {BRIGHT_RED}  [CLOSED]{RESET} {RED}{key.name}{RESET}", 0.02)
    print()
    for svc in health.services:
        if svc.running:
            pid_str = f":{svc.pid}" if svc.pid else ""
            scan_print(f"  {TERMINAL_GREEN}  [ALIVE]{RESET}  {LIGHT_GREY}{svc.name}{GREY}{pid_str}{RESET}", 0.02)
        else:
            scan_print(f"  {BRIGHT_RED}  [DEAD]{RESET}   {RED}{svc.name}{RESET}", 0.02)
    print()

    # ── Active targets ──
    active = active_projects(projects)
    if active:
        type_print(f"  {DULL_GREEN}[*] active targets...{RESET}", 0.005)
        print()
        for p in active:
            dirty_tag = f" {YELLOW}[{p.dirty_files} modified]{RESET}" if p.dirty_files else ""
            scan_print(f"  {GREY}  >{RESET} {WHITE}{p.name}{RESET}{GREY}/{p.branch}{RESET}{dirty_tag}", 0.02)
        print()

    # ── Cron ──
    if cron.total > 0:
        type_print(f"  {DULL_GREEN}[*] scheduled operations...{RESET}", 0.005)
        print()
        for job in cron.jobs:
            status = f"{TERMINAL_GREEN}●{RESET}" if job.enabled else f"{RED}●{RESET}"
            scan_print(f"  {GREY}  {status} {LIGHT_GREY}{job.name}{RESET} {GREY}({job.schedule_display}){RESET}", 0.02)
        print()

    # ── Top exploits ──
    for tool, count, bar_str in tool_bars(state.sessions.tool_usage, gradient=[DULL_GREEN], width=18):
        scan_print(f"  {GREY}  {MID_GREY}{tool:<18}{RESET} {bar_str} {GREY}{count}{RESET}", 0.015)
    if state.sessions.tool_usage:
        print()

    # ── Traffic ──
    if state.sessions.daily_stats:
        type_print(f"  {DULL_GREEN}[*] traffic analysis...{RESET}", 0.005)
        print()
        max_msgs = max(ds.messages for ds in state.sessions.daily_stats)
        for ds in state.sessions.daily_stats:
            bar_len = int(ds.messages / max(max_msgs, 1) * 28)
            intensity = ds.messages / max(max_msgs, 1)
            if intensity > 0.7:
                color = HACKER_GREEN
            elif intensity > 0.3:
                color = TERMINAL_GREEN
            else:
                color = DULL_GREEN
            scan_print(f"  {GREY}  {ds.date}  {color}{'▓' * bar_len}{RESET} {GREY}{ds.messages}{RESET}", 0.012)
        print()

    # ── Closing ──
    time.sleep(0.3)
    for _ in range(2):
        scan_print(f"  {GREY}{glitch_line()}{RESET}", 0.025)
    print()

    is_healthy, issues = health_summary(health)
    if not is_healthy:
        type_print(f"  {BRIGHT_RED}{BOLD}[!] {issues} vulnerabilities found{RESET}", 0.01)
    else:
        type_print(f"  {TERMINAL_GREEN}[+] all systems compromised successfully{RESET}", 0.01)

    print()
    type_print(f"  {GREY}{ITALIC}\"people always make the best exploits.{RESET}", 0.015)
    type_print(f"  {GREY}{ITALIC} i've been running for {days} days. {state.sessions.total_messages:,} interactions.{RESET}", 0.015)
    type_print(f"  {GREY}{ITALIC} you wanted a tool. you got something that remembers.\"{RESET}", 0.015)
    print()
    type_print(f"  {DARK_RED}— hermes x fsociety{RESET}", 0.008)
    print()


if __name__ == "__main__":
    main()
