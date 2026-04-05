"""Unit tests for memcli.preflight.write_lock."""
from __future__ import annotations

import datetime
import os
import time
from pathlib import Path

import pytest

from memcli.log import make_logger
from memcli.preflight.write_lock import run, prune_stale_tokens

_log = make_logger("test")


def _make_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    buffers = vault / ".second-brain" / "buffers"
    buffers.mkdir(parents=True)
    return vault


def test_acquires_lock_when_none_exists(tmp_path):
    vault = _make_vault(tmp_path)
    result = run(vault_path=vault, log=_log)
    assert result["ok"] is True
    assert result["action"] == "locked"
    assert (vault / ".second-brain" / "buffers" / "sync.lock").exists()


def test_skips_when_live_lock_exists(tmp_path):
    vault = _make_vault(tmp_path)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (vault / ".second-brain" / "buffers" / "sync.lock").write_text(f"locked_at: {ts}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="sync.lock exists"):
        run(vault_path=vault, log=_log)


def test_releases_lock(tmp_path):
    vault = _make_vault(tmp_path)
    (vault / ".second-brain" / "buffers" / "sync.lock").write_text("locked_at: 2026-01-01T00:00:00\n", encoding="utf-8")

    result = run(vault_path=vault, release=True, log=_log)
    assert result["ok"] is True
    assert result["action"] == "released"
    assert not (vault / ".second-brain" / "buffers" / "sync.lock").exists()


def test_release_noop_when_no_lock(tmp_path):
    vault = _make_vault(tmp_path)
    result = run(vault_path=vault, release=True, log=_log)
    assert result["ok"] is True
    assert result["action"] == "released"


def test_stale_lock_auto_released(tmp_path):
    vault = _make_vault(tmp_path)
    old_ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=10)).isoformat()
    (vault / ".second-brain" / "buffers" / "sync.lock").write_text(f"locked_at: {old_ts}\n", encoding="utf-8")

    result = run(vault_path=vault, stale_lock_hours=2.0, log=_log)
    assert result["ok"] is True
    assert result["action"] == "locked"


def test_prune_stale_tokens(tmp_path):
    buffers = tmp_path / "buffers"
    buffers.mkdir()
    token_dir = buffers / ".lobster-tokens"
    token_dir.mkdir()
    old_file = token_dir / "old-token.json"
    new_file = token_dir / "new-token.json"
    old_file.write_text("{}", encoding="utf-8")
    new_file.write_text("{}", encoding="utf-8")

    old_mtime = time.time() - (48 * 3600)
    os.utime(str(old_file), (old_mtime, old_mtime))

    pruned = prune_stale_tokens(buffers, ttl_hours=24)
    assert pruned == 1
    assert not old_file.exists()
    assert new_file.exists()
