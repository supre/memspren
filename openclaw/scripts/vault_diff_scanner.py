#!/usr/bin/env python3
"""
vault_diff_scanner.py — Scan vault for manually changed files since last sync.

Detects both committed history (git log --after) AND uncommitted working-tree
changes (git status --porcelain + git diff --name-only), so Obsidian edits that
have not been committed are included.

Writes the concatenated file contents to MEMORY_PATH/run/manual-edits.txt and
returns the file path as changed_files_content_file — the downstream
run_entity_plan.py reads from that file to avoid shell interpolation of raw text
in Lobster YAML.

If the vault is not a git repo, logs a warning and returns an empty result (non-fatal).

Returns JSON to stdout:
{
  "changed_files": ["Work/Projects/foo.md", ...],
  "changed_files_content_file": "/abs/path/to/manual-edits.txt",
  "changed_count": int
}
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import state


def run_git(cmd: list, cwd: str, timeout: int = 30) -> tuple[int, str]:
    """Run a git command, return (returncode, stdout)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout,
        )
        return result.returncode, result.stdout
    except Exception:
        return 1, ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--memory-path", required=True,
                        help="MEMORY_PATH — manual-edits.txt written here")
    parser.add_argument("--since", default=None,
                        help="ISO timestamp of last sync (from system-state.md)")
    args = parser.parse_args()

    vault_path  = Path(args.vault_path)
    memory_path = Path(args.memory_path)
    empty = {"changed_files": [], "changed_files_content_file": "", "changed_count": 0}
    
    # Read since timestamp from state if not provided
    since = args.since
    if not since:
        since = state.get_field(str(memory_path), "check_cli_last_sync")

    if not vault_path.exists():
        print(json.dumps({**empty, "warn": "vault path not found"}), file=sys.stderr)
        print(json.dumps(empty))
        return

    # Confirm vault is a git repo
    rc, _ = run_git(["git", "rev-parse", "--git-dir"], str(vault_path))
    if rc != 0:
        print(json.dumps({"warn": "vault is not a git repo — skipping manual edit ingestion"}),
              file=sys.stderr)
        print(json.dumps(empty))
        return

    changed_files: list[str] = []

    # ── Committed history since last_sync ──────────────────────────────────
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

    # ── Uncommitted working-tree changes (staged + unstaged + untracked) ───
    # git status --porcelain emits lines like:
    #   M  path.md   (modified/staged)
    #   ?? path.md   (untracked)
    #    M path.md   (modified unstaged)
    #    D path.md   (deleted — skip, file gone)
    #   R  old -> new.md  (renamed)
    rc, out = run_git(["git", "status", "--porcelain"], str(vault_path))
    if rc == 0 and out.strip():
        for line in out.strip().splitlines():
            if len(line) < 3:
                continue
            xy   = line[:2]
            path = line[3:].strip()

            # Renamed: "R  old -> new" — take the new path after " -> "
            if " -> " in path:
                path = path.split(" -> ")[-1].strip()

            # Skip deleted files (nothing to read)
            if xy.strip() in ("D", "DD", "AD"):
                continue

            if path.endswith(".md"):
                changed_files.append(path)

    # Also catch unstaged modifications not shown by --porcelain for tracked files
    # (belt-and-suspenders: git diff --name-only covers modified-but-unstaged)
    rc, out = run_git(["git", "diff", "--name-only"], str(vault_path))
    if rc == 0 and out.strip():
        for f in out.strip().splitlines():
            f = f.strip()
            if f.endswith(".md"):
                changed_files.append(f)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for f in changed_files:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    changed_files = deduped

    # ── Read content of changed files (exclude .second-brain/) ────────────
    content_parts: list[str] = []
    valid_files:   list[str] = []
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

    # ── Write content to file (avoids shell interpolation of raw text) ─────
    run_dir      = memory_path / "run"
    content_file = str(run_dir / "manual-edits.txt")
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manual-edits.txt").write_text(combined, encoding="utf-8")
    except Exception as e:
        print(json.dumps({"warn": f"could not write manual-edits file: {e}"}),
              file=sys.stderr)
        content_file = ""

    result = {
        "changed_files":              valid_files,
        "changed_files_content_file": content_file,
        "changed_count":              len(valid_files),
    }
    print(json.dumps(result))
    
    # Write to shared state
    state.write_state(str(memory_path), {
        "vault_diff_changed_count": len(valid_files),
    })


if __name__ == "__main__":
    main()
