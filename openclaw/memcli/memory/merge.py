"""
merge.py — Collect, validate, and write Layer 1 memory files.

Stage 3: receives Stage 2 parallel refinement results, validates each,
and writes files to .second-brain/Memory/. Pure logic — no LLM.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MEMORY_FILES: dict[str, str] = {
    "insights":   "insights.md",
    "goals":      "goals.md",
    "tasks":      "tasks.md",
    "hot_memory": "hot-memory.md",
}


def run(
    *,
    memory_path: Path,
    parallel_results: dict,
) -> dict:
    if not parallel_results:
        raise RuntimeError("empty input from parallel_memory")

    memory_path.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    fallback: list[str] = []

    for key, filename in MEMORY_FILES.items():
        job = parallel_results.get(key, {})
        if job.get("ok") and job.get("content"):
            try:
                (memory_path / filename).write_text(job["content"], encoding="utf-8")
                written.append(key)
            except Exception as e:
                print(json.dumps({"warn": f"write failed for {filename}: {e}"}),
                      file=sys.stderr)
                fallback.append(key)
        else:
            reason = job.get("error", "no content returned")
            print(json.dumps({"warn": f"{key} job failed ({reason}) — keeping existing {filename}"}),
                  file=sys.stderr)
            fallback.append(key)

    if len(fallback) == 4:
        raise RuntimeError("all 4 memory refinement jobs failed — aborting before vault writes")

    parts = []
    for key in MEMORY_FILES:
        label = key.replace("_", "-")
        parts.append(f"{label} {'OK' if key in written else 'FALLBACK'}")

    return {
        "ok": True,
        "written": written,
        "fallback": fallback,
        "summary": ", ".join(parts),
    }
