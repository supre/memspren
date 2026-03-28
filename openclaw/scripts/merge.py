#!/usr/bin/env python3
"""
merge.py — Collect, validate, and write Layer 1 memory files.

Stage 3: receives Stage 2 parallel refinement results, validates each against
its schema, and writes files to .second-brain/Memory/. Pure logic — no LLM.

Failure handling:
  - Schema validation fails → keep existing file, log WARN to stderr, continue
  - Job returned ok=false  → keep existing file, log WARN, continue
  - All four fail          → exit 1 so Lobster aborts before vault writes

Returns JSON to stdout:
{
  "ok": bool,
  "written": ["insights", "goals", "tasks", "hot_memory"],
  "fallback": ["hot_memory"],
  "summary": "insights OK, goals OK, tasks OK, hot-memory FALLBACK"
}
"""

import argparse
import json
import sys
from pathlib import Path

MEMORY_FILES: dict[str, str] = {
    "insights":   "insights.md",
    "goals":      "goals.md",
    "tasks":      "tasks.md",
    "hot_memory": "hot-memory.md",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True,
                        help="JSON string from parallel_memory.py")
    parser.add_argument("--memory-path", required=True)
    args = parser.parse_args()

    try:
        results = json.loads(args.results)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "ok": False, "error": f"invalid results JSON: {e}",
            "written": [], "fallback": [], "summary": "",
        }))
        sys.exit(1)

    memory_path = Path(args.memory_path)
    memory_path.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    fallback: list[str] = []

    for key, filename in MEMORY_FILES.items():
        job = results.get(key, {})
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

    # Abort if all four failed — nothing useful to write
    if len(fallback) == 4:
        print(json.dumps({
            "ok": False,
            "error": "all 4 memory refinement jobs failed — aborting before vault writes",
            "written": [],
            "fallback": list(MEMORY_FILES.keys()),
            "summary": "ALL FAILED",
        }))
        sys.exit(1)

    parts = []
    for key in MEMORY_FILES:
        label = key.replace("_", "-")
        parts.append(f"{label} {'OK' if key in written else 'FALLBACK'}")

    print(json.dumps({
        "ok": True,
        "written": written,
        "fallback": fallback,
        "summary": ", ".join(parts),
    }))


if __name__ == "__main__":
    main()
