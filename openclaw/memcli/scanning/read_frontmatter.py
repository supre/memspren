"""read_frontmatter.py — Batch-read YAML frontmatter from classifier-scoped vault folders."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ..log import Logger
from ..paths import VaultPaths

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


def run(
    *,
    vault_path: Path,
    classifiers: str,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()

    try:
        classifier_list: list[str] = json.loads(classifiers)
    except (json.JSONDecodeError, ValueError):
        raw = classifiers.strip().strip("[]")
        classifier_list = [c.strip().strip('"').strip("'") for c in raw.split(",") if c.strip()]

    folders_to_scan: set[str] = set()
    for classifier in classifier_list:
        folder = CLASSIFIER_FOLDER_MAP.get(classifier.lower())
        if folder:
            folders_to_scan.add(folder)

    log.debug("scanning folders", folders=list(folders_to_scan))

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
                "path": rel_path,
                "description": fm.get("description", ""),
                "status": fm.get("status", ""),
                "node_type": fm.get("node_type", ""),
            })

    frontmatter_file = ""
    try:
        out_path = paths.run / "frontmatter.json"
        out_path.write_text(json.dumps(results), encoding="utf-8")
        frontmatter_file = str(out_path)
    except Exception as e:
        log.warn(f"could not write frontmatter file: {e}")

    log.info("frontmatter scan complete", count=len(results))
    return {"frontmatter_file": frontmatter_file, "count": len(results)}
