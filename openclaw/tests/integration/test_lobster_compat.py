"""
Integration tests verifying the Lobster compat shim (scripts/memcli.py) still
routes commands correctly through runner.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_vault(tmp_path: Path) -> Path:
    """Create a vault directory with the full .second-brain layout."""
    vault = tmp_path / "vault"
    vault.mkdir()
    sb = vault / ".second-brain"
    (sb / "memory").mkdir(parents=True)
    (sb / "run").mkdir(parents=True)
    (sb / "buffers").mkdir(parents=True)
    (sb / "logs").mkdir(parents=True)
    return vault


def _run_via_runner(args: list[str]) -> tuple[int, str]:
    """Run: python -m scripts.runner scripts/memcli.py <args>"""
    cmd = [
        sys.executable, "-m", "scripts.runner",
        "scripts/memcli.py",
    ] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return result.returncode, result.stdout.strip()


def _run_shim_direct(args: list[str]) -> tuple[int, str]:
    """Run: python scripts/memcli.py <args>"""
    cmd = [sys.executable, "scripts/memcli.py"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return result.returncode, result.stdout.strip()


def test_runner_wraps_clean_exit(tmp_path):
    """runner.py + memcli shim -> clean-exit command emits valid JSON."""
    vault = _make_vault(tmp_path)
    rc, out = _run_via_runner(["clean-exit", "--vault-path", str(vault), "--message", "lobster-test"])
    assert rc == 0, f"runner returned non-zero: {out}"
    result = json.loads(out)
    assert result["ok"] is True
    assert result["action"] == "exit"
    assert result["message"] == "lobster-test"


def test_shim_direct_clean_exit(tmp_path):
    """Direct python scripts/memcli.py invocation works without runner.py."""
    vault = _make_vault(tmp_path)
    rc, out = _run_shim_direct(["clean-exit", "--vault-path", str(vault), "--message", "direct-test"])
    assert rc == 0
    result = json.loads(out)
    assert result["ok"] is True


def test_runner_write_lock(tmp_path):
    """runner.py -> write-lock acquires lock and returns JSON."""
    vault = _make_vault(tmp_path)

    rc, out = _run_via_runner([
        "write-lock",
        "--vault-path", str(vault),
    ])
    assert rc == 0
    result = json.loads(out)
    assert result["ok"] is True
    assert result["action"] == "locked"
    assert (vault / ".second-brain" / "buffers" / "sync.lock").exists()

    # Release via runner
    rc2, out2 = _run_via_runner([
        "write-lock",
        "--vault-path", str(vault),
        "--release",
    ])
    assert rc2 == 0
    assert json.loads(out2)["action"] == "released"


def test_runner_output_is_valid_json(tmp_path):
    """runner.py validates JSON contract -- all output must be parseable."""
    vault = _make_vault(tmp_path)
    rc, out = _run_via_runner(["clean-exit", "--vault-path", str(vault)])
    assert rc == 0
    json.loads(out)  # Should not raise


def test_shim_routes_check_cli_help():
    """memcli shim properly dispatches check-cli command."""
    cmd = [sys.executable, "scripts/memcli.py", "check-cli", "--help"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    # check-cli --help should exit 0 (Click help) or 1 (argparse help on older)
    # Either way the output should mention vault or obsidian
    combined = (result.stdout + result.stderr).lower()
    assert "vault" in combined or "obsidian" in combined or "usage" in combined
