"""Unit tests for memcli.state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli import state


def test_read_state_missing_returns_empty(tmp_path):
    result = state.read_state(str(tmp_path / "Memory"))
    assert result == {}


def test_write_state_creates_run_dir(tmp_path):
    mem = tmp_path / "Memory"
    state.write_state(str(mem), {"key": "value"})
    assert (mem / "run" / "state.json").exists()


def test_write_state_merges_not_overwrites(tmp_path):
    mem = tmp_path / "Memory"
    state.write_state(str(mem), {"a": 1})
    state.write_state(str(mem), {"b": 2})
    result = state.read_state(str(mem))
    assert result == {"a": 1, "b": 2}


def test_write_state_overwrites_same_key(tmp_path):
    mem = tmp_path / "Memory"
    state.write_state(str(mem), {"a": 1})
    state.write_state(str(mem), {"a": 99})
    assert state.read_state(str(mem))["a"] == 99


def test_get_field_returns_value(tmp_path):
    mem = tmp_path / "Memory"
    state.write_state(str(mem), {"vault_name": "test-vault"})
    assert state.get_field(str(mem), "vault_name") == "test-vault"


def test_get_field_returns_default_when_missing(tmp_path):
    mem = tmp_path / "Memory"
    assert state.get_field(str(mem), "nonexistent", "fallback") == "fallback"


def test_get_field_returns_none_by_default(tmp_path):
    mem = tmp_path / "Memory"
    assert state.get_field(str(mem), "missing") is None


def test_clear_state_removes_file(tmp_path):
    mem = tmp_path / "Memory"
    state.write_state(str(mem), {"x": 1})
    state.clear_state(str(mem))
    assert not (mem / "run" / "state.json").exists()


def test_clear_state_noop_when_missing(tmp_path):
    """clear_state should not raise if state file doesn't exist."""
    mem = tmp_path / "Memory"
    state.clear_state(str(mem))  # Should not raise
