"""clean_exit.py — Emit a clean exit signal for Lobster when there is nothing to sync."""

from __future__ import annotations

from pathlib import Path

from ..log import Logger
from ..paths import VaultPaths


def run(
    *,
    vault_path: Path,
    message: str = "Nothing to sync.",
    release_lock: bool = False,
    log: Logger,
) -> dict:
    if release_lock:
        paths = VaultPaths(vault_path)
        lock_path = paths.buffers / "sync.lock"
        try:
            if lock_path.exists():
                lock_path.unlink()
                log.info("released lock on clean exit")
        except OSError:
            pass

    log.info("clean exit", message=message)
    return {"ok": True, "action": "exit", "message": message}
