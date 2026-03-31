"""write_lock.py — Manage the sync lock file and prune stale Lobster resume tokens."""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from ..log import Logger
from ..paths import VaultPaths


def prune_stale_tokens(buffers_path: Path, ttl_hours: float) -> int:
    token_dir = buffers_path / ".lobster-tokens"
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


def run(
    *,
    vault_path: Path,
    release: bool = False,
    prune_tokens_older_than_hours: float | None = None,
    stale_lock_hours: float = 2.0,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()
    lock_path = paths.buffers / "sync.lock"

    if release:
        log.info("releasing lock", lock_path=str(lock_path))
        try:
            if lock_path.exists():
                lock_path.unlink()
            pruned = 0
            if prune_tokens_older_than_hours:
                pruned = prune_stale_tokens(paths.buffers, prune_tokens_older_than_hours)
                log.debug("pruned stale tokens", count=pruned)
            result: dict = {"ok": True, "action": "released"}
            if pruned:
                result["tokens_pruned"] = pruned
            return result
        except Exception as e:
            log.error("release failed", error=str(e))
            raise RuntimeError(str(e)) from e

    # Write lock
    if lock_path.exists():
        stale = False
        hours = stale_lock_hours or 2.0
        try:
            raw = lock_path.read_text(encoding="utf-8")
            for line in raw.splitlines():
                if line.startswith("locked_at:"):
                    ts_str = line.split(":", 1)[1].strip().rstrip("Z")
                    locked_at = datetime.datetime.fromisoformat(ts_str)
                    age_hours = (datetime.datetime.now(datetime.UTC) - locked_at).total_seconds() / 3600
                    if age_hours >= hours:
                        stale = True
                    break
        except Exception:
            pass

        if not stale:
            log.warn("lock exists, skipping", lock_path=str(lock_path))
            raise RuntimeError("sync.lock exists — concurrent run in progress. SYNC SKIPPED.")

        log.warn(f"stale sync.lock detected (>{hours}h old) — auto-releasing")
        try:
            lock_path.unlink()
        except Exception:
            pass

    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        lock_path.write_text(f"locked_at: {ts}\n", encoding="utf-8")
        log.info("lock acquired", lock_path=str(lock_path))
        return {"ok": True, "action": "locked"}
    except Exception as e:
        log.error("lock write failed", error=str(e))
        raise RuntimeError(str(e)) from e
