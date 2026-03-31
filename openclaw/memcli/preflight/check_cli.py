"""
check_cli.py — Verify obsidian-cli availability and resolve the write mode.

Two modes:
  json_mode=True  (pipeline): returns {write_mode, vault_name, last_sync}
  json_mode=False (diagnostic): prints human-readable checks, raises on failure
"""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import state


def print_path_fix():
    """Print platform-specific instructions for adding `obsidian` to PATH."""
    os_name = platform.system()
    print("", file=sys.stderr)
    print("To fix: add the Obsidian CLI to your PATH.", file=sys.stderr)
    if os_name == "Darwin":
        print("  macOS — add to ~/.zprofile (or ~/.bash_profile):", file=sys.stderr)
        print('    export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"', file=sys.stderr)
        print("  Then run: source ~/.zprofile", file=sys.stderr)
    elif os_name == "Linux":
        print("  Linux — create a symlink:", file=sys.stderr)
        print("    sudo ln -s /path/to/obsidian /usr/local/bin/obsidian", file=sys.stderr)
        print("  Or add the directory to ~/.bashrc / ~/.profile.", file=sys.stderr)
        print("  Snap install? Try: sudo snap alias obsidian obsidian", file=sys.stderr)
    elif os_name == "Windows":
        print("  Windows — add the Obsidian install directory to your system PATH", file=sys.stderr)
        print("  via System Properties → Environment Variables.", file=sys.stderr)
    else:
        print(f"  ({os_name}) Add the Obsidian binary directory to your PATH.", file=sys.stderr)


def check_in_path() -> bool:
    if shutil.which("obsidian") is None:
        print("✗ ERROR: `obsidian` command not found in PATH.", file=sys.stderr)
        print_path_fix()
        return False
    print("✓ `obsidian` found in PATH.")
    return True


def check_running() -> bool:
    try:
        result = subprocess.run(
            ["obsidian", "version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ Obsidian CLI reachable. {version}")
            return True
        else:
            print("✗ ERROR: `obsidian version` returned a non-zero exit code.", file=sys.stderr)
            print("  Please open Obsidian and try again.", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ ERROR: `obsidian version` timed out.", file=sys.stderr)
        print("  Please open Obsidian and try again.", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("✗ ERROR: `obsidian` not found when running version check.", file=sys.stderr)
        return False


def check_vault(vault_name: str) -> bool:
    try:
        result = subprocess.run(
            ["obsidian", f"vault={vault_name}", "files"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print(f"✓ Vault \"{vault_name}\" is accessible.")
            return True
        else:
            stderr = result.stderr.strip()
            print(f"✗ ERROR: Could not access vault \"{vault_name}\".", file=sys.stderr)
            if stderr:
                print(f"  {stderr}", file=sys.stderr)
            print(
                f"  Check that the vault name exactly matches what appears in "
                f"Obsidian → Manage vaults.",
                file=sys.stderr,
            )
            print("  Please open Obsidian and try again.", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ ERROR: Vault check for \"{vault_name}\" timed out.", file=sys.stderr)
        print("  Please open Obsidian and try again.", file=sys.stderr)
        return False


def read_last_sync(vault_path: str | None) -> str | None:
    if not vault_path:
        return None
    state_path = Path(vault_path) / ".second-brain" / "Memory" / "system-state.md"
    try:
        content = state_path.read_text(encoding="utf-8")
        m = re.search(r"^last_sync:\s*(.+)$", content, re.MULTILINE)
        if m:
            val = m.group(1).strip()
            return val if val and val.lower() not in ("null", "none", "") else None
    except Exception:
        pass
    return None


def cli_is_available(vault_name: str | None = None) -> bool:
    if shutil.which("obsidian") is None:
        return False
    try:
        result = subprocess.run(
            ["obsidian", "version"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
    except Exception:
        return False
    if vault_name:
        try:
            result = subprocess.run(
                ["obsidian", f"vault={vault_name}", "files"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
    return True


def run(
    *,
    vault_path: Path,
    vault_name: str = "",
    memory_path: Path | None = None,
    json_mode: bool = True,
) -> dict:
    if json_mode:
        if not vault_name:
            print(
                json.dumps({"warn": "no vault_name supplied in pipeline mode; forcing filesystem write mode"}),
                file=sys.stderr,
            )

        cli_ok = cli_is_available(vault_name) if vault_name else False
        write_mode = "obsidian" if cli_ok else "filesystem"
        last_sync = read_last_sync(str(vault_path))

        result = {
            "write_mode": write_mode,
            "vault_name": vault_name or "",
            "last_sync": last_sync,
        }

        if memory_path:
            state.write_state(str(memory_path), {
                "check_cli_vault_name": vault_name or "",
                "check_cli_write_mode": write_mode,
                "check_cli_last_sync": last_sync,
            })
        return result

    # Diagnostic mode
    print("--- Obsidian CLI Check ---")
    if not check_in_path():
        raise RuntimeError("obsidian command not found in PATH")
    if not check_running():
        raise RuntimeError("obsidian CLI not reachable")
    if vault_name:
        if not check_vault(vault_name):
            raise RuntimeError(f"vault '{vault_name}' not accessible")
    print("--- All checks passed ---")
    return {"ok": True, "write_mode": "obsidian", "vault_name": vault_name}
