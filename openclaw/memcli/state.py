"""
state.py — Shared state file manager for Lobster workflow.

State file location: {run_path}/state.json

All functions accept a run_path (the .second-brain/run directory).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_state_path(run_path: str | Path) -> Path:
    return Path(run_path) / "state.json"


def read_state(run_path: str | Path) -> dict[str, Any]:
    state_path = get_state_path(run_path)
    if not state_path.exists():
        return {}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(run_path: str | Path, updates: dict[str, Any]) -> None:
    state_path = get_state_path(run_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    current = read_state(run_path)
    current.update(updates)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def get_field(run_path: str | Path, field: str, default: Any = None) -> Any:
    state = read_state(run_path)
    return state.get(field, default)


def clear_state(run_path: str | Path) -> None:
    state_path = get_state_path(run_path)
    if state_path.exists():
        state_path.unlink()
