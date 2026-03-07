#!/usr/bin/env python3
"""
check_cli.py — Verify that the Obsidian CLI is available and Obsidian is running.

Usage:
    python scripts/check_cli.py
    python scripts/check_cli.py --vault "My Vault"

Exit codes:
    0  All checks passed
    1  One or more checks failed (details printed to stderr)
"""

import argparse
import platform
import shutil
import subprocess
import sys


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


def main():
    parser = argparse.ArgumentParser(
        description="Verify Obsidian CLI availability and vault accessibility."
    )
    parser.add_argument(
        "--vault",
        metavar="NAME",
        help='Vault name to validate (e.g. --vault "My Second Brain")',
    )
    args = parser.parse_args()

    print("--- Obsidian CLI Check ---")

    # Check 1: PATH
    if not check_in_path():
        sys.exit(1)

    # Check 2: Obsidian running
    if not check_running():
        sys.exit(1)

    # Check 3: Vault (optional — only when --vault is provided)
    if args.vault:
        if not check_vault(args.vault):
            sys.exit(1)

    print("--- All checks passed ---")
    sys.exit(0)


if __name__ == "__main__":
    main()
