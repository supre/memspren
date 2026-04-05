"""CLI integration tests for the `setup` and `get-active-buffer` commands."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def run_cmd(args: list[str], cwd: str = None) -> tuple[int, dict]:
    """Invoke `uv run -m scripts.memcli <args>` and return (returncode, json_output)."""
    skill_root = Path(__file__).resolve().parents[4]  # openclaw/
    cmd = [sys.executable, "-m", "scripts.memcli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(skill_root),
    )
    try:
        output = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        output = {"raw_stdout": result.stdout, "raw_stderr": result.stderr}
    return result.returncode, output


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return vault


# ── setup command ──────────────────────────────────────────────────────────

class TestSetupCommand:
    def test_setup_returns_ok(self, tmp_vault):
        code, out = run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        assert code == 0, f"Non-zero exit: {out}"
        assert out.get("ok") is True

    def test_setup_creates_vault_folders(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        assert (tmp_vault / "Work" / "Projects").is_dir()
        assert (tmp_vault / "People").is_dir()
        assert (tmp_vault / "Tasks").is_dir()

    def test_setup_creates_second_brain_dirs(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        sb = tmp_vault / ".second-brain"
        assert (sb / "memory").is_dir()
        assert (sb / "buffers").is_dir()
        assert (sb / "run").is_dir()

    def test_setup_idempotent(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        code, out = run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        assert code == 0
        assert out.get("ok") is True
        assert out.get("folders_created") == []

    def test_setup_reports_git_initialized(self, tmp_vault):
        code, out = run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        assert out.get("git_initialized") is True


# ── get-active-buffer command ──────────────────────────────────────────────

class TestGetActiveBufferCommand:
    def test_returns_path_and_entry_count(self, tmp_vault):
        # Need vault structure first
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        code, out = run_cmd(["get-active-buffer", "--vault-path", str(tmp_vault)])
        assert code == 0, f"Non-zero exit: {out}"
        assert "path" in out
        assert "entry_count" in out
        assert "rotated" in out

    def test_creates_buffer_if_none_exists(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        code, out = run_cmd(["get-active-buffer", "--vault-path", str(tmp_vault)])
        assert code == 0
        assert Path(out["path"]).exists()

    def test_returns_rotated_false_on_first_call(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        _, out = run_cmd(["get-active-buffer", "--vault-path", str(tmp_vault)])
        assert out["rotated"] is False

    def test_rotates_when_over_word_limit(self, tmp_vault):
        run_cmd(["setup", "--vault-path", str(tmp_vault), "--vault-name", "TestVault"])
        # Get the active buffer path and stuff it with words
        _, out = run_cmd(["get-active-buffer", "--vault-path", str(tmp_vault)])
        buf_path = Path(out["path"])
        buf_path.write_text(
            buf_path.read_text() + "\n" + " ".join(["word"] * 20) + "\n",
            encoding="utf-8"
        )
        # Now request with tiny max-words limit
        _, out2 = run_cmd(["get-active-buffer", "--vault-path", str(tmp_vault), "--max-words", "5"])
        assert out2["rotated"] is True
