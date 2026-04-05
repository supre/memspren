"""metrics_writer.py — Stage 5: write metrics, archive buffers, update system-state."""

from __future__ import annotations

import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import state
from ..log import Logger
from ..paths import VaultPaths

DEFAULT_MAX_LOG_BYTES = 2 * 1024 * 1024
DEFAULT_KEEP_LINES = 2000


def archive_buffers(buffers_path: Path, sealed_buffers) -> int:
    if not isinstance(sealed_buffers, list):
        return 0
    archive_dir = buffers_path / "sync-archive"
    archive_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    archived = 0
    for buf in sealed_buffers:
        filename = buf.get("filename") or f"sync-buffer-{buf.get('buffer_id','x')}.md"
        src = buffers_path / filename
        if not src.exists():
            continue
        dst = archive_dir / f"{ts}-{buf.get('buffer_id','x')}.md"
        try:
            shutil.copy2(str(src), str(dst))
            src.unlink()
            archived += 1
        except Exception as e:
            print(json.dumps({"warn": f"archive failed for {filename}: {e}"}), file=sys.stderr)
    return archived


def update_system_state(memory_path: Path, ts: str, summary: str) -> None:
    state_path = memory_path / "system-state.md"
    if not state_path.exists():
        memory_path.mkdir(parents=True, exist_ok=True)
        state_path.write_text(f"last_sync: {ts}\nlast_sync_summary: {summary}\n", encoding="utf-8")
        return
    content = state_path.read_text(encoding="utf-8")
    if re.search(r"^last_sync:", content, re.MULTILINE):
        content = re.sub(r"^last_sync:.*$", f"last_sync: {ts}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\nlast_sync: {ts}\n"
    if re.search(r"^last_sync_summary:", content, re.MULTILINE):
        content = re.sub(r"^last_sync_summary:.*$", f"last_sync_summary: {summary}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\nlast_sync_summary: {summary}\n"
    state_path.write_text(content, encoding="utf-8")


def append_system_log(vault_path: Path, log_entry: str, write_mode: str = "filesystem", vault_name: str = "") -> None:
    log_rel = "Logs/system-log.md"
    log_path = vault_path / log_rel
    if write_mode == "obsidian" and vault_name:
        try:
            subprocess.run(
                ["obsidian", f"vault={vault_name}", "append", f"path={log_rel}", f"content=\n\n{log_entry}"],
                capture_output=True, text=True, timeout=30, check=True,
            )
        except Exception as e:
            print(json.dumps({"warn": f"obsidian system-log append failed: {e}"}), file=sys.stderr)
        return
    try:
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
            log_path.write_text(existing.rstrip() + "\n\n" + log_entry, encoding="utf-8")
        else:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(f"# System Log\n\n{log_entry}", encoding="utf-8")
    except Exception as e:
        print(json.dumps({"warn": f"system-log write failed: {e}"}), file=sys.stderr)


def rotate_telemetry_log(logs_path: Path, max_bytes: int, keep_lines: int) -> None:
    log_path = logs_path / "sync-telemetry.log"
    if not log_path.exists():
        return
    if log_path.stat().st_size <= max_bytes:
        return
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        log_path.write_text("\n".join(lines[-keep_lines:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def _read_json(path: Path) -> dict | list:
    """Read a JSON file, return {} on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run(
    *,
    vault_path: Path,
    write_mode: str = "filesystem",
    vault_name: str = "",
    max_log_bytes: int = DEFAULT_MAX_LOG_BYTES,
    keep_lines: int = DEFAULT_KEEP_LINES,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()

    # Read all prior step results from run/ files
    extraction = _read_json(paths.run / "extraction-output.json")
    entity = _read_json(paths.run / "entity-write-result.json")
    vault_diff_state = state.get_field(str(paths.run), "vault_diff_changed_count", 0)

    sealed_bufs = state.get_field(str(paths.run), "rotate_buffer_sealed_buffers", [])

    # Entity writes considered OK if the result file exists and has written > 0
    entity_ok = isinstance(entity, dict) and entity.get("entities") and len(entity.get("entities", [])) > 0
    entity_writes_ok_state = state.get_field(str(paths.run), "entity_writes_ok", False)
    do_archive = entity_ok or entity_writes_ok_state
    archive_count = archive_buffers(paths.buffers, sealed_bufs) if do_archive else 0
    if not do_archive:
        log.info("buffer archival skipped — entity writes did not succeed")

    if archive_count > 0:
        from ..buffer.rotate_buffer import reset_active_to_001
        reset_result = reset_active_to_001(str(paths.buffers))
        log.debug("buffer id reset check", **reset_result)

    ts = datetime.datetime.utcnow().isoformat() + "Z"

    # Check which memory files exist to determine what was written
    written_keys = []
    for key, filename in [("insights", "insights.md"), ("goals", "goals.md"),
                          ("tasks", "tasks.md"), ("hot_memory", "hot-memory.md")]:
        if (paths.memory / filename).exists():
            written_keys.append(key)
    metrics = {
        "last_sync": ts,
        "buffers_processed": archive_count,
        "entities_created": entity.get("created", 0) if isinstance(entity, dict) else 0,
        "entities_updated": entity.get("updated", 0) if isinstance(entity, dict) else 0,
        "entities_merged": entity.get("merged", 0) if isinstance(entity, dict) else 0,
        "links_added": entity.get("links_added", 0) if isinstance(entity, dict) else 0,
        "manual_edits_absorbed": vault_diff_state if isinstance(vault_diff_state, int) else 0,
        "memory_files_updated": written_keys,
        "inference_results": {
            "extraction": "ok" if extraction else "fail",
            "insights": "ok" if "insights" in written_keys else "fail",
            "goals": "ok" if "goals" in written_keys else "fail",
            "tasks": "ok" if "tasks" in written_keys else "fail",
            "hot_memory": "ok" if "hot_memory" in written_keys else "fail",
            "entity_plan": "ok" if (isinstance(entity, dict) and entity.get("ok")) else "fail",
        },
    }

    metrics_path = paths.run / "metrics.json"
    metrics_written = False
    try:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        metrics_written = True
        log.debug("wrote metrics.json")
    except Exception as e:
        log.warn(f"metrics write failed: {e}")

    summary = (
        f"{metrics['entities_created']} created, "
        f"{metrics['entities_updated']} updated, "
        f"{len(written_keys)} memory files updated"
    )

    if do_archive:
        update_system_state(paths.memory, ts, summary)
        log_entry = (
            f"[{ts}] SYNC COMPLETE\n"
            f"  buffers_processed: {metrics['buffers_processed']}\n"
            f"  entities_created: {metrics['entities_created']}\n"
            f"  entities_updated: {metrics['entities_updated']}\n"
            f"  memory_files_updated: {', '.join(written_keys) or 'none'}\n"
            f"  manual_edits_absorbed: {metrics['manual_edits_absorbed']}"
        )
    else:
        log_entry = (
            f"[{ts}] SYNC INCOMPLETE — vault writes skipped or failed\n"
            f"  memory_files_updated: {', '.join(written_keys) or 'none'}\n"
            f"  note: last_sync NOT advanced; next run will re-diff from previous checkpoint"
        )
    append_system_log(vault_path, log_entry, write_mode=write_mode, vault_name=vault_name)
    rotate_telemetry_log(paths.logs, max_log_bytes, keep_lines)

    log.info("metrics complete", summary=summary, archive_count=archive_count)
    return {"ok": True, "metrics_written": metrics_written, "archive_count": archive_count, "summary": summary}
