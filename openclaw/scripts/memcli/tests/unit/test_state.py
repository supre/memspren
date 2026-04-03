"""Unit tests for memcli.state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli import state


def test_read_state_missing_returns_empty(tmp_path):
    result = state.read_state(str(tmp_path / "run"))
    assert result == {}


def test_write_state_creates_state_file(tmp_path):
    run_path = tmp_path / "run"
    state.write_state(str(run_path), {"key": "value"})
    assert (run_path / "state.json").exists()


def test_write_state_merges_not_overwrites(tmp_path):
    run_path = tmp_path / "run"
    state.write_state(str(run_path), {"a": 1})
    state.write_state(str(run_path), {"b": 2})
    result = state.read_state(str(run_path))
    assert result == {"a": 1, "b": 2}


def test_write_state_overwrites_same_key(tmp_path):
    run_path = tmp_path / "run"
    state.write_state(str(run_path), {"a": 1})
    state.write_state(str(run_path), {"a": 99})
    assert state.read_state(str(run_path))["a"] == 99


def test_get_field_returns_value(tmp_path):
    run_path = tmp_path / "run"
    state.write_state(str(run_path), {"vault_name": "test-vault"})
    assert state.get_field(str(run_path), "vault_name") == "test-vault"


def test_get_field_returns_default_when_missing(tmp_path):
    run_path = tmp_path / "run"
    assert state.get_field(str(run_path), "nonexistent", "fallback") == "fallback"


def test_get_field_returns_none_by_default(tmp_path):
    run_path = tmp_path / "run"
    assert state.get_field(str(run_path), "missing") is None


def test_clear_state_removes_file(tmp_path):
    run_path = tmp_path / "run"
    state.write_state(str(run_path), {"x": 1})
    state.clear_state(str(run_path))
    assert not (run_path / "state.json").exists()


def test_clear_state_noop_when_missing(tmp_path):
    """clear_state should not raise if state file doesn't exist."""
    run_path = tmp_path / "run"
    state.clear_state(str(run_path))  # Should not raise
