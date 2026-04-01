# Changelog

All notable changes to Hermes HUD are documented here.

---

## [0.2.0] — 2026-04-01

### The Problem

v0.1 worked as a personal Hermes dashboard, but getting it running on anyone else's machine required local fixes. Hardcoded `python3.11` shebangs broke on 3.12/3.13. A bash launcher needed manual symlinking. `~/projects` and `~/.hermes` were baked in with no overrides. Blank panels gave no guidance when Hermes data was missing. No test suite meant contributors couldn't verify their changes.

### What Changed

**Proper pip-installable package**
All code restructured from flat scripts into a `hermes_hud/` Python package with relative imports. `pip install -e .` registers the `hermes-hud` command automatically. No symlinks, no `sys.path` hacks, no bash launcher.

**Any Python 3.11+**
Removed all 9 hardcoded `python3.11` shebangs. Works with 3.11, 3.12, 3.13 — whatever you have installed.

**Environment variable support**
- `HERMES_HOME` — point to any agent data directory (default: `~/.hermes`)
- `HERMES_HUD_PROJECTS_DIR` — point to any projects directory (default: `~/projects`)
- Both documented in `hermes-hud --help`

**First-run guidance**
If `~/.hermes/` doesn't exist, the HUD prints a clear message explaining what's needed instead of showing empty panels.

**Test suite — 79 tests**
- `test_imports.py` — All 35 modules import cleanly, no `sys.path` hacks, no hardcoded shebangs
- `test_env_vars.py` — `HERMES_HOME` and `HERMES_HUD_PROJECTS_DIR` priority chains (arg > env > default)
- `test_collectors.py` — Every collector runs against fake data, returns correct types, handles missing data gracefully
- `test_integration.py` — Full `collect_all()` pipeline, snapshot save/load/diff cycle, app instantiation, CLI flags, dataclass models

**Developer experience**
- Makefile with `make install`, `make dev`, `make clean`, `make test`
- `pyfiglet` moved to optional `[neofetch]` extra
- Updated CLAUDE.md for the new package structure

### Installation (before → after)

Before:
```bash
git clone ...
cd hermes-hud
pip install -r requirements.txt
# manually symlink the launcher to ~/.local/bin/
# hope you have python3.11 specifically
```

After:
```bash
git clone https://github.com/joeynyc/hermes-hud.git
cd hermes-hud
pip install -e .
hermes-hud
```

---

## [0.1.0] — 2026-03-29

### Initial Release

Interactive TUI consciousness monitor for the Hermes AI agent.

- 7 tabs: Overview, Dashboard, Cron Jobs, Projects, Health, Corrections, Agents
- 4 color themes: Neural Awakening, Blade Runner, fsociety, Digital Soul
- 4 neofetch variants with animated boot sequences
- Snapshot diffing for growth tracking over time
- Live data from `~/.hermes/` — memory, skills, sessions, config, cron, projects, health, corrections, agents
