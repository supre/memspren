"""vault_diff_scanner.py — Scan vault for manually changed files since last sync."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .. import state
from ..log import Logger
from ..paths import VaultPaths


def run_git(cmd: list, cwd: str, timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return result.returncode, result.stdout
    except Exception:
        return 1, ""


def run(
    *,
    vault_path: Path,
    since: str | None = None,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()
    empty = {"changed_files": [], "changed_files_content_file": "", "changed_count": 0}

    if not since:
        since = state.get_field(str(paths.run), "check_cli_last_sync")

    if not vault_path.exists():
        log.warn("vault path not found", vault_path=str(vault_path))
        return empty

    rc, _ = run_git(["git", "rev-parse", "--git-dir"], str(vault_path))
    if rc != 0:
        log.warn("vault is not a git repo — skipping manual edit ingestion")
        return empty

    changed_files: list[str] = []

    if since and since not in ("null", "None", ""):
        rc, out = run_git(
            ["git", "log", "--name-only", "--pretty=format:", f"--after={since}"],
            str(vault_path),
        )
        if rc == 0 and out.strip():
            for f in out.strip().splitlines():
                f = f.strip()
                if f.endswith(".md"):
                    changed_files.append(f)

    rc, out = run_git(["git", "status", "--porcelain"], str(vault_path))
    if rc == 0 and out.strip():
        for line in out.strip().splitlines():
            if len(line) < 3:
                continue
            xy = line[:2]
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ")[-1].strip()
            if xy.strip() in ("D", "DD", "AD"):
                continue
            if path.endswith(".md"):
                changed_files.append(path)

    rc, out = run_git(["git", "diff", "--name-only"], str(vault_path))
    if rc == 0 and out.strip():
        for f in out.strip().splitlines():
            f = f.strip()
            if f.endswith(".md"):
                changed_files.append(f)

    seen: set[str] = set()
    deduped: list[str] = []
    for f in changed_files:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    changed_files = deduped

    content_parts: list[str] = []
    valid_files: list[str] = []
    for rel_path in changed_files:
        if ".second-brain/" in rel_path or rel_path.startswith(".second-brain"):
            continue
        full_path = vault_path / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
            content_parts.append(f"=== {rel_path} ===\n{content}\n")
            valid_files.append(rel_path)
        except Exception:
            pass

    combined = "\n".join(content_parts)

    content_file = str(paths.run / "manual-edits.txt")
    try:
        (paths.run / "manual-edits.txt").write_text(combined, encoding="utf-8")
    except Exception as e:
        log.warn(f"could not write manual-edits file: {e}")
        content_file = ""

    log.info("vault diff scan complete", changed_count=len(valid_files))

    state.write_state(str(paths.run), {"vault_diff_changed_count": len(valid_files)})

    return {
        "changed_files": valid_files,
        "changed_files_content_file": content_file,
        "changed_count": len(valid_files),
    }
