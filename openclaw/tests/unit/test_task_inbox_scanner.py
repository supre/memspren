"""Unit tests for memcli.scanning.task_inbox_scanner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.scanning.task_inbox_scanner import (
    deduplicate,
    levenshtein_ratio,
    parse_task_line,
    run,
)


# ── levenshtein_ratio ──────────────────────────────────────────────────────

def test_identical_strings_ratio_is_1():
    assert levenshtein_ratio("hello", "hello") == 1.0


def test_completely_different_strings_low_ratio():
    assert levenshtein_ratio("abc", "xyz") < 0.5


def test_empty_strings_ratio_is_1():
    assert levenshtein_ratio("", "") == 1.0


def test_one_empty_string_ratio_is_0():
    assert levenshtein_ratio("hello", "") == 0.0


# ── parse_task_line ────────────────────────────────────────────────────────

def test_parses_open_task():
    task = parse_task_line("- [ ] Write unit tests")
    assert task is not None
    assert task["title"] == "Write unit tests"
    assert task["status"] == "open"
    assert task["completed_date"] is None


def test_parses_completed_task():
    task = parse_task_line("- [x] Deploy to production")
    assert task is not None
    assert task["status"] == "completed"


def test_parses_completed_task_with_date():
    task = parse_task_line("- [x] Code review | 2026-03-15")
    assert task is not None
    assert task["completed_date"] == "2026-03-15"
    assert task["status"] == "completed"


def test_parses_uppercase_x():
    task = parse_task_line("- [X] Fix bug")
    assert task is not None
    assert task["status"] == "completed"


def test_returns_none_for_non_task():
    assert parse_task_line("## Heading") is None
    assert parse_task_line("Regular paragraph text") is None
    assert parse_task_line("") is None


# ── deduplicate ────────────────────────────────────────────────────────────

def test_deduplicates_near_identical_tasks():
    tasks = [
        {"title": "Write unit tests for the API", "status": "open", "completed_date": None},
        {"title": "Write unit test for the API",  "status": "open", "completed_date": None},
    ]
    result = deduplicate(tasks, threshold=0.85)
    assert len(result) == 1
    assert result[0]["title"] == "Write unit tests for the API"


def test_keeps_distinct_tasks():
    tasks = [
        {"title": "Deploy to staging", "status": "open", "completed_date": None},
        {"title": "Review pull request", "status": "open", "completed_date": None},
    ]
    result = deduplicate(tasks, threshold=0.85)
    assert len(result) == 2


def test_dedup_empty_list():
    assert deduplicate([], threshold=0.85) == []


# ── run() integration ─────────────────────────────────────────────────────

def test_main_parses_tasks_and_writes_file(tmp_path):
    vault = tmp_path / "vault"
    tasks_dir = vault / "Tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "tasks-inbox.md").write_text(
        "- [ ] Task Alpha\n- [x] Task Beta | 2026-01-10\n",
        encoding="utf-8",
    )
    mem = tmp_path / "Memory"
    mem.mkdir()

    result = run(vault_path=vault, memory_path=mem)

    assert result["open_count"] == 1
    assert len(result["tasks"]) == 2
    assert (mem / "run" / "task-inbox.json").exists()


def test_main_returns_empty_when_no_inbox(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    result = run(vault_path=vault)

    assert result["open_count"] == 0
    assert result["tasks"] == []
