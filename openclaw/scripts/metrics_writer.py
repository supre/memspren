#!/usr/bin/env python3
"""
metrics_writer.py — Stage 5: write metrics.json, archive buffers, update system-state.md.

Collects results from all prior stages, writes the metrics snapshot, archives sealed
buffers, updates system-state.md (last_sync, last_sync_summary), and appends to
Logs/system-log.md.

Log rotation: if sync-telemetry.log exceeds max_log_bytes (default 2 MB), trims
to the newest keep_lines lines (default 2000).

Returns JSON to stdout:
{ "ok": bool, "metrics_written": bool, "archive_count": int, "summary": str }
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_MAX_LOG_BYTES = 2 * 1024 * 1024  # 2 MB
DEFAULT_KEEP_LINES    = 2000


def archive_buffers(memory_path: Path, sealed_buffers) -> int:
    """Move sealed buffers to sync-archive/. Returns count archived."""
    if not isinstance(sealed_buffers, list):
        return 0
    archive_dir = memory_path / "sync-archive"
    archive_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    archived = 0
    for buf in sealed_buffers:
        filename = buf.get("filename") or f"sync-buffer-{buf.get('buffer_id','x')}.md"
        src = memory_path / filename
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
        # Create minimal file so vault_diff_scanner can find last_sync on next run
        memory_path.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            f"last_sync: {ts}\nlast_sync_summary: {summary}\n",
            encoding="utf-8",
        )
        return

    content = state_path.read_text(encoding="utf-8")

    # Update existing key, or append it if absent
    if re.search(r"^last_sync:", content, re.MULTILINE):
        content = re.sub(r"^last_sync:.*$", f"last_sync: {ts}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\nlast_sync: {ts}\n"

    if re.search(r"^last_sync_summary:", content, re.MULTILINE):
        content = re.sub(r"^last_sync_summary:.*$", f"last_sync_summary: {summary}", content, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f"\nlast_sync_summary: {summary}\n"

    state_path.write_text(content, encoding="utf-8")


def append_system_log(
    vault_path: Path, log_entry: str, write_mode: str = "filesystem", vault_name: str = ""
) -> None:
    log_rel = "Logs/system-log.md"
    log_path = vault_path / log_rel

    if write_mode == "obsidian" and vault_name:
        # Route through obsidian-cli so Obsidian watchers are triggered
        try:
            subprocess.run(
                ["obsidian", f"vault={vault_name}", "append",
                 f"path={log_rel}", f"content=\n\n{log_entry}"],
                capture_output=True, text=True, timeout=30, check=True,
            )
        except Exception as e:
            print(json.dumps({"warn": f"obsidian system-log append failed: {e}"}), file=sys.stderr)
        return

    # Filesystem path
    try:
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
            log_path.write_text(existing.rstrip() + "\n\n" + log_entry, encoding="utf-8")
        else:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(f"# System Log\n\n{log_entry}", encoding="utf-8")
    except Exception as e:
        print(json.dumps({"warn": f"system-log write failed: {e}"}), file=sys.stderr)


def rotate_telemetry_log(memory_path: Path, max_bytes: int, keep_lines: int) -> None:
    log_path = memory_path / "sync-telemetry.log"
    if not log_path.exists():
        return
    if log_path.stat().st_size <= max_bytes:
        return
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        log_path.write_text("\n".join(lines[-keep_lines:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-path", required=True)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--write-mode", default="filesystem")
    parser.add_argument("--vault-name", default="",
                        help="Obsidian vault name (required for obsidian write mode)")
    parser.add_argument("--extraction-result",  default="{}")
    parser.add_argument("--layer1-result",       default="{}")
    parser.add_argument("--entity-result",       default="{}")
    parser.add_argument("--vault-diff-result",   default="{}")
    parser.add_argument("--sealed-buffers",      default="[]")
    parser.add_argument("--entity-writes-ok",    default="false",
                        help="Pass 'true' only when entity_writes step returned ok=true. "
                             "Buffers are NOT archived unless this flag is true.")
    parser.add_argument("--max-log-bytes",       type=int, default=DEFAULT_MAX_LOG_BYTES)
    parser.add_argument("--keep-lines",          type=int, default=DEFAULT_KEEP_LINES)
    args = parser.parse_args()

    memory_path = Path(args.memory_path)
    vault_path  = Path(args.vault_path)

    def parse(s: str) -> dict | list:
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}

    extraction   = parse(args.extraction_result)
    layer1       = parse(args.layer1_result)
    entity       = parse(args.entity_result)
    vault_diff   = parse(args.vault_diff_result)
    sealed_bufs  = parse(args.sealed_buffers)

    # Only archive buffers if entity writes actually succeeded.
    # Skipped when: approval was denied, entity_pipeline errored, or step never ran.
    entity_writes_ok = str(args.entity_writes_ok).lower() in ("true", "1", "yes")
    archive_count = archive_buffers(memory_path, sealed_bufs) if entity_writes_ok else 0
    if not entity_writes_ok:
        print(json.dumps({"info": "buffer archival skipped — entity writes did not succeed"}),
              file=sys.stderr)

    ts = datetime.datetime.utcnow().isoformat() + "Z"

    written_keys = layer1.get("written", []) if isinstance(layer1, dict) else []
    metrics = {
        "last_sync":                ts,
        "buffers_processed":        archive_count,
        "entities_created":         entity.get("created", 0) if isinstance(entity, dict) else 0,
        "entities_updated":         entity.get("updated", 0) if isinstance(entity, dict) else 0,
        "entities_merged":          entity.get("merged", 0) if isinstance(entity, dict) else 0,
        "links_added":              entity.get("links_added", 0) if isinstance(entity, dict) else 0,
        "manual_edits_absorbed":    vault_diff.get("changed_count", 0) if isinstance(vault_diff, dict) else 0,
        "memory_files_updated":     written_keys,
        "inference_results": {
            "extraction":  "ok" if extraction else "fail",
            "insights":    "ok" if "insights"   in written_keys else "fail",
            "goals":       "ok" if "goals"       in written_keys else "fail",
            "tasks":       "ok" if "tasks"       in written_keys else "fail",
            "hot_memory":  "ok" if "hot_memory"  in written_keys else "fail",
            "entity_plan": "ok" if (isinstance(entity, dict) and entity.get("ok")) else "fail",
        },
    }

    metrics_path = memory_path / "metrics.json"
    metrics_written = False
    try:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        metrics_written = True
    except Exception as e:
        print(json.dumps({"warn": f"metrics write failed: {e}"}), file=sys.stderr)

    summary = (
        f"{metrics['entities_created']} created, "
        f"{metrics['entities_updated']} updated, "
        f"{len(written_keys)} memory files updated"
    )

    if entity_writes_ok:
        # Only advance last_sync when vault writes actually completed.
        # If entity writes were skipped (approval denied) or failed, keeping the
        # old last_sync means the next vault_diff_scanner still sees un-synced edits.
        update_system_state(memory_path, ts, summary)
        log_entry = (
            f"[{ts}] SYNC COMPLETE\n"
            f"  buffers_processed: {metrics['buffers_processed']}\n"
            f"  entities_created: {metrics['entities_created']}\n"
            f"  entities_updated: {metrics['entities_updated']}\n"
            f"  memory_files_updated: {', '.join(written_keys) or 'none'}\n"
            f"  manual_edits_absorbed: {metrics['manual_edits_absorbed']}"
        )
    else:
        # Vault writes did not complete — record the attempt but do not advance last_sync.
        log_entry = (
            f"[{ts}] SYNC INCOMPLETE — vault writes skipped or failed\n"
            f"  memory_files_updated: {', '.join(written_keys) or 'none'}\n"
            f"  note: last_sync NOT advanced; next run will re-diff from previous checkpoint"
        )
    append_system_log(vault_path, log_entry, write_mode=args.write_mode, vault_name=args.vault_name)

    rotate_telemetry_log(memory_path, args.max_log_bytes, args.keep_lines)

    print(json.dumps({
        "ok":              True,
        "metrics_written": metrics_written,
        "archive_count":   archive_count,
        "summary":         summary,
    }))


if __name__ == "__main__":
    main()
