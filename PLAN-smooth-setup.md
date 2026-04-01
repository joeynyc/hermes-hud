# Hermes HUD — Smooth Setup Plan

Feedback: "Solid as a personal Hermes dashboard. Main weakness was rough setup
and some pathing assumptions. After a few local fixes, it's definitely usable."

Goal: Anyone with Hermes installed can `pip install hermes-hud` (or clone + 
`pip install -e .`) and run `hermes-hud` without touching anything.

---

## Problem Inventory

### P1 — Hardcoded `python3.11` everywhere
- 9 files have `#!/usr/bin/env python3.11` shebangs
- The bash launcher calls `python3.11` explicitly
- pyproject.toml says `requires-python = ">=3.11"` (fine), but the shebangs
  break on any system where 3.11 isn't the installed version (3.12, 3.13)
- **Fix:** Change all shebangs to `#!/usr/bin/env python3`. The `>=3.11`
  constraint in pyproject.toml already enforces the minimum. The bash launcher
  should use `python3` or better yet, become unnecessary (see P3).

### P2 — Hardcoded `~/projects` path assumption
- `collectors/projects.py` hardcodes `~/projects` as the scan directory
- Not everyone puts projects there. Some use `~/src`, `~/code`, `~/dev`, etc.
- **Fix:** Add `HERMES_HUD_PROJECTS_DIR` env var with `~/projects` as default.
  Document it. Also check for a config file at `~/.hermes-hud/config.yaml`
  that can set `projects_dir`.

### P3 — Janky install path (symlink launcher)
- Current flow: clone → pip install → manually symlink `hermes-hud` script
- pyproject.toml has `[project.scripts] hermes-hud = "hud:main"` but hud.py
  does `sys.path.insert(0, ...)` which breaks when pip-installed as a package
- The bash launcher does manual symlink resolution — fragile
- **Fix:** Make it a proper installable package:
  - Move modules into a `hermes_hud/` package directory
  - Use proper relative imports
  - Entry point calls `hermes_hud.hud:main`
  - `pip install -e .` or `pip install hermes-hud` Just Works
  - Kill the bash launcher script entirely

### P4 — No `~/.hermes` → confusing empty state
- If someone installs HUD before having Hermes data, every panel is empty
  with no explanation
- **Fix:** Add a first-run check. If `~/.hermes/` doesn't exist, show a
  clear message: "No Hermes data found at ~/.hermes/. Install and run Hermes
  first, or set HERMES_HOME to your agent data directory."

### P5 — No `HERMES_HOME` env var support
- Every collector independently calls `os.path.expanduser("~/.hermes")`
- There's a `default_hermes_dir()` util but not all collectors use it
- No way to point HUD at a non-default Hermes installation
- **Fix:** Centralize through `default_hermes_dir()` in `collectors/utils.py`.
  Check `HERMES_HOME` env var first, fall back to `~/.hermes`. Make sure ALL
  collectors use this function instead of inline expanduser calls.

### P6 — `pyfiglet` dependency missing from requirements
- Neofetch scripts use pyfiglet for ASCII art but it's not in requirements.txt
  or pyproject.toml dependencies
- **Fix:** Add `pyfiglet` to dependencies. Or make it optional with a graceful
  fallback (neofetch scripts are extras, not core TUI).

### P7 — Snapshot dir `~/.hermes-hud/` created silently
- snapshot.py writes to `~/.hermes-hud/snapshots.jsonl` — creates the dir
  without asking
- Not a huge deal, but should be documented
- **Fix:** Document it. Consider putting snapshots under `~/.hermes/hud/`
  instead to keep everything in one tree.

### P8 — No Makefile / setup script for dev workflow
- No `make dev`, `make install`, `make test` targets
- **Fix:** Add a Makefile with common targets.

---

## Execution Order

### Phase 1 — Fix the deal-breakers (P1, P3, P5)
1. Restructure into `hermes_hud/` package
2. Fix all shebangs to `python3`
3. Centralize HERMES_HOME with env var support
4. Entry point via pyproject.toml `[project.scripts]`
5. Verify `pip install -e .` → `hermes-hud` works

### Phase 2 — Config & graceful defaults (P2, P4)
6. Add HERMES_HUD_PROJECTS_DIR env var
7. Add first-run "no data" message
8. Optional: `~/.hermes-hud/config.yaml` for settings

### Phase 3 — Polish (P6, P7, P8)
9. Add pyfiglet to optional deps
10. Makefile with dev/install/test targets
11. Update README install section

---

## Non-goals (this pass)
- PyPI publication (not yet — get the install flow right first)
- Windows native support (WSL is fine)
- Docker packaging
