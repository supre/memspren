"""merge.py — Collect, validate, and write Layer 1 memory files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..log import Logger
from ..paths import VaultPaths

MEMORY_FILES: dict[str, str] = {
    "insights":   "insights.md",
    "goals":      "goals.md",
    "tasks":      "tasks.md",
    "hot_memory": "hot-memory.md",
}


def run(
    *,
    vault_path: Path,
    parallel_results: dict,
    log: Logger,
) -> dict:
    if not parallel_results:
        raise RuntimeError("empty input from parallel_memory")

    paths = VaultPaths(vault_path)
    paths.memory.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    fallback: list[str] = []

    for key, filename in MEMORY_FILES.items():
        job = parallel_results.get(key, {})
        if job.get("ok") and job.get("content"):
            try:
                (paths.memory / filename).write_text(job["content"], encoding="utf-8")
                written.append(key)
                log.info(f"wrote {filename}", content_len=len(job["content"]))
            except Exception as e:
                log.warn(f"write failed for {filename}: {e}")
                fallback.append(key)
        else:
            reason = job.get("error", "no content returned")
            log.warn(f"{key} job failed ({reason}) — keeping existing {filename}")
            fallback.append(key)

    if len(fallback) == 4:
        raise RuntimeError("all 4 memory refinement jobs failed — aborting before vault writes")

    parts = []
    for key in MEMORY_FILES:
        label = key.replace("_", "-")
        parts.append(f"{label} {'OK' if key in written else 'FALLBACK'}")

    return {"ok": True, "written": written, "fallback": fallback, "summary": ", ".join(parts)}
