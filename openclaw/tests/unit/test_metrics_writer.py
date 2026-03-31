"""Unit tests for memcli.finalize.metrics_writer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.finalize.metrics_writer import (
    archive_buffers,
    rotate_telemetry_log,
    update_system_state,
    run,
)


# ── archive_buffers ────────────────────────────────────────────────────────

def test_archive_buffers_moves_files(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    buf_file = mem / "sync-buffer-001.md"
    buf_file.write_text("buffer content", encoding="utf-8")

    sealed = [{"buffer_id": "001", "filename": "sync-buffer-001.md"}]
    count = archive_buffers(mem, sealed)

    assert count == 1
    assert not buf_file.exists()
    assert len(list((mem / "sync-archive").glob("*.md"))) == 1


def test_archive_buffers_skips_missing_files(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    sealed = [{"buffer_id": "999", "filename": "sync-buffer-999.md"}]
    count = archive_buffers(mem, sealed)
    assert count == 0


def test_archive_buffers_returns_zero_for_non_list(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    assert archive_buffers(mem, None) == 0
    assert archive_buffers(mem, {}) == 0


# ── update_system_state ────────────────────────────────────────────────────

def test_update_system_state_creates_new_file(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    update_system_state(mem, "2026-03-30T12:00:00Z", "1 created, 0 updated")
    content = (mem / "system-state.md").read_text()
    assert "last_sync: 2026-03-30T12:00:00Z" in content


def test_update_system_state_updates_existing(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    (mem / "system-state.md").write_text("last_sync: 2026-01-01T00:00:00Z\n", encoding="utf-8")

    update_system_state(mem, "2026-03-30T12:00:00Z", "new summary")
    content = (mem / "system-state.md").read_text()
    assert "2026-03-30" in content
    assert "2026-01-01" not in content


# ── rotate_telemetry_log ───────────────────────────────────────────────────

def test_rotate_telemetry_log_trims_large_file(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    log = mem / "sync-telemetry.log"
    log.write_text("\n".join(f"line {i}" for i in range(5000)), encoding="utf-8")

    rotate_telemetry_log(mem, max_bytes=1, keep_lines=100)

    lines = log.read_text().splitlines()
    assert len(lines) == 100
    assert lines[-1] == "line 4999"


def test_rotate_telemetry_log_noop_when_small(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    log = mem / "sync-telemetry.log"
    log.write_text("short log\n", encoding="utf-8")

    rotate_telemetry_log(mem, max_bytes=1024 * 1024, keep_lines=100)
    assert log.read_text() == "short log\n"


def test_rotate_telemetry_log_noop_when_missing(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    rotate_telemetry_log(mem, max_bytes=1, keep_lines=100)


# ── run() ──────────────────────────────────────────────────────────────────

def test_main_writes_metrics_json(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()

    result = run(memory_path=mem, vault_path=vault)
    assert result["ok"] is True
    assert result["metrics_written"] is True
    assert (mem / "metrics.json").exists()


def test_main_archives_buffers_only_when_entity_writes_ok(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()

    buf_file = mem / "sync-buffer-001.md"
    buf_file.write_text("buf", encoding="utf-8")

    sealed = json.dumps([{"buffer_id": "001", "filename": "sync-buffer-001.md"}])

    result = run(
        memory_path=mem,
        vault_path=vault,
        sealed_buffers=sealed,
        entity_writes_ok="false",
    )
    assert result["archive_count"] == 0
    assert buf_file.exists()


def test_main_archives_buffers_when_entity_writes_ok(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()

    buf_file = mem / "sync-buffer-001.md"
    buf_file.write_text("buf", encoding="utf-8")

    sealed = json.dumps([{"buffer_id": "001", "filename": "sync-buffer-001.md"}])

    result = run(
        memory_path=mem,
        vault_path=vault,
        sealed_buffers=sealed,
        entity_writes_ok="true",
    )
    assert result["archive_count"] == 1
    assert not buf_file.exists()
