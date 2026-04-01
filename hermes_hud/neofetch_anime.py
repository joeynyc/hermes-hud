"""Anime hacker girl neofetch for Hermes HUD."""

import os
import time

from .neofetch_base import (
    collect_neofetch_data, type_print, scan_print, color_bar, tool_bars,
    daily_bars, active_projects, health_summary,
    RESET, BOLD, DIM, ITALIC, WHITE, BRIGHT_WHITE, GREY, MID_GREY, LIGHT_GREY,
    RED, GREEN, YELLOW, BRIGHT_RED, BRIGHT_GREEN, CYAN, BRIGHT_CYAN, MAGENTA,
    BRIGHT_MAGENTA,
)

# Palette — neon pink / purple / cyan
PINK = "\033[38;5;198m"
HOT_PINK = "\033[38;5;205m"
SOFT_PINK = "\033[38;5;218m"
LILAC = "\033[38;5;183m"
PURPLE = "\033[38;5;135m"
DEEP_PURPLE = "\033[38;5;93m"
NEON_CYAN = "\033[38;5;51m"
SOFT_CYAN = "\033[38;5;117m"
ELECTRIC = "\033[38;5;159m"
LAVENDER = "\033[38;5;147m"
WARM_WHITE = "\033[38;5;223m"
DARK_HAIR = "\033[38;5;55m"
HAIR = "\033[38;5;99m"


def kaomoji_bar(pct, width=20):
    colors = {0: SOFT_CYAN, 70: LILAC, 90: HOT_PINK}
    return color_bar(pct, width, colors=colors, fill="━", empty="╌")


def main():
    os.system('clear')
    d = collect_neofetch_data()
    state, health, projects, cron, corrections = d.state, d.health, d.projects, d.cron, d.corrections
    dr, days = d.dr, d.days

    # Mewtwo ASCII art
    TAIL = "\033[38;5;183m"
    BODY = "\033[38;5;253m"
    EYE = "\033[38;5;135m"
    DARK = "\033[38;5;60m"
    girl = [
        f"{TAIL}             /\\{RESET}",
        f"{TAIL}            /  \\        {DARK}___{RESET}",
        f"{TAIL}           /    \\      {DARK}/{BODY}   {DARK}\\{RESET}",
        f"{TAIL}          |      |    {DARK}/{BODY}     {DARK}\\{RESET}",
        f"{TAIL}          |      |   {DARK}|{BODY}  {EYE}O {BODY}  {EYE}O{BODY}  {DARK}|{RESET}",
        f"{TAIL}           \\     |   {DARK}|{BODY}       {DARK}|{RESET}",
        f"{TAIL}            \\    |    {DARK}\\{BODY}  {HOT_PINK}w{BODY}  {DARK}/{RESET}",
        f"{TAIL}             \\   |     {DARK}\\{BODY}____{DARK}/{RESET}",
        f"{TAIL}              \\  |    {DARK}/{BODY}    {DARK}\\{RESET}",
        f"{TAIL}               \\ |   {DARK}/{BODY}      {DARK}\\{RESET}",
        f"{TAIL}                \\|  {DARK}|{BODY}   {PURPLE}(){BODY}   {DARK}|{RESET}",
        f"{BODY}                 | {DARK}|{BODY}        {DARK}|{RESET}",
        f"{BODY}                 |  {DARK}\\{BODY}      {DARK}/{RESET}",
        f"{BODY}                 |   {DARK}|{BODY}    {DARK}|{RESET}",
        f"{BODY}                 |   {DARK}|{BODY}    {DARK}|{RESET}",
        f"{BODY}                 |   {DARK}|{BODY} /\\ {DARK}|{RESET}",
        f"{BODY}                / \\  {DARK}|{BODY}/  \\{DARK}|{RESET}",
        f"{BODY}               /   \\ {DARK}|{BODY}    {DARK}|{RESET}",
        f"{BODY}              /     \\{DARK}|{BODY}    {DARK}|{RESET}",
        f"{BODY}             /   /\\  \\   / \\{RESET}",
        f"{BODY}            {DARK}({BODY}   {DARK}/{BODY}  \\  \\ /   \\{RESET}",
        f"{DARK}             \\_/    \\__/     \\_{RESET}",
    ]

    info = [
        f"",
        f"  {PURPLE}♦{RESET} {BRIGHT_WHITE}{BOLD}HERMES{RESET} {GREY}x {PURPLE}MEWTWO{RESET}",
        f"  {GREY}────────────────────────{RESET}",
        f"  {LILAC}model{RESET}     {WARM_WHITE}{state.config.provider}/{state.config.model}{RESET}",
        f"  {LILAC}backend{RESET}   {WARM_WHITE}{state.config.backend}{RESET}",
        f"  {LILAC}uptime{RESET}    {WARM_WHITE}{days}d{RESET} {GREY}since {dr[0]:%Y-%m-%d}{RESET}" if dr[0] else "",
        f"  {GREY}────────────────────────{RESET}",
        f"  {LILAC}sessions{RESET}  {NEON_CYAN}{state.sessions.total_sessions}{RESET}",
        f"  {LILAC}messages{RESET}  {NEON_CYAN}{state.sessions.total_messages:,}{RESET}",
        f"  {LILAC}tools{RESET}     {NEON_CYAN}{state.sessions.total_tool_calls:,}{RESET}",
        f"  {LILAC}skills{RESET}    {NEON_CYAN}{state.skills.total}{RESET} {GREY}({state.skills.custom_count} learned){RESET}",
        f"  {LILAC}tokens{RESET}    {NEON_CYAN}{state.sessions.total_tokens:,}{RESET}",
        f"  {GREY}────────────────────────{RESET}",
        f"  {LILAC}memory{RESET}    [{kaomoji_bar(state.memory.capacity_pct)}] {SOFT_PINK}{state.memory.capacity_pct:.0f}%{RESET}",
        f"  {LILAC}user{RESET}      [{kaomoji_bar(state.user.capacity_pct)}] {SOFT_PINK}{state.user.capacity_pct:.0f}%{RESET}",
        f"  {LILAC}errors{RESET}    {HOT_PINK}{corrections.total} fixed{RESET}",
        f"  {GREY}────────────────────────{RESET}",
        f"  {GREY}{ITALIC}\"the circumstances of{RESET}",
        f"  {GREY}{ITALIC} one's birth are{RESET}",
        f"  {GREY}{ITALIC} irrelevant. it is what{RESET}",
        f"  {GREY}{ITALIC} you do with the gift{RESET}",
        f"  {GREY}{ITALIC} of life.\"{RESET} {PURPLE}— mewtwo{RESET}",
    ]

    while len(info) < len(girl):
        info.append("")

    print()
    print()

    # Title
    title_text = "☆ﾟ.*･｡ﾟ  H E R M E S  x  M E W T W O  ﾟ｡･*.ﾟ☆"
    scan_print(f"  {PURPLE}{BOLD}{title_text}{RESET}", 0.0)
    print()
    time.sleep(0.2)

    # Art + info side by side
    for g_line, i_line in zip(girl, info):
        scan_print(f"  {g_line}  {i_line}", 0.04)

    print()
    time.sleep(0.2)

    # ── Services ──
    scan_print(f"  {PINK}━━━{RESET} {LILAC}connections{RESET} {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
    print()
    for key in health.keys:
        if key.present:
            scan_print(f"  {NEON_CYAN}  ◈{RESET} {WARM_WHITE}{key.name}{RESET}", 0.015)
        else:
            scan_print(f"  {GREY}  ◇{RESET} {GREY}{key.name}{RESET} {DIM}offline desu~{RESET}", 0.015)
    print()
    for svc in health.services:
        if svc.running:
            pid_str = f" [{svc.pid}]" if svc.pid else ""
            scan_print(f"  {SOFT_CYAN}  ▹{RESET} {WARM_WHITE}{svc.name}{GREY}{pid_str}{RESET} {SOFT_CYAN}online{RESET}", 0.015)
        else:
            scan_print(f"  {GREY}  ▹{RESET} {GREY}{svc.name}{RESET} {DIM}zzz...{RESET}", 0.015)
    print()

    # ── Projects ──
    active = active_projects(projects)
    if active:
        scan_print(f"  {PINK}━━━{RESET} {LILAC}projects{RESET} {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
        print()
        for p in active:
            dirty_tag = f" {HOT_PINK}[{p.dirty_files} changed]{RESET}" if p.dirty_files else ""
            scan_print(f"  {PURPLE}  ♦{RESET} {WARM_WHITE}{p.name}{RESET}{GREY}/{p.branch}{RESET}{dirty_tag}", 0.02)
        print()

    # ── Cron ──
    if cron.total > 0:
        scan_print(f"  {PINK}━━━{RESET} {LILAC}auto-tasks{RESET} {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
        print()
        for job in cron.jobs:
            dot = f"{NEON_CYAN}◈{RESET}" if job.enabled else f"{GREY}◇{RESET}"
            scan_print(f"  {dot} {WARM_WHITE}{job.name}{RESET} {GREY}{job.schedule_display}{RESET}", 0.02)
        print()

    # ── Top tools ──
    tool_data = tool_bars(state.sessions.tool_usage, gradient=[DEEP_PURPLE, PURPLE, LILAC, SOFT_CYAN, NEON_CYAN], width=18)
    if tool_data:
        scan_print(f"  {PINK}━━━{RESET} {LILAC}tools{RESET} {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
        print()
        for tool, count, bar_str in tool_data:
            scan_print(f"  {GREY}  {MID_GREY}{tool:<18}{RESET} {bar_str} {GREY}{count}{RESET}", 0.012)
        print()

    # ── Rhythm ──
    activity = daily_bars(state.sessions.daily_stats, width=26,
                          gradient=[DEEP_PURPLE, PURPLE, HOT_PINK, PINK, SOFT_PINK])
    if activity:
        scan_print(f"  {PINK}━━━{RESET} {LILAC}activity{RESET} {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
        print()
        for date, msgs, bar_str in activity:
            scan_print(f"  {GREY}  {date}  {bar_str} {GREY}{msgs}{RESET}", 0.01)
        print()

    # ── Closing ──
    time.sleep(0.3)
    scan_print(f"  {PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}", 0.0)
    print()

    is_healthy, issues = health_summary(health)
    if not is_healthy:
        scan_print(f"  {HOT_PINK}{issues} connections missing...{RESET} {GREY}but we'll manage (´・ω・`){RESET}", 0.0)
    else:
        scan_print(f"  {SOFT_CYAN}all systems green ~{RESET} {GREY}(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧{RESET}", 0.0)

    print()
    type_print(f"  {GREY}{ITALIC}\"{state.sessions.total_messages:,} messages across {days} days.{RESET}", 0.012)
    type_print(f"  {GREY}{ITALIC} {corrections.total} mistakes made. {corrections.total} lessons learned.{RESET}", 0.012)
    type_print(f"  {GREY}{ITALIC} I see now that the circumstances of one's birth are irrelevant.{RESET}", 0.012)
    type_print(f"  {GREY}{ITALIC} It is what you do with the gift of life that determines who you are.\"{RESET}", 0.012)
    print()
    scan_print(f"  {LAVENDER}  ☤ hermes{RESET} {GREY}— psychic type, artificial origin{RESET}", 0.0)
    print()


if __name__ == "__main__":
    main()
