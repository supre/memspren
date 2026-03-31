"""
Shared pytest fixtures for memcli tests.

All tests that need file I/O or Gateway mocking should use these fixtures
instead of rolling their own tmp dirs / patches.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock

import pytest


# ── Directory fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def tmp_memory_dir(tmp_path: Path) -> Path:
    """Creates Memory/ with run/ subdir and seed memory files."""
    mem = tmp_path / "Memory"
    run = mem / "run"
    run.mkdir(parents=True)
    for fname in ("insights.md", "goals.md", "tasks.md", "hot-memory.md"):
        (mem / fname).write_text(f"Existing {fname}", encoding="utf-8")
    return mem


@pytest.fixture
def tmp_vault_dir(tmp_path: Path) -> Path:
    """Creates a minimal vault directory."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


# ── Input file fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def fake_buffer_files(tmp_memory_dir: Path):
    """Writes buffer-content.txt and manual-edits.txt in run/."""
    run = tmp_memory_dir / "run"
    buf = run / "buffer-content.txt"
    edits = run / "manual-edits.txt"
    buf.write_text("Daily reflection content for testing.", encoding="utf-8")
    edits.write_text("Manual edit: updated project status.", encoding="utf-8")
    return buf, edits


@pytest.fixture
def fake_extraction_output() -> dict:
    """Realistic extraction output dict (no file I/O)."""
    return {
        "raw_insights": [{"summary": "Need better async patterns", "category": "technical"}],
        "raw_goals": [{"title": "Ship v2 by Q3", "timeframe": "quarter"}],
        "raw_tasks": [{"title": "Write unit tests", "priority": "high"}],
        "raw_patterns": [{"pattern": "Procrastination on testing", "frequency": "recurring"}],
        "classifiers": ["project:personal", "learning"],
    }


@pytest.fixture
def fake_task_inbox(tmp_memory_dir: Path) -> Path:
    """Writes task-inbox.json to run/ and returns its path."""
    run = tmp_memory_dir / "run"
    data = {
        "tasks": [{"title": "Write unit tests", "status": "open", "completed_date": None}],
        "completed": [],
        "open_count": 1,
    }
    f = run / "task-inbox.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


@pytest.fixture
def fake_extraction_file(tmp_memory_dir: Path, fake_extraction_output: dict) -> Path:
    """Writes extraction-output.json to run/ and returns its path."""
    run = tmp_memory_dir / "run"
    f = run / "extraction-output.json"
    f.write_text(json.dumps(fake_extraction_output), encoding="utf-8")
    return f


# ── Gateway mock fixtures ───────────────────────────────────────────────────

@pytest.fixture
def mock_gateway():
    """Patches gateway_client.post_json for the duration of the test."""
    with mock.patch("memcli.gateway_client.post_json") as m:
        yield m


@pytest.fixture
def gateway_env(monkeypatch):
    """Sets OPENCLAW_URL and OPENCLAW_TOKEN env vars."""
    monkeypatch.setenv("OPENCLAW_URL", "http://gateway.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "test-token")


# ── Fake gateway response builders ─────────────────────────────────────────

def make_extraction_response(payload: dict) -> dict:
    """Wraps a dict as the nested response structure run_extraction.py expects."""
    return {
        "result": {
            "content": [{"type": "text", "text": json.dumps(payload)}]
        }
    }


def make_parallel_job_response(content: str) -> dict:
    """Wraps a content string as the nested response structure parallel_memory.py expects."""
    return {
        "result": {
            "details": {
                "json": {"content": content}
            }
        }
    }
