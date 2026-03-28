#!/usr/bin/env python3
"""
read_frontmatter.py — Batch-read YAML frontmatter from classifier-scoped vault folders.

Reads only frontmatter (not body) for all files in the folders relevant to this sync's
classifiers. Fast and low-token — drives merge detection in the entity plan step.

Returns JSON to stdout:
[{ "path": str, "description": str, "status": str, "node_type": str }, ...]
"""

import argparse
import json
import sys
from pathlib import Path

# Maps classifier strings to vault folder paths (relative to vault root)
CLASSIFIER_FOLDER_MAP: dict[str, str] = {
    "project:personal": "Work/Projects",
    "project:work":     "Work/Projects",
    "idea":             "Work/Ideas",
    "people":           "People",
    "learning":         "Notes/Learnings",
    "log":              "Log/Daily",
    "pattern":          "Notes/Patterns",
    "relationship":     "People",
    "vision":           "Vision",
    "strategy":         "Strategy",
    "kt":               "Work/KT",
}


def read_frontmatter(file_path: Path) -> dict:
    """Extract YAML frontmatter fields from a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    result: dict[str, str] = {}
    for line in content[3:end].strip().splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"').strip("'")

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--classifiers", required=True,
                        help="JSON array or comma-separated list of classifier strings")
    parser.add_argument("--memory-path", default="",
                        help="MEMORY_PATH — frontmatter.json written here for downstream steps")
    args = parser.parse_args()

    vault_path = Path(args.vault_path)

    # Parse classifiers — Lobster may pass as JSON array string or plain list
    try:
        classifiers: list[str] = json.loads(args.classifiers)
    except (json.JSONDecodeError, ValueError):
        raw = args.classifiers.strip().strip("[]")
        classifiers = [c.strip().strip('"').strip("'") for c in raw.split(",") if c.strip()]

    # Collect unique folders to scan
    folders_to_scan: set[str] = set()
    for classifier in classifiers:
        folder = CLASSIFIER_FOLDER_MAP.get(classifier.lower())
        if folder:
            folders_to_scan.add(folder)

    results: list[dict] = []
    for folder_rel in sorted(folders_to_scan):
        folder_path = vault_path / folder_rel
        if not folder_path.exists():
            continue
        for md_file in sorted(folder_path.glob("*.md")):
            fm = read_frontmatter(md_file)
            if not fm:
                continue
            try:
                rel_path = str(md_file.relative_to(vault_path))
            except ValueError:
                rel_path = str(md_file)
            results.append({
                "path":        rel_path,
                "description": fm.get("description", ""),
                "status":      fm.get("status", ""),
                "node_type":   fm.get("node_type", ""),
            })

    # Write the frontmatter array to a file so downstream steps can read without
    # shell interpolation (descriptions may contain quotes or newlines).
    frontmatter_file = ""
    if args.memory_path:
        run_dir = Path(args.memory_path) / "run"
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            out_path = run_dir / "frontmatter.json"
            out_path.write_text(json.dumps(results), encoding="utf-8")
            frontmatter_file = str(out_path)
        except Exception as e:
            print(json.dumps({"warn": f"could not write frontmatter file: {e}"}), file=sys.stderr)

    # Return a dict (not raw array) so Lobster can extract frontmatter_file via
    # $read_frontmatter.json.frontmatter_file
    print(json.dumps({"frontmatter_file": frontmatter_file, "count": len(results)}))


if __name__ == "__main__":
    main()
