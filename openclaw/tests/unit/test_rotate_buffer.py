"""Unit tests for memcli.buffer.rotate_buffer."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from memcli.buffer.rotate_buffer import (
    count_words,
    create_buffer,
    list_sealed,
    parse_frontmatter,
    read_active_id,
    rotate,
    seal_buffer,
    sync_check,
    write_active_id,
)


def _make_vault(tmp_path: Path) -> tuple[Path, str, str]:
    """Create vault layout and return (vault, buffers_dir, run_path) strings."""
    vault = tmp_path / "vault"
    vault.mkdir()
    sb = vault / ".second-brain"
    buffers = sb / "buffers"
    run = sb / "run"
    buffers.mkdir(parents=True)
    run.mkdir(parents=True)
    return vault, str(buffers), str(run)


# ── parse_frontmatter ──────────────────────────────────────────────────────

def test_parse_frontmatter_extracts_fields():
    content = "---\nstate: active\nbuffer_id: \"001\"\nentry_count: 5\n---\nBody text"
    result = parse_frontmatter(content)
    assert result["state"] == "active"
    assert result["buffer_id"] == "001"
    assert result["entry_count"] == "5"


def test_parse_frontmatter_empty_without_delimiters():
    assert parse_frontmatter("No frontmatter here") == {}


# ── count_words ────────────────────────────────────────────────────────────

def test_count_words_excludes_frontmatter():
    content = "---\nstate: active\n---\nHello world test"
    assert count_words(content) == 3


def test_count_words_no_frontmatter():
    assert count_words("one two three") == 3


# ── create_buffer / read_active_id ─────────────────────────────────────────

def test_create_buffer_sets_active_id(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    create_buffer(buffers_dir, "001")
    assert read_active_id(buffers_dir) == "001"


def test_create_buffer_writes_correct_id(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    path = create_buffer(buffers_dir, "003")
    content = Path(path).read_text()
    assert 'buffer_id: "003"' in content
    assert "state: active" in content


# ── seal_buffer ────────────────────────────────────────────────────────────

def test_seal_buffer_marks_state(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    create_buffer(buffers_dir, "001")
    result = seal_buffer(buffers_dir, "001")
    assert result["state"] == "sealed"

    # Confirm file updated
    buf_path = Path(buffers_dir) / "sync-buffer-001.md"
    content = buf_path.read_text()
    assert "state: sealed" in content


def test_seal_buffer_missing_returns_error(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    result = seal_buffer(buffers_dir, "999")
    assert "error" in result


# ── rotate ─────────────────────────────────────────────────────────────────

def test_rotate_initializes_when_no_active(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    result = rotate(buffers_dir)
    assert result["action"] == "initialized"
    assert result["new_active"] == "001"


def test_rotate_seals_current_and_creates_new(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    create_buffer(buffers_dir, "001")
    result = rotate(buffers_dir)
    assert result["action"] == "rotated"
    assert result["sealed"] == "001"
    assert result["new_active"] == "002"


# ── list_sealed ────────────────────────────────────────────────────────────

def test_list_sealed_returns_only_sealed(tmp_path):
    _, buffers_dir, _ = _make_vault(tmp_path)
    create_buffer(buffers_dir, "001")
    # No sealed buffers yet
    assert list_sealed(buffers_dir) == []

    seal_buffer(buffers_dir, "001")
    sealed = list_sealed(buffers_dir)
    assert len(sealed) == 1
    assert sealed[0]["buffer_id"] == "001"
    assert sealed[0]["state"] == "sealed"


# ── sync_check ─────────────────────────────────────────────────────────────

def test_sync_check_empty_vault_returns_no_content(tmp_path):
    _, buffers_dir, run_path = _make_vault(tmp_path)
    result = sync_check(buffers_dir, run_path)
    assert result["has_content"] is False
    assert result["should_exit"] is True
    assert result["sealed_buffers"] == []


def test_sync_check_writes_buffer_content_file(tmp_path):
    _, buffers_dir, run_path = _make_vault(tmp_path)

    # Create and seal a buffer with content
    buf_path = create_buffer(buffers_dir, "001")
    # Write some body content
    content = Path(buf_path).read_text()
    Path(buf_path).write_text(
        content.replace("entry_count: 0", "entry_count: 2") + "\nSome brain dump content here.\n"
    )
    seal_buffer(buffers_dir, "001")

    result = sync_check(buffers_dir, run_path)
    assert result["has_content"] is True
    assert result["buffer_content_file"] != ""
    assert Path(result["buffer_content_file"]).exists()
