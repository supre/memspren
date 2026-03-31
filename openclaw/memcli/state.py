#!/usr/bin/env python3
"""
state.py — Shared state file manager for Lobster workflow.

Since Lobster doesn't support $step.json.field access, we use a shared
state file pattern. Each script writes its output fields to a central
state.json file, and subsequent scripts read from known file paths.

State file location: {MEMORY_PATH}/run/state.json
"""

import json
from pathlib import Path
from typing import Any, Dict


def get_state_path(memory_path: str) -> Path:
    """Get path to the shared state file."""
    return Path(memory_path) / "run" / "state.json"


def read_state(memory_path: str) -> Dict[str, Any]:
    """Read the current state. Returns empty dict if file doesn't exist."""
    state_path = get_state_path(memory_path)
    if not state_path.exists():
        return {}
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(memory_path: str, updates: Dict[str, Any]) -> None:
    """
    Update the state file with new fields.
    Merges with existing state - doesn't overwrite the entire file.
    """
    state_path = get_state_path(memory_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    current = read_state(memory_path)
    current.update(updates)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)


def get_field(memory_path: str, field: str, default: Any = None) -> Any:
    """Get a specific field from state. Returns default if not found."""
    state = read_state(memory_path)
    return state.get(field, default)


def clear_state(memory_path: str) -> None:
    """Clear the state file (called at start of sync)."""
    state_path = get_state_path(memory_path)
    if state_path.exists():
        state_path.unlink()
