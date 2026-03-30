"""Unit tests for openclaw.scripts.extraction.run_extraction."""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from openclaw.scripts.extraction import run_extraction


def _run(args: list[str]) -> tuple[int, dict]:
    """Run run_extraction.main() with given args; return (exit_code, parsed_json)."""
    buf = io.StringIO()
    exit_code = 0
    with mock.patch.object(sys, "argv", ["run-extraction"] + args):
        with contextlib.redirect_stdout(buf):
            try:
                run_extraction.main()
            except SystemExit as e:
                exit_code = e.code or 0
    output = buf.getvalue().strip()
    result = json.loads(output) if output else {}
    return exit_code, result


def test_extraction_success(tmp_memory_dir, monkeypatch, fake_buffer_files, fake_extraction_output):
    """Gateway returns valid extraction JSON; it should be written to stdout and file."""
    from tests.conftest import make_extraction_response

    buf_file, edits_file = fake_buffer_files
    mem = tmp_memory_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("openclaw.scripts.gateway_client.post_json",
                    return_value=make_extraction_response(fake_extraction_output)):
        exit_code, result = _run([
            "--buffer-content-file", str(buf_file),
            "--manual-edits-file",   str(edits_file),
            "--memory-path",         str(mem),
        ])

    assert exit_code == 0
    assert result["raw_insights"] == fake_extraction_output["raw_insights"]
    assert (mem / "run" / "extraction-output.json").exists()


def test_missing_buffer_file_exits_1(tmp_path):
    exit_code, result = _run([
        "--buffer-content-file", str(tmp_path / "missing.txt"),
        "--manual-edits-file",   str(tmp_path / "edits.txt"),
        "--memory-path",         str(tmp_path),
    ])
    assert exit_code == 1
    assert result.get("ok") is False


def test_gateway_error_exits_1(tmp_memory_dir, monkeypatch, fake_buffer_files):
    buf_file, edits_file = fake_buffer_files
    mem = tmp_memory_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("openclaw.scripts.gateway_client.post_json",
                    side_effect=RuntimeError("Gateway HTTP 500: server error")):
        exit_code, result = _run([
            "--buffer-content-file", str(buf_file),
            "--manual-edits-file",   str(edits_file),
            "--memory-path",         str(mem),
        ])

    assert exit_code == 1
    assert result.get("ok") is False
    assert "Gateway HTTP 500" in result.get("error", "")


def test_extraction_saves_to_run_dir(tmp_memory_dir, monkeypatch, fake_buffer_files, fake_extraction_output):
    from tests.conftest import make_extraction_response

    buf_file, edits_file = fake_buffer_files
    mem = tmp_memory_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("openclaw.scripts.gateway_client.post_json",
                    return_value=make_extraction_response(fake_extraction_output)):
        _run([
            "--buffer-content-file", str(buf_file),
            "--manual-edits-file",   str(edits_file),
            "--memory-path",         str(mem),
        ])

    saved = json.loads((mem / "run" / "extraction-output.json").read_text())
    assert saved["classifiers"] == fake_extraction_output["classifiers"]


def test_missing_prompt_file_exits_1(tmp_memory_dir, monkeypatch, fake_buffer_files):
    """If prompts/extraction_prompt.txt doesn't exist the script should fail gracefully."""
    buf_file, edits_file = fake_buffer_files
    mem = tmp_memory_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    # Temporarily make PROMPTS_DIR point to an empty dir
    with mock.patch("openclaw.scripts.extraction.run_extraction.PROMPTS_DIR", tmp_memory_dir / "noprompts"):
        exit_code, result = _run([
            "--buffer-content-file", str(buf_file),
            "--manual-edits-file",   str(edits_file),
            "--memory-path",         str(mem),
        ])

    assert exit_code == 1
    assert result.get("ok") is False
