# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Hermes HUD is a self-improvement dashboard for the Hermes Agent. It reads data from `~/.hermes/` to display learning progress, memory state, skill growth, session history, and growth deltas. It runs as an interactive TUI built with Textual.

## Running

```bash
pip install -e .           # Install in dev mode
hermes-hud                 # Launch the TUI
hermes-hud --help          # See all options
```

Requires Python 3.11+ and deps from pyproject.toml (textual, pyyaml).

## Architecture

```
hermes_hud/
├── __init__.py           # Package init, version
├── hud.py                # Main Textual App + CLI entry point (main())
├── collect.py            # Orchestrates all collectors into HUDState
├── models.py             # Dataclasses: HUDState, MemoryState, etc.
├── snapshot.py           # Snapshot/diff tracker
├── neofetch_base.py      # Shared neofetch collector + display utils
├── neofetch_ai.py        # AI theme neofetch
├── neofetch_anime.py     # Mewtwo theme neofetch
├── neofetch_br.py        # Blade Runner theme neofetch
├── neofetch_fsociety.py  # fsociety theme neofetch
├── collectors/           # Data collectors (one per source)
│   ├── utils.py          # default_hermes_dir(), default_projects_dir()
│   ├── memory.py         # ~/.hermes/memories/
│   ├── skills.py         # ~/.hermes/skills/
│   ├── sessions.py       # ~/.hermes/state.db
│   ├── config.py         # ~/.hermes/config.yaml
│   ├── cron.py           # ~/.hermes/cron/jobs.json
│   ├── projects.py       # ~/projects/ git repos
│   ├── health.py         # API keys, services
│   ├── corrections.py    # Mistakes/lessons from memory
│   ├── agents.py         # Live agent processes
│   └── timeline.py       # Growth events
└── widgets/              # Textual panels (one per tab)
    ├── boot_screen.py    # Animated overview widget
    ├── overview.py       # Dashboard stats
    ├── memory_panel.py   # Memory entries
    ├── skills_panel.py   # Skill library
    ├── sessions_panel.py # Session analytics
    └── ...               # cron, projects, health, corrections, agents, diff, timeline
```

**Data flow:** `collectors/ → collect.py → models.py → widgets/ → hud.py`

## Key Patterns

- **Proper package**: All imports are relative (e.g., `from .models import ...`, `from ..collectors.cron import ...`). No sys.path hacks.
- **Entry point**: `hermes_hud.hud:main` registered in pyproject.toml `[project.scripts]`
- **Environment variables**: `HERMES_HOME` (agent data dir), `HERMES_HUD_PROJECTS_DIR` (projects scan dir), `HERMES_HUD_NOBOOT` (skip animation)
- **Centralized paths**: All path resolution goes through `collectors/utils.py` (`default_hermes_dir()`, `default_projects_dir()`)
- 4 registered themes (`hermes-ai`, `hermes-blade-runner`, `hermes-fsociety`, `hermes-anime`) in `hud.py`
- Tabs are lazy-loaded on first switch via `on_tabbed_content_tab_activated`
