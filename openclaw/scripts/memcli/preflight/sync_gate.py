"""sync_gate.py — Stop the pipeline cleanly when there is nothing to sync.

Reads rotate_buffer_has_content from state.json. If False, releases the lock
and exits with code 1 to halt the Lobster pipeline. If True, exits 0 so the
pipeline continues.

This must be called as a raw Click command (not via _exec) so it can emit
valid JSON and still control the exit code independently.
"""

from __future__ import annotations

import json
import sys

from ..log import Logger
from ..paths import VaultPaths
from .. import state


def run(*, vault_path, log: Logger) -> None:
    """Check whether there is content to sync. Exits 1 if not (halts pipeline)."""
    paths = VaultPaths(vault_path)

    has_content = state.get_field(str(paths.run), "rotate_buffer_has_content", False)

    if not has_content:
        lock_path = paths.buffers / "sync.lock"
        if lock_path.exists():
            try:
                lock_path.unlink()
                log.info("released lock on clean exit")
            except OSError as e:
                log.warn("could not release lock", error=str(e))

        log.info("sync gate: nothing to sync — halting pipeline")
        print(json.dumps({"ok": True, "action": "nothing_to_sync", "message": "Nothing to sync."}))
        sys.exit(1)

    log.info("sync gate: content detected — proceeding with sync")
