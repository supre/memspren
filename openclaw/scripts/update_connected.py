#!/usr/bin/env python3
"""
update_connected.py — Append a path to a vault file's `connected:` YAML array.

Reads the file via the Obsidian CLI, parses YAML frontmatter, deduplicates,
appends the new path, and writes the result back via CLI overwrite.

No filesystem fallback. If Obsidian is not running or the CLI call fails,
the script prints a clear error and exits with code 1.

Usage:
    python scripts/update_connected.py \\
        --vault "My Second Brain" \\
        --file  "Work/Projects/my-project.md" \\
        --add   "Log/Daily/2026-02-28.md"

    # Add multiple paths at once
    python scripts/update_connected.py \\
        --vault "My Second Brain" \\
        --file  "Work/Projects/my-project.md" \\
        --add   "Log/Daily/2026-02-28.md" \\
        --add   "People/jane-smith.md"
"""

import argparse
import subprocess
import sys
import re


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def run_obsidian(args: list[str], vault: str, timeout: int = 10) -> subprocess.CompletedProcess:
    """Run an obsidian CLI command and return the CompletedProcess result."""
    cmd = ["obsidian", f"vault={vault}"] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(
            f"✗ ERROR: obsidian CLI timed out running: {' '.join(cmd)}\n"
            "  Please open Obsidian and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError:
        print(
            "✗ ERROR: `obsidian` command not found.\n"
            "  Run `python scripts/check_cli.py` to diagnose.",
            file=sys.stderr,
        )
        sys.exit(1)


def read_file(vault: str, path: str) -> str:
    """Read a vault file's content via the CLI."""
    result = run_obsidian(["read", f"path={path}"], vault)
    if result.returncode != 0:
        err = result.stderr.strip()
        print(
            f"✗ ERROR: Could not read \"{path}\" from vault \"{vault}\".\n"
            f"  {err}\n"
            "  Please open Obsidian and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout


def write_file(vault: str, path: str, content: str) -> None:
    """Write (overwrite) a vault file's content via the CLI."""
    result = run_obsidian(
        ["create", f"path={path}", f"content={content}", "overwrite"],
        vault,
        timeout=15,
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        print(
            f"✗ ERROR: Could not write \"{path}\" to vault \"{vault}\".\n"
            f"  {err}\n"
            "  Please open Obsidian and try again.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (lightweight — no external deps)
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)", re.DOTALL)


def split_frontmatter(content: str) -> tuple[str, str]:
    """
    Split markdown content into (frontmatter_block, body).

    frontmatter_block includes the `---` delimiters.
    Returns ('', content) if no frontmatter is found.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return "", content
    fm_inner = match.group(1)
    body = match.group(2)
    return f"---\n{fm_inner}\n---\n", body


def parse_connected(frontmatter_block: str) -> list[str]:
    """
    Extract the values from the `connected:` YAML list.

    Handles both compact (`connected: []`) and block list forms.
    Returns an empty list if the field is absent or empty.
    """
    # Block list form:
    #   connected:
    #     - some/path.md
    #     - other/path.md
    block_match = re.search(
        r"^connected:\s*\n((?:[ \t]+-[^\n]*\n?)*)", frontmatter_block, re.MULTILINE
    )
    if block_match:
        items_str = block_match.group(1)
        return [
            line.strip().lstrip("- ").strip()
            for line in items_str.splitlines()
            if line.strip().startswith("-")
        ]

    # Inline empty form: `connected: []`
    inline_match = re.search(r"^connected:\s*\[\s*\]", frontmatter_block, re.MULTILINE)
    if inline_match:
        return []

    # Inline single-value form (edge case): `connected: some/path.md`
    single_match = re.search(r"^connected:\s*(\S+)", frontmatter_block, re.MULTILINE)
    if single_match:
        return [single_match.group(1)]

    return []


def set_connected(frontmatter_block: str, paths: list[str]) -> str:
    """
    Replace the `connected:` field in the frontmatter block with `paths`.

    Always writes in YAML block list form. If `connected:` did not exist,
    appends it before the closing `---`.
    """
    if not paths:
        new_value = "connected: []\n"
    else:
        items = "\n".join(f"  - {p}" for p in paths)
        new_value = f"connected:\n{items}\n"

    # Replace existing connected block (block or inline form)
    replaced = re.sub(
        r"^connected:.*?(?=\n\S|\n---)",
        new_value.rstrip("\n"),
        frontmatter_block,
        flags=re.MULTILINE | re.DOTALL,
    )

    if replaced != frontmatter_block:
        return replaced

    # `connected:` didn't exist — insert before closing `---`
    return re.sub(r"\n---\n?$", f"\n{new_value}---\n", frontmatter_block)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Append path(s) to a vault file's `connected:` YAML array."
    )
    parser.add_argument("--vault", required=True, metavar="NAME", help="Obsidian vault name")
    parser.add_argument(
        "--file", required=True, metavar="PATH", help="Vault-relative path of the file to update"
    )
    parser.add_argument(
        "--add",
        required=True,
        metavar="PATH",
        action="append",
        dest="additions",
        help="Vault-relative path to add (can be repeated)",
    )
    args = parser.parse_args()

    vault = args.vault
    file_path = args.file
    additions = args.additions

    # 1. Read current content
    content = read_file(vault, file_path)

    # 2. Parse frontmatter
    fm_block, body = split_frontmatter(content)
    if not fm_block:
        print(
            f"✗ ERROR: \"{file_path}\" has no YAML frontmatter.\n"
            "  Every vault file must start with --- frontmatter --- as per the skill rules.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Get existing connected list, deduplicate additions
    existing = parse_connected(fm_block)
    before_count = len(existing)
    for path in additions:
        if path not in existing:
            existing.append(path)
    added_count = len(existing) - before_count

    if added_count == 0:
        print(f"✓ No changes — all paths already present in connected: for \"{file_path}\".")
        sys.exit(0)

    # 4. Rebuild frontmatter
    new_fm = set_connected(fm_block, existing)
    new_content = new_fm + body

    # 5. Write back via CLI
    write_file(vault, file_path, new_content)

    added_paths = ", ".join(f'"{p}"' for p in additions if p not in existing[:before_count])
    print(
        f"✓ Updated connected: in \"{file_path}\" "
        f"(+{added_count} path{'s' if added_count != 1 else ''})."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
