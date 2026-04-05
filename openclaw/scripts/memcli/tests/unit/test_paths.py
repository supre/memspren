"""Unit tests for memcli.paths.VaultPaths."""
from __future__ import annotations

from pathlib import Path

import pytest

from memcli.paths import VaultPaths


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def test_vault_paths_properties(tmp_vault):
    vp = VaultPaths(tmp_vault)
    assert vp.vault == tmp_vault
    assert vp.base == tmp_vault / ".second-brain"
    assert vp.memory == tmp_vault / ".second-brain" / "memory"
    assert vp.buffers == tmp_vault / ".second-brain" / "buffers"
    assert vp.run == tmp_vault / ".second-brain" / "run"
    assert vp.logs == tmp_vault / ".second-brain" / "logs"


def test_ensure_creates_all_directories(tmp_vault):
    vp = VaultPaths(tmp_vault)
    vp.ensure()
    assert vp.memory.is_dir()
    assert vp.buffers.is_dir()
    assert vp.run.is_dir()
    assert vp.logs.is_dir()


def test_ensure_is_idempotent(tmp_vault):
    vp = VaultPaths(tmp_vault)
    vp.ensure()
    vp.ensure()  # Should not raise
    assert vp.memory.is_dir()


def test_ensure_creates_nested_dirs(tmp_path):
    """ensure() should create the vault/.second-brain/ tree even if missing."""
    vault = tmp_path / "new-vault"
    vault.mkdir()
    vp = VaultPaths(vault)
    vp.ensure()
    assert (vault / ".second-brain" / "memory").is_dir()
