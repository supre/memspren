#!/usr/bin/env python3
"""
write_lock.py — Manage the sync lock file and prune stale Lobster resume tokens.

Without --release: writes sync.lock. Aborts with exit 1 if lock already exists
(signals a concurrent sync run — Lobster will emit SYNC SKIPPED).

With --release: removes sync.lock and optionally prunes stale resume tokens.

Returns JSON to stdout:
  { "ok": bool, "action": "locked"|"skipped"|"released", "error": str|null }
"""

import argparse
import datetime
import json
import sys
from pathlib import Path


def prune_stale_tokens(memory_path: Path, ttl_hours: float) -> int:
    """Remove Lobster resume token files older than ttl_hours. Returns count pruned."""
    token_dir = memory_path / ".lobster-tokens"
    if not token_dir.exists():
        return 0
    cutoff = datetime.datetime.now(datetime.UTC).timestamp() - (ttl_hours * 3600)
    pruned = 0
    for token_file in token_dir.glob("*.json"):
        try:
            if token_file.stat().st_mtime < cutoff:
                token_file.unlink()
                pruned += 1
        except OSError:
            pass
    return pruned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-path", required=True)
    parser.add_argument("--release", action="store_true",
                        help="Release (delete) the lock instead of writing it")
    parser.add_argument("--prune-tokens-older-than-hours", type=float, default=None,
                        help="Prune stale Lobster resume tokens older than N hours (only with --release)")
    parser.add_argument("--stale-lock-hours", type=float, default=2.0,
                        help="Auto-release a lock file older than this many hours (default: 2)")
    args = parser.parse_args()

    memory_path = Path(args.memory_path)
    lock_path = memory_path / "sync.lock"

    if args.release:
        try:
            if lock_path.exists():
                lock_path.unlink()
            pruned = 0
            if args.prune_tokens_older_than_hours:
                pruned = prune_stale_tokens(memory_path, args.prune_tokens_older_than_hours)
            result = {"ok": True, "action": "released"}
            if pruned:
                result["tokens_pruned"] = pruned
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"ok": False, "action": "error", "error": str(e)}))
            sys.exit(1)
        return

    # Write lock
    if lock_path.exists():
        # Check whether the existing lock is stale (pipeline crashed without releasing)
        stale = False
        stale_hours = args.stale_lock_hours or 2.0
        try:
            raw = lock_path.read_text(encoding="utf-8")
            # locked_at line format: "locked_at: 2026-03-28T12:00:00Z"
            for line in raw.splitlines():
                if line.startswith("locked_at:"):
                    ts_str = line.split(":", 1)[1].strip().rstrip("Z")
                    locked_at = datetime.datetime.fromisoformat(ts_str)
                    age_hours = (datetime.datetime.now(datetime.UTC) - locked_at).total_seconds() / 3600
                    if age_hours >= stale_hours:
                        stale = True
                    break
        except Exception:
            pass  # Can't determine age — treat as live lock

        if not stale:
            print(json.dumps({
                "ok": False,
                "action": "skipped",
                "error": "sync.lock exists — concurrent run in progress. SYNC SKIPPED.",
            }))
            sys.exit(1)

        # Stale lock — log and overwrite
        print(json.dumps({"warn": f"stale sync.lock detected (>{stale_hours}h old) — auto-releasing"}),
              file=sys.stderr)
        try:
            lock_path.unlink()
        except Exception:
            pass

    try:
        memory_path.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        lock_path.write_text(f"locked_at: {ts}\n", encoding="utf-8")
        print(json.dumps({"ok": True, "action": "locked"}))
    except Exception as e:
        print(json.dumps({"ok": False, "action": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
