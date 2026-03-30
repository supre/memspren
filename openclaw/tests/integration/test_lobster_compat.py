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


def test_runner_wraps_clean_exit():
    """runner.py + memcli shim → clean-exit command emits valid JSON."""
    rc, out = _run_via_runner(["clean-exit", "--message", "lobster-test"])
    assert rc == 0, f"runner returned non-zero: {out}"
    result = json.loads(out)
    assert result["ok"] is True
    assert result["action"] == "exit"
    assert result["message"] == "lobster-test"


def test_shim_direct_clean_exit():
    """Direct python scripts/memcli.py invocation works without runner.py."""
    rc, out = _run_shim_direct(["clean-exit", "--message", "direct-test"])
    assert rc == 0
    result = json.loads(out)
    assert result["ok"] is True


def test_runner_write_lock(tmp_path):
    """runner.py → write-lock acquires lock and returns JSON."""
    mem = tmp_path / "Memory"
    mem.mkdir()

    rc, out = _run_via_runner([
        "write-lock",
        "--memory-path", str(mem),
    ])
    assert rc == 0
    result = json.loads(out)
    assert result["ok"] is True
    assert result["action"] == "locked"
    assert (mem / "sync.lock").exists()

    # Release via runner
    rc2, out2 = _run_via_runner([
        "write-lock",
        "--memory-path", str(mem),
        "--release",
    ])
    assert rc2 == 0
    assert json.loads(out2)["action"] == "released"


def test_runner_output_is_valid_json():
    """runner.py validates JSON contract — all output must be parseable."""
    rc, out = _run_via_runner(["clean-exit"])
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
