# Contributing to Hermes HUD

Thanks for your interest. Here's how to get involved.

## Setup

```bash
git clone https://github.com/joeynyc/hermes-hud.git
cd hermes-hud
python3.11 -m venv venv
source venv/bin/activate
python -m pip install -e ".[neofetch]"
```

If `python3.11` is not the right binary on your system, use any Python 3.11+ interpreter you have available instead.

You'll need [Hermes Agent](https://github.com/NousResearch/hermes) installed at `~/.hermes/` for the HUD to have data to display. Without it, panels will be empty but the app will still run.

## Code Style

- Python 3.11+ required
- Type hints are welcome but not enforced
- Follow existing patterns — look at any file in `collectors/` or `widgets/` for the conventions
- Boot screen scripts use raw ANSI escape codes; Textual widgets use the framework's styling

## Making Changes

1. Fork the repo
2. Create a feature branch: `git checkout -b my-feature`
3. Make your changes
4. Test locally: `hermes-hud` for the TUI, `hermes-hud --neofetch` for skins
5. Open a PR against `main`

## What We'd Love Help With

- **New TUI themes** — Add color palettes in `hud.py` following the existing pattern
- **New widgets** — Dashboard panels that surface interesting agent data
- **Better data visualizations** — Sparklines, heatmaps, anything that makes the data sing
- **Documentation** — Usage examples, screenshots, guides

## Architecture Quick Reference

```
collectors/  →  collect.py  →  models.py  →  widgets/  →  hud.py
  (read data)    (orchestrate)   (types)      (render)     (app)
```

Each collector reads from `~/.hermes/` and returns typed data. Widgets consume that data and render it. The TUI tabs are lazy-loaded.

## Questions?

Open an issue. We don't bite.
