"""Test that HERMES_HOME and HERMES_HUD_PROJECTS_DIR env vars work."""

import os
import pytest
from hermes_hud.collectors.utils import default_hermes_dir, default_projects_dir


def test_hermes_home_default(monkeypatch):
    """Without env var, defaults to ~/.hermes."""
    monkeypatch.delenv("HERMES_HOME", raising=False)
    result = default_hermes_dir()
    assert result == os.path.expanduser("~/.hermes")


def test_hermes_home_env_var(monkeypatch):
    """HERMES_HOME env var overrides the default."""
    monkeypatch.setenv("HERMES_HOME", "/custom/path")
    result = default_hermes_dir()
    assert result == "/custom/path"


def test_hermes_home_explicit_arg_wins(monkeypatch):
    """Explicit argument beats env var."""
    monkeypatch.setenv("HERMES_HOME", "/from-env")
    result = default_hermes_dir("/explicit")
    assert result == "/explicit"


def test_projects_dir_default(monkeypatch):
    """Without env var, defaults to ~/projects."""
    monkeypatch.delenv("HERMES_HUD_PROJECTS_DIR", raising=False)
    result = default_projects_dir()
    assert result == os.path.expanduser("~/projects")


def test_projects_dir_env_var(monkeypatch):
    """HERMES_HUD_PROJECTS_DIR env var overrides the default."""
    monkeypatch.setenv("HERMES_HUD_PROJECTS_DIR", "/my/code")
    result = default_projects_dir()
    assert result == "/my/code"


def test_projects_dir_explicit_arg_wins(monkeypatch):
    """Explicit argument beats env var."""
    monkeypatch.setenv("HERMES_HUD_PROJECTS_DIR", "/from-env")
    result = default_projects_dir("/explicit")
    assert result == "/explicit"
