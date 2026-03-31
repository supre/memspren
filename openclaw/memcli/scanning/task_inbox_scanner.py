"""task_inbox_scanner.py — Parse tasks-inbox.md and extract open/completed tasks."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .. import state
from ..log import Logger
from ..paths import VaultPaths


def levenshtein_ratio(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        new_dp = [i] + [0] * n
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                new_dp[j] = dp[j - 1]
            else:
                new_dp[j] = 1 + min(dp[j], new_dp[j - 1], dp[j - 1])
        dp = new_dp
    return 1.0 - dp[n] / max(m, n)


def parse_task_line(line: str) -> dict | None:
    match = re.match(
        r"^-\s+\[([ xX])\]\s+(.+?)(?:\s+\|\s+(\d{4}-\d{2}-\d{2}))?$",
        line.strip(),
    )
    if not match:
        return None
    checked, title, date = match.groups()
    status = "completed" if checked.lower() == "x" else "open"
    return {"title": title.strip(), "status": status, "completed_date": date}


def deduplicate(tasks: list[dict], threshold: float) -> list[dict]:
    seen: list[dict] = []
    for task in tasks:
        if not any(levenshtein_ratio(task["title"], s["title"]) >= threshold for s in seen):
            seen.append(task)
    return seen


def run(
    *,
    vault_path: Path,
    dedup_threshold: float = 0.85,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()
    inbox_path = vault_path / "Tasks" / "tasks-inbox.md"
    empty = {"tasks": [], "completed": [], "open_count": 0, "task_inbox_file": ""}

    if not inbox_path.exists():
        log.debug("no tasks-inbox.md found")
        return empty

    raw_tasks: list[dict] = []
    try:
        for line in inbox_path.read_text(encoding="utf-8").splitlines():
            task = parse_task_line(line)
            if task:
                raw_tasks.append(task)
    except Exception as e:
        log.warn(f"error reading tasks-inbox: {e}")
        return empty

    tasks = deduplicate(raw_tasks, dedup_threshold)
    completed = [t for t in tasks if t["status"] == "completed"]
    open_tasks = [t for t in tasks if t["status"] == "open"]

    result: dict = {"tasks": tasks, "completed": completed, "open_count": len(open_tasks)}

    task_inbox_file = ""
    try:
        out_path = paths.run / "task-inbox.json"
        out_path.write_text(json.dumps(result), encoding="utf-8")
        task_inbox_file = str(out_path)
    except Exception as e:
        log.warn(f"could not write task-inbox file: {e}")

    state.write_state(str(paths.run), {
        "task_inbox_file": task_inbox_file,
        "task_inbox_open_count": len(open_tasks),
    })

    result["task_inbox_file"] = task_inbox_file
    log.info("task inbox parsed", open_count=len(open_tasks), total=len(tasks))
    return result
