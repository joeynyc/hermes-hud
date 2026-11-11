"""Test that unknown CLI options are rejected instead of booting the TUI."""

import pytest

import hermes_hud.hud as hud_module


class FakeApp:
    """Stand-in for the Textual app: records launch, never opens a UI."""

    launched = []

    def run(self):
        FakeApp.launched.append(True)


@pytest.fixture
def no_tui(monkeypatch):
    FakeApp.launched = []
    monkeypatch.setattr(hud_module, "HermesHUD", FakeApp)


def test_unknown_option_exits_nonzero_without_launching_tui(monkeypatch, capsys, no_tui):
    """A typo'd flag must fail fast with exit code 2, not start the dashboard."""
    monkeypatch.setattr("sys.argv", ["hermes-hud", "--bogus-flag"])
    with pytest.raises(SystemExit) as exc_info:
        hud_module.main()
    assert exc_info.value.code == 2
    assert FakeApp.launched == []
    assert "bogus" in capsys.readouterr().err


def test_help_still_prints_usage(monkeypatch, capsys, no_tui):
    """--help keeps working and never launches the TUI."""
    monkeypatch.setattr("sys.argv", ["hermes-hud", "--help"])
    assert hud_module.main() is None
    assert "--text" in capsys.readouterr().out
    assert FakeApp.launched == []
