"""
entity_pipeline.py — Per-entity content generation, linking, and vault writes.

Stage 4c: for each entity in the write plan, runs three sequential steps in parallel
across entities via ThreadPoolExecutor:
  1. Content directive  (light agent) — refine content_draft into final frontmatter + body
  2. Linking directive  (light agent) — determine wikilinks and connected entries
  3. Write             — git snapshot for existing files, then write to vault
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint
from ..vault.git_commit import commit_file as _git_commit_file

MAX_WORKERS = 4
CONTENT_TASK_TIMEOUT = 90
LINK_TASK_TIMEOUT = 60


def run_llm_task(
    prompt_file: str,
    input_data: dict,
    schema_file: str,
    agent: str,
    timeout: int = CONTENT_TASK_TIMEOUT,
) -> dict | None:
    """Call the OpenClaw Gateway /tools/invoke for an llm-task."""
    try:
        prompt = (PROMPTS_DIR / prompt_file).read_text(encoding="utf-8").strip()
        schema = json.loads((SCHEMAS_DIR / schema_file).read_text(encoding="utf-8"))
    except Exception:
        return None

    gateway_token = get_gateway_token()
    endpoint = get_gateway_endpoint()

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": input_data,
            "schema": schema,
            "agent": agent,
            "timeoutMs": timeout * 1000,
        },
    }

    try:
        result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=timeout)
    except Exception:
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
    except Exception:
        return None


def git_snapshot(vault_path: Path, rel_path: str) -> None:
    try:
        _git_commit_file(str(vault_path), rel_path, "pre-sync snapshot")
    except Exception:
        pass


def obsidian_write(vault_name: str, rel_path: str, content: str, action: str) -> None:
    cli_action = "append" if action == "append" else "write"
    subprocess.run(
        ["obsidian", f"vault={vault_name}", cli_action,
         f"path={rel_path}", f"content={content}"],
        capture_output=True, text=True, timeout=30, check=True,
    )


def filesystem_write(vault_path: Path, rel_path: str, full_content: str, body_only: str, action: str) -> None:
    full_path = vault_path / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if action == "append":
        existing = full_path.read_text(encoding="utf-8") if full_path.exists() else ""
        full_path.write_text(
            existing.rstrip() + "\n\n" + body_only if existing else full_content,
            encoding="utf-8",
        )
    else:
        full_path.write_text(full_content, encoding="utf-8")


def write_entity(
    vault_path: Path,
    vault_name: str,
    rel_path: str,
    full_content: str,
    body_only: str,
    action: str,
    write_mode: str,
) -> None:
    if write_mode == "obsidian" and vault_name:
        content_to_send = body_only if action == "append" else full_content
        obsidian_write(vault_name, rel_path, content_to_send, action)
    else:
        filesystem_write(vault_path, rel_path, full_content, body_only, action)


def _fs_add_connected(full_path: Path, source_path: str) -> None:
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


def update_connected_for(
    vault_path: Path, vault_name: str, target_path: str, source_path: str, write_mode: str
) -> None:
    if write_mode == "obsidian" and vault_name:
        update_connected_script = Path(__file__).parent.parent / "vault" / "update_connected.py"
        try:
            subprocess.run(
                [sys.executable, str(update_connected_script),
                 "--vault", vault_name,
                 "--file", target_path,
                 "--add", source_path],
                capture_output=True, timeout=15,
            )
        except Exception:
            pass
    else:
        _fs_add_connected(vault_path / target_path, source_path)


def build_frontmatter_block(frontmatter: dict) -> str:
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def process_entity(
    entity: dict,
    vault_path: Path,
    vault_name: str,
    write_mode: str,
) -> dict:
    path = entity.get("path", "")
    action = entity.get("action", "create")
    draft = entity.get("content_draft", "")

    # Step 1: Content directive
    content_result = run_llm_task(
        "entity_content_prompt.txt",
        {"content_draft": draft, "action": action, "path": path},
        "entity_content_schema.json",
        "memspren-light",
        timeout=CONTENT_TASK_TIMEOUT,
    )

    if not content_result:
        return {"path": path, "ok": False, "error": "content directive failed", "action": action}

    body = content_result.get("body", draft)
    frontmatter = content_result.get("frontmatter", {})
    full_content = build_frontmatter_block(frontmatter) + "\n\n" + body
    body_only = body

    # Step 2: Linking directive
    existing_snippet = ""
    full_path = vault_path / path
    if full_path.exists():
        try:
            existing_snippet = full_path.read_text(encoding="utf-8")[:2000]
        except Exception:
            pass

    linking_result = run_llm_task(
        "entity_linking_prompt.txt",
        {"entity_content": full_content, "existing_content": existing_snippet, "path": path},
        "entity_linking_schema.json",
        "memspren-light",
        timeout=LINK_TASK_TIMEOUT,
    )

    links_added = 0
    if linking_result:
        wikilinks = linking_result.get("wikilinks", [])
        connected_additions = linking_result.get("connected_additions", [])

        if wikilinks:
            link_text = "  ".join(f"[[{w}]]" for w in wikilinks)
            footer = f"\n\n---\n*Related: {link_text}*"
            full_content += footer
            body_only += footer
            links_added = len(wikilinks)

        for target in connected_additions:
            update_connected_for(vault_path, vault_name, target, path, write_mode)

    # Step 3: Write
    if action in ("append", "merge", "update") and full_path.exists():
        git_snapshot(vault_path, path)

    try:
        write_entity(vault_path, vault_name, path, full_content, body_only, action, write_mode)
    except Exception as e:
        return {"path": path, "ok": False, "error": f"write failed: {e}", "action": action}

    return {"path": path, "ok": True, "action": action, "links_added": links_added}


def run(
    *,
    plan: str,
    vault_path: Path,
    vault_name: str = "",
    write_mode: str = "filesystem",
    memory_path: Path,
) -> dict:
    try:
        plan_data = json.loads(plan)
        entities = plan_data.get("entities", plan_data) if isinstance(plan_data, dict) else plan_data
        if not isinstance(entities, list):
            entities = []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid plan JSON: {e}") from e

    entity_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_entity, entity, vault_path, vault_name, write_mode
            ): entity
            for entity in entities
        }
        for future in as_completed(futures):
            entity_results.append(future.result())

    created = sum(1 for r in entity_results if r.get("ok") and r.get("action") == "create")
    updated = sum(1 for r in entity_results if r.get("ok") and r.get("action") in ("append", "update"))
    merged = sum(1 for r in entity_results if r.get("ok") and r.get("action") == "merge")
    links_added = sum(r.get("links_added", 0) for r in entity_results)
    failed = [{"path": r["path"], "error": r["error"]} for r in entity_results if not r.get("ok")]
    written = len(entity_results) - len(failed)

    return {
        "ok": written > 0 or len(entities) == 0,
        "written": written,
        "created": created,
        "updated": updated,
        "merged": merged,
        "links_added": links_added,
        "failed": failed,
    }
