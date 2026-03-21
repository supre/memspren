#!/usr/bin/env python3
"""
scan_descriptions.py — Extract frontmatter descriptions from vault files.

Scans a folder in the Obsidian vault and returns structured metadata
(description, node_type, status, last_modified) for each file.
Used by the agent to find similar/duplicate files before creating new ones.

Usage:
    python3 scripts/scan_descriptions.py --vault "VaultName" --folder "Vision"
    python3 scripts/scan_descriptions.py --vault "VaultName" --folder "Work/Ideas"

Output: JSON array to stdout
"""

import argparse
import json
import subprocess
import sys
import re
import os


def run_obsidian_cli(vault: str, *args) -> str:
    """Run an obsidian-cli command and return stdout."""
    cmd = ["obsidian", f'vault={vault}'] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def list_files_in_folder(vault: str, folder: str) -> list:
    """List markdown files in a vault folder using obsidian-cli search."""
    # Use obsidian-cli to search for files in the folder
    # Fall back to filesystem if search doesn't work for folder listing
    vault_path = get_vault_path(vault)
    if not vault_path:
        return []

    folder_path = os.path.join(vault_path, folder)
    if not os.path.isdir(folder_path):
        return []

    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            if f.endswith('.md') and not f.startswith('.'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, vault_path)
                files.append(rel_path)
    return files


def get_vault_path(vault: str) -> str:
    """Get vault path from obsidian-cli or common locations."""
    # Try obsidian-cli first
    result = run_obsidian_cli(vault, "vault:path")
    if result:
        return result.strip()

    # Fall back to home directory search
    home = os.path.expanduser("~")
    common_paths = [
        os.path.join(home, vault),
        os.path.join(home, "Documents", vault),
    ]
    for p in common_paths:
        if os.path.isdir(p) and os.path.isdir(os.path.join(p, ".obsidian")):
            return p
    return ""


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content. Only reads until closing ---."""
    if not content.startswith('---'):
        return {}

    # Find closing ---
    end = content.find('---', 3)
    if end == -1:
        return {}

    yaml_block = content[3:end].strip()
    result = {}

    for line in yaml_block.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('-'):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ('description', 'node_type', 'status', 'last_modified', 'created'):
                result[key] = value if value else None

    return result


def read_frontmatter_only(vault: str, file_path: str) -> str:
    """Read a file from the vault, return content up to closing frontmatter ---."""
    content = run_obsidian_cli(vault, "read", f"path={file_path}")
    if not content:
        # Fall back to direct file read
        vault_path = get_vault_path(vault)
        if vault_path:
            full_path = os.path.join(vault_path, file_path)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError):
                return ""

    if not content or not content.startswith('---'):
        return ""

    # Only return up to closing ---
    end = content.find('---', 3)
    if end == -1:
        return content
    return content[:end + 3]


def scan_folder(vault: str, folder: str) -> list:
    """Scan a folder and return descriptions for all files."""
    files = list_files_in_folder(vault, folder)
    results = []

    for file_path in files:
        frontmatter_text = read_frontmatter_only(vault, file_path)
        meta = parse_frontmatter(frontmatter_text)

        results.append({
            "path": file_path,
            "description": meta.get("description"),
            "node_type": meta.get("node_type"),
            "status": meta.get("status"),
            "last_modified": meta.get("last_modified") or meta.get("created"),
        })

    return results


def scan_folder_by_path(vault_path: str, folder: str) -> list:
    """Scan a folder using direct vault path and return descriptions for all files."""
    folder_path = os.path.join(vault_path, folder)
    if not os.path.isdir(folder_path):
        return []

    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            if f.endswith('.md') and not f.startswith('.'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, vault_path)
                files.append(rel_path)

    results = []
    for file_path in files:
        full = os.path.join(vault_path, file_path)
        try:
            with open(full, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Only need frontmatter
        except (FileNotFoundError, PermissionError):
            continue

        meta = parse_frontmatter(content)
        results.append({
            "path": file_path,
            "description": meta.get("description"),
            "node_type": meta.get("node_type"),
            "status": meta.get("status"),
            "last_modified": meta.get("last_modified") or meta.get("created"),
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scan vault folder and extract frontmatter descriptions"
    )
    parser.add_argument("--vault", help="Obsidian vault name (uses obsidian-cli)")
    parser.add_argument("--vault-path", help="Direct path to vault (no obsidian-cli needed)")
    parser.add_argument("--folder", required=True, help="Folder to scan (relative to vault root)")
    args = parser.parse_args()

    if args.vault_path:
        results = scan_folder_by_path(args.vault_path, args.folder)
    elif args.vault:
        results = scan_folder(args.vault, args.folder)
    else:
        print(json.dumps({"error": "provide --vault or --vault-path"}))
        sys.exit(1)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
