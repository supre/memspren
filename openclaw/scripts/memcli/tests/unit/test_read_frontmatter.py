"""Unit tests for memcli.scanning.read_frontmatter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from memcli.log import make_logger
from memcli.scanning.read_frontmatter import CLASSIFIER_FOLDER_MAP, run, read_frontmatter

_log = make_logger("test")


def _write_md(path: Path, frontmatter: dict, body: str = "") -> None:
    """Write a markdown file with YAML frontmatter."""
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    if body:
        lines.append(body)
    path.write_text("\n".join(lines), encoding="utf-8")


# ── read_frontmatter function ──────────────────────────────────────────────

def test_read_frontmatter_extracts_fields(tmp_path):
    md = tmp_path / "test.md"
    _write_md(md, {"description": "A test file", "node_type": "project", "status": "active"})
    result = read_frontmatter(md)
    assert result["description"] == "A test file"
    assert result["node_type"] == "project"
    assert result["status"] == "active"


def test_read_frontmatter_missing_file_returns_empty(tmp_path):
    result = read_frontmatter(tmp_path / "nonexistent.md")
    assert result == {}


def test_read_frontmatter_no_frontmatter_returns_empty(tmp_path):
    md = tmp_path / "plain.md"
    md.write_text("Just plain body text\n", encoding="utf-8")
    result = read_frontmatter(md)
    assert result == {}


# ── classifier mapping ─────────────────────────────────────────────────────

def test_classifier_folder_map_has_key_classifiers():
    assert "project:personal" in CLASSIFIER_FOLDER_MAP
    assert "idea" in CLASSIFIER_FOLDER_MAP
    assert "people" in CLASSIFIER_FOLDER_MAP
    assert "learning" in CLASSIFIER_FOLDER_MAP


# ── run() ──────────────────────────────────────────────────────────────────

def test_main_scans_classifier_folder(tmp_path):
    vault = tmp_path / "vault"
    projects_dir = vault / "Work" / "Projects"
    projects_dir.mkdir(parents=True)
    _write_md(projects_dir / "my-project.md", {
        "description": "An exciting project",
        "node_type": "project",
        "status": "active",
    })

    result = run(
        vault_path=vault,
        classifiers='["project:personal"]',
        log=_log,
    )

    assert result["count"] == 1
    run_dir = vault / ".second-brain" / "run"
    assert (run_dir / "frontmatter.json").exists()

    items = json.loads((run_dir / "frontmatter.json").read_text())
    assert items[0]["description"] == "An exciting project"


def test_main_empty_folder_returns_zero_count(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    result = run(
        vault_path=vault,
        classifiers='["idea"]',
        log=_log,
    )

    assert result["count"] == 0
