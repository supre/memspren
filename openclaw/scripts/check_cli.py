#!/usr/bin/env python3
"""
check_cli.py — Verify obsidian-cli availability and resolve the write mode.

Used in two ways:

1. Human/diagnostic mode (default):
   python scripts/check_cli.py [--vault "My Vault"]
   Prints human-readable check results. Exit 0 = all passed, 1 = failed.

2. Lobster pipeline mode (--json):
   python scripts/check_cli.py --vault-path /path/to/vault --json
   Emits a single JSON object to stdout. Never prints other text to stdout.
   Output: { "write_mode": "obsidian"|"filesystem", "vault_name": str, "last_sync": str|null }
   write_mode is "obsidian" if CLI is available and Obsidian is running,
   "filesystem" otherwise (non-fatal fallback for the pipeline).
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Import state module
sys.path.insert(0, os.path.dirname(__file__))
import state


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
    """Check 1: Is `obsidian` available in PATH?"""
    if shutil.which("obsidian") is None:
        print("✗ ERROR: `obsidian` command not found in PATH.", file=sys.stderr)
        print_path_fix()
        return False
    print("✓ `obsidian` found in PATH.")
    return True


def check_running() -> bool:
    """Check 2: Is Obsidian running and the CLI reachable?"""
    try:
        result = subprocess.run(
            ["obsidian", "version"],
            capture_output=True,
            text=True,
            timeout=5,
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
        # Should have been caught by check_in_path, but handle gracefully.
        print("✗ ERROR: `obsidian` not found when running version check.", file=sys.stderr)
        return False


def check_vault(vault_name: str) -> bool:
    """Check 3: Does the named vault exist and respond to CLI queries?"""
    try:
        result = subprocess.run(
            ["obsidian", f"vault={vault_name}", "files"],
            capture_output=True,
            text=True,
            timeout=10,
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
    """Read last_sync timestamp from system-state.md, or None if not found."""
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
    """Return True if obsidian-cli is reachable and (optionally) the vault is accessible."""
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


def main():
    parser = argparse.ArgumentParser(
        description="Verify Obsidian CLI availability and vault accessibility."
    )
    parser.add_argument(
        "--vault",
        metavar="NAME",
        help='Vault name to validate (e.g. --vault "My Second Brain")',
    )
    parser.add_argument(
        "--vault-path",
        metavar="PATH",
        help="Vault filesystem path (used in pipeline mode to read last_sync)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="Emit JSON output for Lobster pipeline. Never prints to stdout except JSON.",
    )
    parser.add_argument(
        "--memory-path",
        help="Path to .second-brain/Memory (for writing shared state)",
    )
    args = parser.parse_args()

    # ── Pipeline / JSON mode ──────────────────────────────────────────────────
    if args.json_mode:
        vault_name = args.vault   # must be supplied via --vault; no folder-name fallback
        vault_path = args.vault_path

        if not vault_name:
            # No vault name supplied — cannot use obsidian-cli, force filesystem mode.
            # The workflow requires --vault to be passed; this path means misconfiguration.
            print(json.dumps({"warn": "no --vault supplied in pipeline mode; forcing filesystem write mode"}),
                  file=sys.stderr)

        cli_ok = cli_is_available(vault_name) if vault_name else False
        write_mode = "obsidian" if cli_ok else "filesystem"
        last_sync = read_last_sync(vault_path)

        result = {
            "write_mode": write_mode,
            "vault_name": vault_name or "",
            "last_sync":  last_sync,
        }
        print(json.dumps(result))
        
        # Write to shared state for subsequent steps
        if args.memory_path:
            state.write_state(args.memory_path, {
                "check_cli_vault_name": vault_name or "",
                "check_cli_write_mode": write_mode,
                "check_cli_last_sync": last_sync,
            })
        return

    # ── Human / diagnostic mode ───────────────────────────────────────────────
    print("--- Obsidian CLI Check ---")

    if not check_in_path():
        sys.exit(1)
    if not check_running():
        sys.exit(1)
    if args.vault:
        if not check_vault(args.vault):
            sys.exit(1)

    print("--- All checks passed ---")
    sys.exit(0)


if __name__ == "__main__":
    main()
