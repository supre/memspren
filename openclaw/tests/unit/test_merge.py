"""Unit tests for memcli.memory.merge."""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from memcli.memory.merge import main


def _run_merge(memory_path: Path, stdin_data: dict) -> tuple[int, dict]:
    """Run merge.main() with given stdin JSON; return (exit_code, parsed_stdout)."""
    buf = io.StringIO()
    stdin_json = json.dumps(stdin_data)
    exit_code = 0
    with mock.patch.object(sys, "argv", ["merge-layer1", "--memory-path", str(memory_path)]):
        with mock.patch("sys.stdin", io.StringIO(stdin_json)):
            with contextlib.redirect_stdout(buf):
                try:
                    main()
                except SystemExit as e:
                    exit_code = e.code or 0
    output = buf.getvalue().strip()
    result = json.loads(output) if output else {}
    return exit_code, result


def test_writes_all_four_files(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    all_ok = {
        "insights":   {"ok": True, "content": "# Insights\nNew insights.", "error": None},
        "goals":      {"ok": True, "content": "# Goals\nNew goals.",       "error": None},
        "tasks":      {"ok": True, "content": "# Tasks\nNew tasks.",       "error": None},
        "hot_memory": {"ok": True, "content": "# Hot Memory\nWarm.",       "error": None},
    }

    exit_code, result = _run_merge(mem, all_ok)

    assert exit_code == 0
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

    exit_code, result = _run_merge(mem, one_failed)

    assert exit_code == 0
    assert result["ok"] is True
    assert "insights" in result["fallback"]
    # Existing file should NOT be overwritten
    assert (mem / "insights.md").read_text() == "Original insights content"


def test_all_failed_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    all_failed = {key: {"ok": False, "content": "", "error": "err"} for key in
                  ("insights", "goals", "tasks", "hot_memory")}

    exit_code, result = _run_merge(mem, all_failed)

    assert exit_code == 1
    assert result["ok"] is False


def test_empty_stdin_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    buf = io.StringIO()
    exit_code = 0
    with mock.patch.object(sys, "argv", ["merge-layer1", "--memory-path", str(mem)]):
        with mock.patch("sys.stdin", io.StringIO("")):
            with contextlib.redirect_stdout(buf):
                try:
                    main()
                except SystemExit as e:
                    exit_code = e.code or 0

    assert exit_code == 1


def test_invalid_json_stdin_exits_1(tmp_path):
    mem = tmp_path / "Memory"
    mem.mkdir()

    buf = io.StringIO()
    exit_code = 0
    with mock.patch.object(sys, "argv", ["merge-layer1", "--memory-path", str(mem)]):
        with mock.patch("sys.stdin", io.StringIO("{not valid json")):
            with contextlib.redirect_stdout(buf):
                try:
                    main()
                except SystemExit as e:
                    exit_code = e.code or 0

    assert exit_code == 1
