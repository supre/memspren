"""entity_linker.py — Determine and write wikilinks for vault entities.

Runs after entity_writer has written all entities. For each newly written entity:
1. LLM call to determine wikilinks + connected additions
2. If link target doesn't exist → create a stub entity
3. Write wikilinks into entity files + update connected arrays
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint, post_json
from ..log import Logger
from ..scanning.read_frontmatter import read_frontmatter

MAX_WORKERS = 4
LINK_TIMEOUT = 60


def _link_via_llm(entity_content: str, path: str, all_entities: list[dict],
                  log: Logger) -> dict | None:
    """Call LLM to determine links for an entity."""
    try:
        prompt = (PROMPTS_DIR / "entity_linking_prompt.txt").read_text(encoding="utf-8").strip()
        schema = json.loads((SCHEMAS_DIR / "entity_linking_schema.json").read_text(encoding="utf-8"))
    except Exception as e:
        log.error("could not load linking prompt/schema", error=str(e))
        return None

    # Build context: list of all known entity paths for the LLM
    existing_summary = "\n".join(
        f"- {e['path']}: {e.get('description', '')}" for e in all_entities[:100]
    )

    gateway_token = get_gateway_token()
    endpoint = get_gateway_endpoint()

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": {
                "entity_content": entity_content[:3000],
                "existing_content": existing_summary,
                "path": path,
            },
            "schema": schema,
            "agent": "memspren-light",
            "timeoutMs": LINK_TIMEOUT * 1000,
        },
    }

    log.debug(f"linking LLM call for {path}", content_len=len(entity_content))

    try:
        result = post_json(endpoint, payload, token=gateway_token, timeout=LINK_TIMEOUT)
    except Exception as e:
        log.error(f"linking LLM call failed for {path}", error=str(e))
        return None

    try:
        if "result" in result:
            inner = result["result"]
            if "details" in inner and "json" in inner["details"]:
                return inner["details"]["json"]
            if "content" in inner:
                items = inner["content"]
                text = next(i["text"] for i in items if i.get("type") == "text")
                return json.loads(text)
            return inner
        return result
    except Exception as e:
        log.error(f"could not parse linking response for {path}", error=str(e))
        return None


def _create_stub(vault_path: Path, rel_path: str, log: Logger) -> None:
    """Create a minimal stub entity for a link target that doesn't exist."""
    full_path = vault_path / rel_path
    if full_path.exists():
        return

    # Derive node_type from path
    node_type = "note"
    if rel_path.startswith("People/"):
        node_type = "person"
    elif rel_path.startswith("Work/Projects/"):
        node_type = "project"
    elif rel_path.startswith("Work/Ideas/"):
        node_type = "idea"
    elif rel_path.startswith("Notes/Learnings/"):
        node_type = "learning"
    elif rel_path.startswith("Notes/Patterns/"):
        node_type = "pattern"

    name = Path(rel_path).stem.replace("-", " ").title()

    content = f"""---
node_type: {node_type}
description: "{name} — stub created by linking step"
status: active
connected: []
---

# {name}

*This entity was auto-created as a link target. Add content during your next sync.*
"""
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    log.info(f"created stub entity: {rel_path}", node_type=node_type)


def _add_wikilinks_footer(vault_path: Path, rel_path: str, wikilinks: list[str]) -> None:
    """Append a Related links footer to an entity file."""
    full_path = vault_path / rel_path
    if not full_path.exists() or not wikilinks:
        return
    content = full_path.read_text(encoding="utf-8")
    link_text = "  ".join(f"[[{w}]]" for w in wikilinks)
    footer = f"\n\n---\n*Related: {link_text}*"
    full_path.write_text(content.rstrip() + footer, encoding="utf-8")


def _update_connected(vault_path: Path, target_path: str, source_path: str) -> None:
    """Add source_path to target file's connected: frontmatter array."""
    full_path = vault_path / target_path
    if not full_path.exists():
        return
    try:
        content = full_path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if not fm_match:
            return
        fm_inner, body = fm_match.group(1), fm_match.group(2)

        block = re.search(r"^connected:\s*\n((?:[ \t]+-[^\n]*\n?)*)", fm_inner, re.MULTILINE)
        if block:
            existing = [l.strip().lstrip("- ").strip() for l in block.group(1).splitlines() if l.strip().startswith("-")]
        else:
            existing = []

        if source_path in existing:
            return

        existing.append(source_path)
        items = "\n".join(f"  - {p}" for p in existing)
        new_connected = f"connected:\n{items}"

        if block:
            new_fm = re.sub(r"^connected:\s*\n(?:[ \t]+-[^\n]*\n?)*", new_connected + "\n", fm_inner, flags=re.MULTILINE)
        else:
            new_fm = re.sub(r"^connected:\s*\[\s*\]", new_connected, fm_inner, flags=re.MULTILINE)
            if new_fm == fm_inner:
                new_fm = fm_inner.rstrip() + f"\n{new_connected}"

        full_path.write_text(f"---\n{new_fm}\n---\n{body}", encoding="utf-8")
    except Exception:
        pass


def _process_entity_links(
    entity_path: str,
    vault_path: Path,
    all_entities: list[dict],
    log: Logger,
) -> dict:
    """Determine and write links for a single entity."""
    full_path = vault_path / entity_path
    if not full_path.exists():
        return {"path": entity_path, "ok": False, "error": "file not found", "links_added": 0}

    content = full_path.read_text(encoding="utf-8")
    linking = _link_via_llm(content, entity_path, all_entities, log)

    if not linking:
        return {"path": entity_path, "ok": True, "links_added": 0}

    wikilinks = linking.get("wikilinks", [])
    connected_additions = linking.get("connected_additions", [])

    # Create stub entities for missing link targets
    for target in connected_additions:
        if not (vault_path / target).exists():
            _create_stub(vault_path, target, log)

    # Write wikilinks footer
    if wikilinks:
        _add_wikilinks_footer(vault_path, entity_path, wikilinks)

    # Update connected arrays on target files
    for target in connected_additions:
        _update_connected(vault_path, target, entity_path)

    log.debug(f"linked {entity_path}", wikilinks=len(wikilinks), connected=len(connected_additions))
    return {"path": entity_path, "ok": True, "links_added": len(wikilinks)}


def run(
    *,
    vault_path: Path,
    written_entities: str = "[]",
    log: Logger,
) -> dict:
    # written_entities can be a file path or inline JSON
    we_path = Path(written_entities)
    if we_path.is_file():
        we_text = we_path.read_text(encoding="utf-8")
        log.debug("read written entities from file", path=written_entities)
    else:
        we_text = written_entities

    try:
        entities_list = json.loads(we_text)
        if isinstance(entities_list, dict):
            entities_list = entities_list.get("entities", [])
        if not isinstance(entities_list, list):
            entities_list = []
    except json.JSONDecodeError:
        entities_list = []

    if not entities_list:
        log.info("no entities to link")
        return {"ok": True, "linked": 0, "stubs_created": 0}

    entity_paths = [e.get("path", "") for e in entities_list if e.get("path")]
    log.info("starting entity linker", entity_count=len(entity_paths))

    # Build full frontmatter list (new entities + existing vault files)
    all_entities: list[dict] = []
    for ep in entity_paths:
        fm = read_frontmatter(vault_path / ep)
        if fm:
            all_entities.append({"path": ep, **fm})

    # Also scan common vault folders for existing entities
    for folder in ["Work/Projects", "Work/Ideas", "People", "Notes/Learnings",
                    "Notes/Patterns", "Vision", "Strategy"]:
        folder_path = vault_path / folder
        if folder_path.exists():
            for md in folder_path.glob("*.md"):
                rel = str(md.relative_to(vault_path))
                if rel not in entity_paths:
                    fm = read_frontmatter(md)
                    if fm:
                        all_entities.append({"path": rel, **fm})

    log.debug("built entity index", total_entities=len(all_entities))

    # Process links in parallel
    link_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_process_entity_links, ep, vault_path, all_entities, log): ep
            for ep in entity_paths
        }
        for future in as_completed(futures):
            link_results.append(future.result())

    total_links = sum(r.get("links_added", 0) for r in link_results)
    linked = sum(1 for r in link_results if r.get("links_added", 0) > 0)

    log.info("entity linker complete", linked=linked, total_links=total_links)

    return {
        "ok": True,
        "linked": linked,
        "total_links": total_links,
        "results": link_results,
    }
