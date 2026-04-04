"""Test that every module in the package imports cleanly."""

import importlib
import pytest


MODULES = [
    "hermes_hud",
    "hermes_hud.hud",
    "hermes_hud.collect",
    "hermes_hud.models",
    "hermes_hud.snapshot",
    "hermes_hud.neofetch_base",
    "hermes_hud.neofetch_ai",
    "hermes_hud.neofetch_anime",
    "hermes_hud.neofetch_br",
    "hermes_hud.neofetch_fsociety",
    "hermes_hud.collectors",
    "hermes_hud.collectors.utils",
    "hermes_hud.collectors.memory",
    "hermes_hud.collectors.skills",
    "hermes_hud.collectors.sessions",
    "hermes_hud.collectors.config",
    "hermes_hud.collectors.timeline",
    "hermes_hud.collectors.cron",
    "hermes_hud.collectors.health",
    "hermes_hud.collectors.corrections",
    "hermes_hud.collectors.projects",
    "hermes_hud.collectors.agents",
    "hermes_hud.widgets",
    "hermes_hud.widgets.boot_screen",
    "hermes_hud.widgets.overview",
    "hermes_hud.widgets.memory_panel",
    "hermes_hud.widgets.skills_panel",
    "hermes_hud.widgets.sessions_panel",
    "hermes_hud.widgets.timeline_panel",
    "hermes_hud.widgets.diff_panel",
    "hermes_hud.widgets.cron_panel",
    "hermes_hud.widgets.projects_panel",
    "hermes_hud.widgets.health_panel",
    "hermes_hud.widgets.corrections_panel",
    "hermes_hud.widgets.agents_panel",
    "hermes_hud.collectors.profiles",
    "hermes_hud.widgets.profiles_panel",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_import(module_name):
    """Every module in the package should import without error."""
    mod = importlib.import_module(module_name)
    assert mod is not None


def test_no_sys_path_hacks():
    """No module should use sys.path.insert — we're a proper package now."""
    import hermes_hud
    import os

    pkg_dir = os.path.dirname(hermes_hud.__file__)
    for root, _dirs, files in os.walk(pkg_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            with open(path) as f:
                content = f.read()
            assert "sys.path.insert" not in content, (
                f"{path} still contains sys.path.insert — remove it"
            )


def test_no_python311_shebangs():
    """No shebang should hardcode python3.11."""
    import hermes_hud
    import os

    pkg_dir = os.path.dirname(hermes_hud.__file__)
    for root, _dirs, files in os.walk(pkg_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            with open(path) as f:
                first_line = f.readline()
            if first_line.startswith("#!"):
                assert "python3.11" not in first_line, (
                    f"{path} has hardcoded python3.11 shebang"
                )
