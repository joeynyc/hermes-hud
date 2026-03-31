"""Parse Hermes config.yaml."""

from __future__ import annotations

import os
from pathlib import Path

from models import ConfigState

try:
    import yaml
except ImportError:
    yaml = None


def _parse_yaml_simple(text: str) -> dict:
    """Minimal YAML parser for flat/simple structures when PyYAML isn't available."""
    result = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            val = val.strip()
            if val:
                result[key.strip()] = val
    return result


def collect_config(hermes_dir: str | None = None) -> ConfigState:
    """Collect configuration state."""
    if hermes_dir is None:
        hermes_dir = os.path.expanduser("~/.hermes")

    config_path = Path(hermes_dir) / "config.yaml"
    if not config_path.exists():
        return ConfigState()

    content = config_path.read_text(encoding="utf-8")

    if yaml:
        try:
            data = yaml.safe_load(content)
        except Exception:
            data = _parse_yaml_simple(content)
    else:
        data = _parse_yaml_simple(content)

    if not isinstance(data, dict):
        return ConfigState()

    model_section = data.get("model", {})
    agent_section = data.get("agent", {})
    terminal_section = data.get("terminal", {})
    compression_section = data.get("compression", {})
    checkpoints_section = data.get("checkpoints", {})

    return ConfigState(
        model=model_section.get("default", "") if isinstance(model_section, dict) else str(model_section),
        provider=model_section.get("provider", "") if isinstance(model_section, dict) else "",
        toolsets=data.get("toolsets", []),
        backend=terminal_section.get("backend", "") if isinstance(terminal_section, dict) else "",
        max_turns=agent_section.get("max_turns", 0) if isinstance(agent_section, dict) else 0,
        compression_enabled=compression_section.get("enabled", False) if isinstance(compression_section, dict) else False,
        checkpoints_enabled=checkpoints_section.get("enabled", False) if isinstance(checkpoints_section, dict) else False,
    )
