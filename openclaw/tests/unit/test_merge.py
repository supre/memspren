"""Unit tests for memcli.memory.merge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.memory.merge import run


def test_writes_all_four_files(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    all_ok = {
        "insights":   {"ok": True, "content": "# Insights\nNew insights.", "error": None},
        "goals":      {"ok": True, "content": "# Goals\nNew goals.",       "error": None},
        "tasks":      {"ok": True, "content": "# Tasks\nNew tasks.",       "error": None},
        "hot_memory": {"ok": True, "content": "# Hot Memory\nWarm.",       "error": None},
    }

    result = run(memory_path=mem, parallel_results=all_ok)

    assert result["ok"] is True
    assert set(result["written"]) == {"insights", "goals", "tasks", "hot_memory"}
    assert result["fallback"] == []

    assert (mem / "insights.md").read_text() == "# Insights\nNew insights."
    assert (mem / "goals.md").read_text() == "# Goals\nNew goals."


def test_failed_job_keeps_existing_file(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()
    (mem / "insights.md").write_text("Original insights content", encoding="utf-8")

    one_failed = {
        "insights":   {"ok": False, "content": "", "error": "gateway error"},
        "goals":      {"ok": True, "content": "# Goals",  "error": None},
        "tasks":      {"ok": True, "content": "# Tasks",  "error": None},
        "hot_memory": {"ok": True, "content": "# HotMem", "error": None},
    }

    result = run(memory_path=mem, parallel_results=one_failed)

    assert result["ok"] is True
    assert "insights" in result["fallback"]
    assert (mem / "insights.md").read_text() == "Original insights content"


def test_all_failed_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    all_failed = {key: {"ok": False, "content": "", "error": "err"} for key in
                  ("insights", "goals", "tasks", "hot_memory")}

    with pytest.raises(RuntimeError, match="all 4"):
        run(memory_path=mem, parallel_results=all_failed)


def test_empty_stdin_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    with pytest.raises(RuntimeError, match="empty input"):
        run(memory_path=mem, parallel_results={})


def test_invalid_json_stdin_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    # All keys missing → all 4 fail → RuntimeError
    with pytest.raises(RuntimeError, match="all 4"):
        run(memory_path=mem, parallel_results={"garbage": True})
