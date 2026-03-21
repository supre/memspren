#!/usr/bin/env python3
"""
git_commit.py — Commit file state before modification.

Safety checkpoint: commits the current version of a file before
the agent modifies it. Nothing is ever lost — user can always
git log / git diff / git revert.

Usage:
    python3 scripts/git_commit.py \\
        --vault-path "/path/to/vault" \\
        --file "Vision/Psychology-Tech Synthesis.md" \\
        --message "pre-merge snapshot: before appending new vision context"

    python3 scripts/git_commit.py \\
        --vault-path "/path/to/vault" \\
        --init

Output: JSON to stdout
"""

import argparse
import json
import subprocess
import sys
import os


def run_git(vault_path: str, *args) -> tuple:
    """Run a git command in the vault directory. Returns (stdout, stderr, returncode)."""
    cmd = ["git"] + list(args)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=vault_path, timeout=10
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return "", str(e), 1


def is_git_repo(vault_path: str) -> bool:
    """Check if the vault is already a git repository."""
    _, _, code = run_git(vault_path, "rev-parse", "--is-inside-work-tree")
    return code == 0


def init_repo(vault_path: str) -> dict:
    """Initialize a git repo in the vault and make initial commit."""
    if is_git_repo(vault_path):
        return {"action": "skipped", "reason": "already a git repo"}

    _, err, code = run_git(vault_path, "init")
    if code != 0:
        return {"action": "error", "error": f"git init failed: {err}"}

    # Create .gitignore for Obsidian internals
    gitignore_path = os.path.join(vault_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write(".obsidian/workspace.json\n")
            f.write(".obsidian/workspace-mobile.json\n")
            f.write(".DS_Store\n")
            f.write(".trash/\n")

    run_git(vault_path, "add", "-A")
    _, err, code = run_git(vault_path, "commit", "-m", "initial vault snapshot")
    if code != 0:
        # Might be empty repo with nothing to commit
        return {"action": "initialized", "note": "repo initialized, nothing to commit yet"}

    stdout, _, _ = run_git(vault_path, "rev-parse", "--short", "HEAD")
    return {"action": "initialized", "hash": stdout}


def commit_file(vault_path: str, file_path: str, message: str) -> dict:
    """Commit a specific file's current state."""
    if not is_git_repo(vault_path):
        init_result = init_repo(vault_path)
        if init_result.get("action") == "error":
            return init_result

    full_path = os.path.join(vault_path, file_path)
    if not os.path.exists(full_path):
        return {"action": "skipped", "reason": "file does not exist", "file": file_path}

    # Check if file has changes
    _, _, code = run_git(vault_path, "diff", "--quiet", "--", file_path)
    _, _, staged_code = run_git(vault_path, "diff", "--cached", "--quiet", "--", file_path)

    # Also check if file is untracked
    stdout, _, _ = run_git(vault_path, "ls-files", "--others", "--exclude-standard", "--", file_path)
    is_untracked = bool(stdout.strip())

    if code == 0 and staged_code == 0 and not is_untracked:
        return {"action": "skipped", "reason": "no changes", "file": file_path}

    # Stage and commit
    run_git(vault_path, "add", "--", file_path)
    _, err, code = run_git(vault_path, "commit", "-m", message)
    if code != 0:
        return {"action": "error", "error": f"commit failed: {err}", "file": file_path}

    stdout, _, _ = run_git(vault_path, "rev-parse", "--short", "HEAD")
    return {
        "action": "committed",
        "hash": stdout,
        "file": file_path,
        "message": message
    }


def main():
    parser = argparse.ArgumentParser(
        description="Commit file state before modification (safety checkpoint)"
    )
    parser.add_argument("--vault-path", required=True, help="Full path to Obsidian vault")
    parser.add_argument("--file", help="File to commit (relative to vault root)")
    parser.add_argument("--message", default="pre-modification snapshot", help="Commit message")
    parser.add_argument("--init", action="store_true", help="Initialize git repo in vault")
    args = parser.parse_args()

    if args.init:
        result = init_repo(args.vault_path)
    elif args.file:
        result = commit_file(args.vault_path, args.file, args.message)
    else:
        result = {"action": "error", "error": "provide --file or --init"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
