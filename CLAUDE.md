# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Hermes HUD is a self-improvement dashboard for the Hermes Agent. It reads data from `~/.hermes/` to display learning progress, memory state, skill growth, session history, and growth deltas. It runs as an interactive TUI built with Textual.

## Running

```bash
./hermes-hud              # Launch the TUI
```

Requires Python 3.11+ and deps from `requirements.txt` (textual, pyyaml).

## Architecture

**Data flow:** `collectors/ → collect.py → models.py → widgets/ → hud.py`

- **`collectors/`** — Each module reads a specific data source from `~/.hermes/` (memory, skills, sessions, config, cron, projects, health, corrections, agents) and returns typed dataclasses from `models.py`
- **`collect.py`** — Orchestrates all collectors into a single `HUDState` via `collect_all()`
- **`models.py`** — All dataclasses: `HUDState` (top-level), `MemoryState`, `SkillsState`, `SessionsState`, `ConfigState`, `TimelineEvent`, `HUDSnapshot`
- **`widgets/`** — Textual widget panels, each renders one section of the dashboard. `boot_screen.py` contains the animated overview shown on launch
- **`hud.py`** — Main Textual `App` subclass (`HermesHUD`). Tabs are lazy-loaded: overview renders immediately, other tabs load on first switch via `_load_data()`
- **`snapshot.py`** — Takes snapshots to `~/.hermes-hud/snapshots.jsonl` for tracking growth over time
- **`neofetch_*.py`** — Themed boot screen displays using ANSI escape codes for the overview tab

## Key Patterns

- The TUI has 4 registered themes (`hermes-ai`, `hermes-blade-runner`, `hermes-fsociety`, `hermes-anime`) defined in `hud.py`
- `HERMES_HUD_NOBOOT` env var disables the boot animation
- Snapshots are JSONL format; `diff_report()` in `snapshot.py` compares two snapshots
- Collectors return dataclasses or plain dicts; the cron/projects/health/corrections/agents collectors are used directly by their panels without going through `HUDState`
