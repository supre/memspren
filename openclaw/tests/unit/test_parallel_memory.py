"""Unit tests for memcli.memory.parallel_memory."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from memcli.memory.parallel_memory import JOBS, load_existing, run_job, run


# ── load_existing ──────────────────────────────────────────────────────────

def test_load_existing_reads_file(tmp_path):
    (tmp_path / "insights.md").write_text("# Insights\ncontent here", encoding="utf-8")
    result = load_existing(tmp_path, "insights.md")
    assert "content here" in result


def test_load_existing_returns_empty_string_when_missing(tmp_path):
    result = load_existing(tmp_path, "nonexistent.md")
    assert result == ""


# ── JOBS configuration ─────────────────────────────────────────────────────

def test_jobs_has_four_entries():
    assert len(JOBS) == 4


def test_insights_job_has_raw_patterns_key():
    insights_job = next(j for j in JOBS if j["name"] == "insights")
    assert "raw_patterns" in insights_job["extraction_keys"]


def test_goals_job_includes_task_inbox_extra_key():
    goals_job = next(j for j in JOBS if j["name"] == "goals")
    assert "task_inbox" in goals_job["extra_keys"]


def test_tasks_job_includes_task_inbox_extra_key():
    tasks_job = next(j for j in JOBS if j["name"] == "tasks")
    assert "task_inbox" in tasks_job["extra_keys"]


def test_hot_memory_job_has_no_extra_keys():
    hot_job = next(j for j in JOBS if j["name"] == "hot_memory")
    assert hot_job["extra_keys"] == []


# ── run_job ────────────────────────────────────────────────────────────────

def test_run_job_succeeds(tmp_path, monkeypatch):
    from tests.conftest import make_parallel_job_response

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    extraction = {
        "raw_insights": [{"summary": "test insight"}],
        "raw_patterns": [{"pattern": "test pattern"}],
    }

    job = next(j for j in JOBS if j["name"] == "insights")

    with mock.patch("memcli.gateway_client.post_json",
                    return_value=make_parallel_job_response("insights-content")):
        name, result = run_job(job, extraction, tmp_path, {})

    assert name == "insights"
    assert result["ok"] is True
    assert result["content"] == "insights-content"
    assert result["error"] is None


def test_run_job_returns_ok_false_on_gateway_error(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    job = next(j for j in JOBS if j["name"] == "goals")
    extraction = {"raw_goals": []}

    with mock.patch("memcli.gateway_client.post_json",
                    side_effect=RuntimeError("Gateway HTTP 503")):
        name, result = run_job(job, extraction, tmp_path, {})

    assert name == "goals"
    assert result["ok"] is False
    assert "503" in result["error"]


def test_run_job_includes_task_inbox_for_goals(tmp_path, monkeypatch):
    """Verify the task_inbox key is passed in payload for goals job."""
    from tests.conftest import make_parallel_job_response

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    captured = []

    def fake_post(url, payload, token, timeout):
        captured.append(payload)
        return make_parallel_job_response("goals-content")

    job = next(j for j in JOBS if j["name"] == "goals")
    extraction = {"raw_goals": [{"title": "Q3 goals"}]}
    task_inbox = {"tasks": [{"title": "test task"}], "open_count": 1}

    with mock.patch("memcli.gateway_client.post_json", side_effect=fake_post):
        run_job(job, extraction, tmp_path, task_inbox)

    assert len(captured) == 1
    assert "task_inbox" in captured[0]["args"]["input"]


# ── run() integration ─────────────────────────────────────────────────────

def test_main_all_jobs_succeed(
    tmp_path, monkeypatch, fake_extraction_file, fake_task_inbox, tmp_memory_dir
):
    from tests.conftest import make_parallel_job_response

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    def fake_gateway(url, payload, token, timeout):
        inp = payload["args"]["input"]
        if "raw_patterns" in inp:
            return make_parallel_job_response("insights-content")
        if "task_inbox" in inp and "raw_goals" in inp:
            return make_parallel_job_response("goals-content")
        if "task_inbox" in inp:
            return make_parallel_job_response("tasks-content")
        return make_parallel_job_response("hot-memory-content")

    with mock.patch("memcli.gateway_client.post_json", side_effect=fake_gateway):
        result = run(
            extraction_file=fake_extraction_file,
            task_inbox_file=fake_task_inbox,
            memory_path=tmp_memory_dir,
        )

    for job_name in ("insights", "goals", "tasks", "hot_memory"):
        assert result[job_name]["ok"] is True, f"{job_name} should be ok"


def test_main_failed_job_does_not_block_others(
    tmp_path, monkeypatch, fake_extraction_file, fake_task_inbox, tmp_memory_dir
):
    from tests.conftest import make_parallel_job_response

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    def fake_gateway(url, payload, token, timeout):
        inp = payload["args"]["input"]
        if "raw_patterns" in inp:
            raise RuntimeError("insights gateway error")
        return make_parallel_job_response("ok-content")

    with mock.patch("memcli.gateway_client.post_json", side_effect=fake_gateway):
        result = run(
            extraction_file=fake_extraction_file,
            task_inbox_file=fake_task_inbox,
            memory_path=tmp_memory_dir,
        )

    assert result["insights"]["ok"] is False
    assert result["goals"]["ok"] is True
    assert result["tasks"]["ok"] is True
    assert result["hot_memory"]["ok"] is True
