# Changelog

All notable changes to Hermes HUD are documented here.

---

## [0.4.0] — 2026-04-05

### tmux Operator View

Agents running inside tmux were invisible to the HUD — you knew a process was alive but had no idea which pane it lived in or whether it needed your attention. The Agents tab now functions as a live operator panel for Ghostty + tmux workflows.

**What's new:**

- **Pane discovery** — detects all tmux panes across sessions with session/window/pane identity
- **Process mapping** — matches live agent processes to panes via TTY (one batch `ps` call for all PIDs)
- **Jump hints** — each live agent line shows `→ session:window.pane` when matched
- **Operator queue** — scans matched pane output for approval prompts, questions, errors, and stuck states; surfaces them in a color-coded queue at the top of the Agents tab
- **Pane preview section** — unmatched panes running non-shell commands shown with coordinates
- **macOS support** — `_get_process_info` now dispatches by platform; macOS variant uses `ps` + `lsof` instead of `/proc`
- **Graceful fallback** — all tmux code degrades silently when tmux is not installed or no server is running
- **Parallel capture** — pane preview reads run concurrently via `ThreadPoolExecutor`

**Files changed:**
- `hermes_hud/collectors/agents.py` — `TmuxPane`, `OperatorAlert` dataclasses; `matched_pane_count`, `unmatched_interesting_panes`, `has_tmux` on `AgentsState`; 10 new helper functions
- `hermes_hud/widgets/agents_panel.py` — operator queue section, jump hints, unmatched panes section
- `tests/test_tmux.py` — 45 new tests (tmux parsing, TTY matching, alert detection, macOS etime)
- `tests/test_collectors.py` — assertions for new `AgentsState` fields

**Test count:** 142 (was 97)

---

## [0.3.0] — 2026-04-04

### Profiles Tab

Hermes supports multiple agent profiles — isolated instances with their own model, memory, skills, and gateway. Until now there was no way to see them side by side. The new Profiles tab (press `8`) shows every profile on your system with full stats.

**Per-profile data:**
- Model, provider, backend URL, port, context length
- Session count, message count, tool calls, token usage (input/output/total)
- Last active timestamp
- Memory and user profile capacity bars with entry counts
- Skill count, cron job count
- Toolsets enabled
- SOUL.md personality summary (first line)
- Compression config (model + enabled status)
- API key names from `.env` (names only, never values)
- Gateway status (systemd service check)
- Server status (health endpoint check for local llama-server)
- CLI alias detection (`~/.local/bin/<name>`)
- Local vs API classification

**Files added:**
- `hermes_hud/collectors/profiles.py` — scans `~/.hermes/` (default profile) and `~/.hermes/profiles/*/` (custom profiles)
- `hermes_hud/widgets/profiles_panel.py` — card-style Rich markup display with capacity bars and status dots
- `tests/test_profiles.py` — 18 tests against fake profile fixtures

**Also:**
- `ProfileInfo` and `ProfilesState` dataclasses in `models.py`
- Tab 8 wired into `hud.py` with CSS, keybinding, and lazy-load
- Fake "social" profile added to test fixtures in `conftest.py`
- Import checks updated for new modules
- 97 tests pass (was 79)

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
- Setup docs now explicitly call out creating the venv with Python 3.11+ on systems where `python3` is still 3.10
- Contributing docs now use the installed `hermes-hud` command instead of a nonexistent `./hermes-hud` script
- `pyfiglet` moved to optional `[neofetch]` extra
- Updated CLAUDE.md for the new package structure

**Snapshot storage**
- Fixed snapshot save/load path handling so tests and alternate snapshot directories resolve the current target file correctly

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
python3.11 -m venv venv
source venv/bin/activate
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
