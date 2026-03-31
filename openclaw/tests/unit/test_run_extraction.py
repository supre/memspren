"""Unit tests for memcli.extraction.run_extraction."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from memcli.log import make_logger
from memcli.extraction.run_extraction import run

_log = make_logger("test")


def test_extraction_success(tmp_vault_dir, monkeypatch, fake_buffer_files, fake_extraction_output):
    """Gateway returns valid extraction JSON; it should be returned and saved to file."""
    from tests.conftest import make_extraction_response

    buf_file, edits_file = fake_buffer_files
    vault = tmp_vault_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("memcli.gateway_client.post_json",
                    return_value=make_extraction_response(fake_extraction_output)):
        result = run(
            buffer_content_file=buf_file,
            manual_edits_file=edits_file,
            vault_path=vault,
            log=_log,
        )

    assert result["raw_insights"] == fake_extraction_output["raw_insights"]
    assert (vault / ".second-brain" / "run" / "extraction-output.json").exists()


def test_missing_buffer_file_exits_1(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    with pytest.raises(RuntimeError, match="Buffer file not found"):
        run(
            buffer_content_file=tmp_path / "missing.txt",
            manual_edits_file=tmp_path / "edits.txt",
            vault_path=vault,
            log=_log,
        )


def test_gateway_error_exits_1(tmp_vault_dir, monkeypatch, fake_buffer_files):
    buf_file, edits_file = fake_buffer_files
    vault = tmp_vault_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("memcli.gateway_client.post_json",
                    side_effect=RuntimeError("Gateway HTTP 500: server error")):
        with pytest.raises(RuntimeError, match="Gateway HTTP 500"):
            run(
                buffer_content_file=buf_file,
                manual_edits_file=edits_file,
                vault_path=vault,
                log=_log,
            )


def test_extraction_saves_to_run_dir(tmp_vault_dir, monkeypatch, fake_buffer_files, fake_extraction_output):
    from tests.conftest import make_extraction_response

    buf_file, edits_file = fake_buffer_files
    vault = tmp_vault_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("memcli.gateway_client.post_json",
                    return_value=make_extraction_response(fake_extraction_output)):
        run(
            buffer_content_file=buf_file,
            manual_edits_file=edits_file,
            vault_path=vault,
            log=_log,
        )

    saved = json.loads((vault / ".second-brain" / "run" / "extraction-output.json").read_text())
    assert saved["classifiers"] == fake_extraction_output["classifiers"]


def test_missing_prompt_file_exits_1(tmp_vault_dir, monkeypatch, fake_buffer_files):
    """If prompts/extraction_prompt.txt doesn't exist the script should fail gracefully."""
    buf_file, edits_file = fake_buffer_files
    vault = tmp_vault_dir

    monkeypatch.setenv("OPENCLAW_URL", "http://gw.test")
    monkeypatch.setenv("OPENCLAW_TOKEN", "tok")

    with mock.patch("memcli.extraction.run_extraction.PROMPTS_DIR", vault / "noprompts"):
        with pytest.raises(RuntimeError, match="Prompt file not found"):
            run(
                buffer_content_file=buf_file,
                manual_edits_file=edits_file,
                vault_path=vault,
                log=_log,
            )
