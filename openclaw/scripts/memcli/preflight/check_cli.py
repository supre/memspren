"""check_cli.py — Verify obsidian-cli availability, resolve write mode, ensure directory structure."""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import state
from ..log import Logger
from ..paths import VaultPaths


def print_path_fix():
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
    elif os_name == "Windows":
        print("  Windows — add the Obsidian install directory to your system PATH", file=sys.stderr)
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
            ["obsidian", "version"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ Obsidian CLI reachable. {version}")
            return True
        else:
            print("✗ ERROR: `obsidian version` returned a non-zero exit code.", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ ERROR: `obsidian version` timed out.", file=sys.stderr)
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
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ ERROR: Vault check for \"{vault_name}\" timed out.", file=sys.stderr)
        return False


def read_last_sync(memory_path: Path) -> str | None:
    state_path = memory_path / "system-state.md"
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
    json_mode: bool = True,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)

    if json_mode:
        # Ensure directory structure exists
        paths.ensure()
        log.info("directory structure ensured", base=str(paths.base))

        if not vault_name:
            log.warn("no vault_name supplied; forcing filesystem write mode")

        cli_ok = cli_is_available(vault_name) if vault_name else False
        write_mode = "obsidian" if cli_ok else "filesystem"
        last_sync = read_last_sync(paths.memory)

        log.info("check-cli result", write_mode=write_mode, last_sync=str(last_sync))

        result = {
            "write_mode": write_mode,
            "vault_name": vault_name or "",
            "last_sync": last_sync,
        }

        state.write_state(str(paths.run), {
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
