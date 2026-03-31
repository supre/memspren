"""
clean_exit.py — Emit a clean exit signal for Lobster when there is nothing to sync.

Optionally releases the sync lock before exiting.
"""

from __future__ import annotations

from pathlib import Path


def run(
    *,
    message: str = "Nothing to sync.",
    release_lock: bool = False,
    memory_path: Path | None = None,
) -> dict:
    if release_lock and memory_path:
        lock_path = memory_path / "sync.lock"
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            pass

    return {"ok": True, "action": "exit", "message": message}
