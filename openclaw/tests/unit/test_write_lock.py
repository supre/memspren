"""Unit tests for openclaw.scripts.preflight.write_lock."""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from openclaw.scripts.preflight.write_lock import main, prune_stale_tokens


def run_write_lock(args: list[str], memory_path: Path) -> dict:
    """Helper: run write_lock.main() with given args, return parsed JSON stdout."""
    import io, contextlib
    buf = io.StringIO()
    with mock.patch.object(sys, "argv", ["write-lock"] + args):
        with contextlib.redirect_stdout(buf):
            try:
                main()
            except SystemExit:
                pass
    output = buf.getvalue().strip()
    return json.loads(output) if output else {}


def test_acquires_lock_when_none_exists(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    result = run_write_lock(["--memory-path", str(mem)], mem)
    assert result["ok"] is True
    assert result["action"] == "locked"
    assert (mem / "sync.lock").exists()


def test_skips_when_live_lock_exists(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    # Write a fresh (non-stale) lock
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (mem / "sync.lock").write_text(f"locked_at: {ts}\n", encoding="utf-8")

    import io, contextlib
    buf = io.StringIO()
    with mock.patch.object(sys, "argv", ["write-lock", "--memory-path", str(mem)]):
        with contextlib.redirect_stdout(buf):
            with pytest.raises(SystemExit) as exc_info:
                main()
    assert exc_info.value.code == 1
    result = json.loads(buf.getvalue().strip())
    assert result["action"] == "skipped"


def test_releases_lock(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    (mem / "sync.lock").write_text("locked_at: 2026-01-01T00:00:00\n", encoding="utf-8")

    result = run_write_lock(["--memory-path", str(mem), "--release"], mem)
    assert result["ok"] is True
    assert result["action"] == "released"
    assert not (mem / "sync.lock").exists()


def test_release_noop_when_no_lock(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    result = run_write_lock(["--memory-path", str(mem), "--release"], mem)
    assert result["ok"] is True
    assert result["action"] == "released"


def test_stale_lock_auto_released(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    # Write a lock that is 10 hours old
    old_ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=10)).isoformat()
    (mem / "sync.lock").write_text(f"locked_at: {old_ts}\n", encoding="utf-8")

    result = run_write_lock(["--memory-path", str(mem), "--stale-lock-hours", "2"], mem)
    assert result["ok"] is True
    assert result["action"] == "locked"


def test_prune_stale_tokens(tmp_path):
    token_dir = tmp_path / ".lobster-tokens"
    token_dir.mkdir()
    old_file = token_dir / "old-token.json"
    new_file = token_dir / "new-token.json"
    old_file.write_text("{}", encoding="utf-8")
    new_file.write_text("{}", encoding="utf-8")

    # Make old_file appear very old
    import os, time
    old_mtime = time.time() - (48 * 3600)
    os.utime(str(old_file), (old_mtime, old_mtime))

    pruned = prune_stale_tokens(tmp_path, ttl_hours=24)
    assert pruned == 1
    assert not old_file.exists()
    assert new_file.exists()
