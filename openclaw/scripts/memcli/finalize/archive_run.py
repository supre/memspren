"""archive_run.py — Archive run artifacts from run/ into run/archive/ with a timestamp.

Every file in run/ (not subdirectories) is renamed with a YYYYMMDD-HHMMSS suffix
and moved into run/archive/. This gives each pipeline run a fresh view of run/
while keeping a full history of what was produced.

Cleanup of old archives is a separate concern (future cron job).
"""

from __future__ import annotations

import datetime
from pathlib import Path

from ..log import Logger
from ..paths import VaultPaths


def run(*, vault_path: Path, log: Logger) -> dict:
    paths = VaultPaths(vault_path)
    run_dir = paths.run
    archive_dir = run_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    archived = []
    failed = []
    for src in sorted(run_dir.iterdir()):
        if src.is_dir():
            continue  # skip archive/ and any other subdirectories
        dst = archive_dir / f"{src.stem}-{ts}{src.suffix}"
        try:
            src.rename(dst)
            archived.append(src.name)
            log.debug(f"archived {src.name}", dst=dst.name)
        except Exception as e:
            failed.append(src.name)
            log.warn(f"could not archive {src.name}", error=str(e))

    log.info("run artifacts archived", count=len(archived), timestamp=ts, failed=len(failed))
    return {"ok": True, "archived": archived, "failed": failed, "timestamp": ts}
