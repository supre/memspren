"""Unit tests for memcli.finalize.metrics_writer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.log import make_logger
from memcli.finalize.metrics_writer import (
    archive_buffers,
    rotate_telemetry_log,
    update_system_state,
    run,
)

_log = make_logger("test")


def _make_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    sb = vault / ".second-brain"
    (sb / "memory").mkdir(parents=True)
    (sb / "run").mkdir(parents=True)
    (sb / "buffers").mkdir(parents=True)
    (sb / "logs").mkdir(parents=True)
    return vault


# ── archive_buffers ────────────────────────────────────────────────────────

def test_archive_buffers_moves_files(tmp_path):
    buffers = tmp_path / "buffers"
    buffers.mkdir()

    buf_file = buffers / "sync-buffer-001.md"
    buf_file.write_text("buffer content", encoding="utf-8")

    sealed = [{"buffer_id": "001", "filename": "sync-buffer-001.md"}]
    count = archive_buffers(buffers, sealed)

    assert count == 1
    assert not buf_file.exists()
    assert len(list((buffers / "sync-archive").glob("*.md"))) == 1


def test_archive_buffers_skips_missing_files(tmp_path):
    buffers = tmp_path / "buffers"
    buffers.mkdir()
    sealed = [{"buffer_id": "999", "filename": "sync-buffer-999.md"}]
    count = archive_buffers(buffers, sealed)
    assert count == 0


def test_archive_buffers_returns_zero_for_non_list(tmp_path):
    buffers = tmp_path / "buffers"
    buffers.mkdir()
    assert archive_buffers(buffers, None) == 0
    assert archive_buffers(buffers, {}) == 0


# ── update_system_state ────────────────────────────────────────────────────

def test_update_system_state_creates_new_file(tmp_path):
    mem = tmp_path / "memory"
    mem.mkdir()
    update_system_state(mem, "2026-03-30T12:00:00Z", "1 created, 0 updated")
    content = (mem / "system-state.md").read_text()
    assert "last_sync: 2026-03-30T12:00:00Z" in content


def test_update_system_state_updates_existing(tmp_path):
    mem = tmp_path / "memory"
    mem.mkdir()
    (mem / "system-state.md").write_text("last_sync: 2026-01-01T00:00:00Z\n", encoding="utf-8")

    update_system_state(mem, "2026-03-30T12:00:00Z", "new summary")
    content = (mem / "system-state.md").read_text()
    assert "2026-03-30" in content
    assert "2026-01-01" not in content


# ── rotate_telemetry_log ───────────────────────────────────────────────────

def test_rotate_telemetry_log_trims_large_file(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    log_file = logs / "sync-telemetry.log"
    log_file.write_text("\n".join(f"line {i}" for i in range(5000)), encoding="utf-8")

    rotate_telemetry_log(logs, max_bytes=1, keep_lines=100)

    lines = log_file.read_text().splitlines()
    assert len(lines) == 100
    assert lines[-1] == "line 4999"


def test_rotate_telemetry_log_noop_when_small(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    log_file = logs / "sync-telemetry.log"
    log_file.write_text("short log\n", encoding="utf-8")

    rotate_telemetry_log(logs, max_bytes=1024 * 1024, keep_lines=100)
    assert log_file.read_text() == "short log\n"


def test_rotate_telemetry_log_noop_when_missing(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    rotate_telemetry_log(logs, max_bytes=1, keep_lines=100)


# ── run() ──────────────────────────────────────────────────────────────────

def test_main_writes_metrics_json(tmp_path):
    vault = _make_vault(tmp_path)

    result = run(vault_path=vault, log=_log)
    assert result["ok"] is True
    assert result["metrics_written"] is True
    assert (vault / ".second-brain" / "run" / "metrics.json").exists()


def test_main_archives_buffers_only_when_entity_writes_ok(tmp_path):
    from memcli import state
    vault = _make_vault(tmp_path)
    buffers = vault / ".second-brain" / "buffers"
    run_dir = vault / ".second-brain" / "run"

    buf_file = buffers / "sync-buffer-001.md"
    buf_file.write_text("buf", encoding="utf-8")

    # Write sealed buffers to state but no entity write result
    state.write_state(str(run_dir), {
        "rotate_buffer_sealed_buffers": [{"buffer_id": "001", "filename": "sync-buffer-001.md"}],
    })

    result = run(vault_path=vault, log=_log)
    assert result["archive_count"] == 0
    assert buf_file.exists()


def test_main_archives_buffers_when_entity_writes_ok(tmp_path):
    from memcli import state
    vault = _make_vault(tmp_path)
    buffers = vault / ".second-brain" / "buffers"
    run_dir = vault / ".second-brain" / "run"

    buf_file = buffers / "sync-buffer-001.md"
    buf_file.write_text("buf", encoding="utf-8")

    # Write sealed buffers to state + entity write result file
    state.write_state(str(run_dir), {
        "rotate_buffer_sealed_buffers": [{"buffer_id": "001", "filename": "sync-buffer-001.md"}],
    })
    (run_dir / "entity-write-result.json").write_text(
        json.dumps({"entities": [{"path": "test.md", "action": "create"}]}),
        encoding="utf-8",
    )

    result = run(vault_path=vault, log=_log)
    assert result["archive_count"] == 1
    assert not buf_file.exists()
