"""setup.py — Idempotent vault scaffold for MemSpren.

Creates all required vault folders, seed files, .second-brain/ structure,
memory stubs, and initializes git. Safe to call at any time — never overwrites
existing content. Only creates what is missing.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from .log import Logger
from .paths import VaultPaths

TODAY = date.today().isoformat()

VAULT_FOLDERS = [
    "Vision",
    "Strategy",
    "Work/Projects",
    "Work/Ideas",
    "Work/KT",
    "People",
    "Log/Daily",
    "Log/Weekly",
    "Notes/Learnings",
    "Notes/Patterns",
    "Tasks",
    "Inbox",
    "Archive",
    "Logs",
]

SEED_FILES: dict[str, str] = {
    "Tasks/tasks-inbox.md": (
        "---\n"
        "node_type: tasks-inbox\n"
        f"description: \"Unified task inbox\"\n"
        f"created: {TODAY}\n"
        "status: active\n"
        "connected: []\n"
        "tags: []\n"
        "---\n\n"
        "# Tasks Inbox\n\n"
        "## Active Tasks\n\n"
        "## Completed (last 2 weeks)\n"
    ),
    "Vision/long-term-vision.md": (
        "---\n"
        "node_type: vision\n"
        f"description: \"Long-term vision — to be populated\"\n"
        f"created: {TODAY}\n"
        "status: active\n"
        "connected: []\n"
        "tags: []\n"
        f"last_modified: {TODAY}\n"
        "---\n\n"
        "# Long-term Vision\n\n"
        "*Add your vision here.*\n"
    ),
    "Vision/core-values.md": (
        "---\n"
        "node_type: vision\n"
        f"description: \"Core values — to be populated\"\n"
        f"created: {TODAY}\n"
        "status: active\n"
        "connected: []\n"
        "tags: []\n"
        f"last_modified: {TODAY}\n"
        "---\n\n"
        "# Core Values\n\n"
        "*Add your values here.*\n"
    ),
    "Strategy/quarterly-goals.md": (
        "---\n"
        "node_type: strategy\n"
        f"description: \"Quarterly goals — to be populated\"\n"
        f"created: {TODAY}\n"
        "status: active\n"
        "connected: []\n"
        "tags: []\n"
        f"last_modified: {TODAY}\n"
        "---\n\n"
        "# Quarterly Goals\n\n"
        "*Add your quarterly goals here.*\n"
    ),
}

MEMORY_STUBS: dict[str, str] = {
    "insights.md": (
        f"LAST_UPDATED: {TODAY}\n\n"
        "WHAT_MATTERS_NOW\n[To be populated after first check-in]\n\n"
        "RECENT_CHALLENGES\n\n"
        "PATTERNS_OBSERVED\n\n"
        "STRATEGIES_WORKING\n\n"
        "STRATEGIES_NOT_WORKING\n\n"
        "ENERGY_STATE\n\n"
        "MINDSET_STATE\n\n"
        "VISION_ALIGNMENT\n"
    ),
    "goals.md": (
        f"LAST_UPDATED: {TODAY}\n\n"
        "LEAD_DOMINO\n[To be populated after first check-in]\n\n"
        "TOP_3\n\n"
        "WHAT_TO_AVOID\n\n"
        "HEALTH_PRIORITY\n\n"
        "EMOTIONAL_CHECK\n\n"
        "WEEKLY_MICRO_GOALS\n\n"
        "QUARTERLY_GOALS\n"
    ),
    "tasks.md": (
        f"LAST_UPDATED: {TODAY}\n\n"
        "OPEN_TASKS\n[To be populated after first sync]\n\n"
        "COMPLETED_RECENTLY\n\n"
        "BLOCKED\n"
    ),
    "hot-memory.md": (
        f"LAST_UPDATED: {TODAY}\n\n"
        "ACTIVE_PROJECTS [max 3]\n\n"
        "OPEN_THREADS\n\n"
        "EVIDENCE_TRAIL\n\n"
        "KEY_INSIGHTS\n\n"
        "IDEAS_PARKED\n"
    ),
    "system-state.md": (
        "---\n"
        "node_type: system-state\n"
        "setup_complete: false\n"
        f"last_updated: {TODAY}\n"
        "---\n"
        "# System State\n\n"
        "## Behavioral Flags\n"
        "journaling: false\n"
        "lifestyle_tracking: false\n"
        "auto_archive: true\n"
    ),
}

GITIGNORE = """.obsidian/workspace.json
.obsidian/workspace-mobile.json
.DS_Store
.trash/
"""


def _create_if_missing(path: Path, content: str, log: Logger) -> bool:
    """Write content to path only if path doesn't exist. Returns True if created."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log.info(f"created: {path.name}")
    return True


def run(
    *,
    vault_path: Path,
    vault_name: str = "",
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)

    created_folders: list[str] = []
    created_files: list[str] = []

    # Create vault content folders
    for folder in VAULT_FOLDERS:
        target = vault_path / folder
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created_folders.append(folder)
            log.info(f"created folder: {folder}")

    # Create seed files (vault content)
    for rel_path, content in SEED_FILES.items():
        if _create_if_missing(vault_path / rel_path, content, log):
            created_files.append(rel_path)

    # Create .second-brain/ directories
    paths.ensure()

    # Create memory stubs
    for filename, content in MEMORY_STUBS.items():
        if _create_if_missing(paths.memory / filename, content, log):
            created_files.append(f".second-brain/memory/{filename}")

    # .gitignore
    gitignore_path = vault_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE, encoding="utf-8")
        created_files.append(".gitignore")
        log.info("created .gitignore")

    # Git init (only if no .git directory)
    git_initialized = False
    git_dir = vault_path / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init"],
                cwd=str(vault_path),
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(vault_path),
                capture_output=True, text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "initial vault snapshot"],
                cwd=str(vault_path),
                capture_output=True, text=True,
            )
            git_initialized = True
            log.info("git initialized and initial commit made")
        except Exception as e:
            log.warn(f"git init failed: {e}")

    log.info(
        "setup complete",
        folders_created=len(created_folders),
        files_created=len(created_files),
        git_initialized=git_initialized,
    )

    return {
        "ok": True,
        "folders_created": created_folders,
        "files_created": created_files,
        "git_initialized": git_initialized,
    }
