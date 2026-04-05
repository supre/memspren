"""Unit tests for memcli.memory.merge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.log import make_logger
from memcli.memory.merge import run

_log = make_logger("test")


def _make_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    mem = vault / ".second-brain" / "memory"
    mem.mkdir(parents=True)
    return vault


def test_writes_all_four_files(tmp_path):
    vault = _make_vault(tmp_path)
    mem = vault / ".second-brain" / "memory"

    all_ok = {
        "insights":   {"ok": True, "content": "# Insights\nNew insights.", "error": None},
        "goals":      {"ok": True, "content": "# Goals\nNew goals.",       "error": None},
        "tasks":      {"ok": True, "content": "# Tasks\nNew tasks.",       "error": None},
        "hot_memory": {"ok": True, "content": "# Hot memory\nWarm.",       "error": None},
    }

    result = run(vault_path=vault, parallel_results=all_ok, log=_log)

    assert result["ok"] is True
    assert set(result["written"]) == {"insights", "goals", "tasks", "hot_memory"}
    assert result["fallback"] == []

    assert (mem / "insights.md").read_text() == "# Insights\nNew insights."
    assert (mem / "goals.md").read_text() == "# Goals\nNew goals."


def test_failed_job_keeps_existing_file(tmp_path):
    vault = _make_vault(tmp_path)
    mem = vault / ".second-brain" / "memory"
    (mem / "insights.md").write_text("Original insights content", encoding="utf-8")

    one_failed = {
        "insights":   {"ok": False, "content": "", "error": "gateway error"},
        "goals":      {"ok": True, "content": "# Goals",  "error": None},
        "tasks":      {"ok": True, "content": "# Tasks",  "error": None},
        "hot_memory": {"ok": True, "content": "# HotMem", "error": None},
    }

    result = run(vault_path=vault, parallel_results=one_failed, log=_log)

    assert result["ok"] is True
    assert "insights" in result["fallback"]
    assert (mem / "insights.md").read_text() == "Original insights content"


def test_all_failed_exits_1(tmp_path):
    vault = _make_vault(tmp_path)

    all_failed = {key: {"ok": False, "content": "", "error": "err"} for key in
                  ("insights", "goals", "tasks", "hot_memory")}

    with pytest.raises(RuntimeError, match="all 4"):
        run(vault_path=vault, parallel_results=all_failed, log=_log)


def test_empty_stdin_exits_1(tmp_path):
    vault = _make_vault(tmp_path)

    with pytest.raises(RuntimeError, match="empty input"):
        run(vault_path=vault, parallel_results={}, log=_log)


def test_invalid_json_stdin_exits_1(tmp_path):
    vault = _make_vault(tmp_path)

    # All keys missing -> all 4 fail -> RuntimeError
    with pytest.raises(RuntimeError, match="all 4"):
        run(vault_path=vault, parallel_results={"garbage": True}, log=_log)
