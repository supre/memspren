"""entity_writer.py — Write entities to vault.

For action=create: write content_draft directly (it's write-ready with frontmatter).
For action=append/merge/update: LLM refinement call merges existing content with new content.
"""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint, post_json
from ..log import Logger
from ..paths import VaultPaths
from ..vault.git_commit import commit_file as _git_commit_file

MAX_WORKERS = 4
MERGE_TIMEOUT = 600


def _git_snapshot(vault_path: Path, rel_path: str) -> None:
    try:
        _git_commit_file(str(vault_path), rel_path, "pre-sync snapshot")
    except Exception:
        pass


def _filesystem_write(vault_path: Path, rel_path: str, content: str) -> None:
    full_path = vault_path / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


def _obsidian_write(vault_name: str, rel_path: str, content: str) -> None:
    subprocess.run(
        ["obsidian", f"vault={vault_name}", "write",
         f"path={rel_path}", f"content={content}"],
        capture_output=True, text=True, timeout=30, check=True,
    )


def _write_file(vault_path: Path, vault_name: str, rel_path: str,
                content: str, write_mode: str) -> None:
    if write_mode == "obsidian" and vault_name:
        _obsidian_write(vault_name, rel_path, content)
    else:
        _filesystem_write(vault_path, rel_path, content)


def _merge_via_llm(existing_content: str, new_content: str,
                   action: str, path: str, log: Logger) -> str | None:
    """Call LLM to merge existing content with new content. Returns final content or None on failure."""
    try:
        prompt = (PROMPTS_DIR / "entity_content_prompt.txt").read_text(encoding="utf-8").strip()
        schema = json.loads((SCHEMAS_DIR / "entity_content_schema.json").read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"could not load merge prompt/schema", error=str(e))
        return None

    gateway_token = get_gateway_token()
    endpoint = get_gateway_endpoint()

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": {
                "existing_content": existing_content,
                "new_content": new_content,
                "action": action,
                "path": path,
            },
            "schema": schema,
            "agent": "main",
            "timeoutMs": MERGE_TIMEOUT * 1000,
        },
    }

    log.debug(f"merge LLM call for {path}",
              existing_len=len(existing_content), new_len=len(new_content), action=action)

    try:
        result = post_json(endpoint, payload, token=gateway_token, timeout=MERGE_TIMEOUT)
    except Exception as e:
        log.error(f"merge LLM call failed for {path}", error=str(e))
        return None

    log.debug(f"merge LLM response for {path}",
              result_keys=list(result.keys()) if isinstance(result, dict) else "n/a")

    # Extract output
    try:
        if "result" in result:
            inner = result["result"]
            if "details" in inner and "json" in inner["details"]:
                output = inner["details"]["json"]
            elif "content" in inner:
                items = inner["content"]
                text = next(i["text"] for i in items if i.get("type") == "text")
                output = json.loads(text)
            else:
                output = inner
        else:
            output = result
    except Exception as e:
        log.error(f"could not parse merge response for {path}", error=str(e))
        return None

    # Build final content from frontmatter + body
    frontmatter = output.get("frontmatter", {})
    body = output.get("body", "")

    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")

    return "\n".join(lines) + "\n\n" + body


def _process_entity(
    entity: dict,
    vault_path: Path,
    vault_name: str,
    write_mode: str,
    log: Logger,
) -> dict:
    path = entity.get("path", "")
    action = entity.get("action", "create")
    raw_draft = entity.get("content_draft", "")
    # Normalize: accept array of bullets or plain string
    if isinstance(raw_draft, list):
        content_draft = "\n".join(str(item) for item in raw_draft)
    else:
        content_draft = str(raw_draft) if raw_draft else ""
    full_path = vault_path / path

    log.debug(f"processing entity: {path}", action=action)

    if action == "create":
        # content_draft is brief notes — expand to full content via LLM
        final_content = _merge_via_llm("", content_draft, "create", path, log)
        if final_content is None:
            log.warn(f"LLM content generation failed for {path}, writing notes as-is")
            final_content = content_draft
        try:
            _write_file(vault_path, vault_name, path, final_content, write_mode)
            log.info(f"created entity: {path}")
            return {"path": path, "ok": True, "action": action}
        except Exception as e:
            log.error(f"write failed for {path}", error=str(e))
            return {"path": path, "ok": False, "error": f"write failed: {e}", "action": action}

    # append/merge/update — need LLM refinement with existing content
    if not full_path.exists():
        log.warn(f"existing file not found for {action}: {path}, treating as create")
        final_content = _merge_via_llm("", content_draft, "create", path, log) or content_draft
        try:
            _write_file(vault_path, vault_name, path, final_content, write_mode)
            log.info(f"created entity (fallback from {action}): {path}")
            return {"path": path, "ok": True, "action": "create"}
        except Exception as e:
            log.error(f"write failed for {path}", error=str(e))
            return {"path": path, "ok": False, "error": f"write failed: {e}", "action": action}

    # Git snapshot before modifying
    _git_snapshot(vault_path, path)

    existing_content = full_path.read_text(encoding="utf-8")
    merged = _merge_via_llm(existing_content, content_draft, action, path, log)

    if merged is None:
        log.warn(f"merge failed for {path}, falling back to simple append")
        # Fallback: just append the new content
        merged = existing_content.rstrip() + "\n\n" + content_draft

    try:
        _write_file(vault_path, vault_name, path, merged, write_mode)
        log.info(f"wrote entity ({action}): {path}")
        return {"path": path, "ok": True, "action": action}
    except Exception as e:
        log.error(f"write failed for {path}", error=str(e))
        return {"path": path, "ok": False, "error": f"write failed: {e}", "action": action}


def run(
    *,
    plan: str,
    vault_path: Path,
    vault_name: str = "",
    write_mode: str = "filesystem",
    log: Logger,
) -> dict:
    # plan can be a file path or inline JSON
    plan_path = Path(plan)
    if plan_path.is_file():
        plan_text = plan_path.read_text(encoding="utf-8")
        log.debug("read plan from file", path=plan)
    else:
        plan_text = plan

    try:
        plan_data = json.loads(plan_text)
        entities = plan_data.get("entities", plan_data) if isinstance(plan_data, dict) else plan_data
        if not isinstance(entities, list):
            entities = []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid plan JSON: {e}") from e

    log.info("starting entity writer", entity_count=len(entities), write_mode=write_mode)

    entity_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_process_entity, entity, vault_path, vault_name, write_mode, log): entity
            for entity in entities
        }
        for future in as_completed(futures):
            entity_results.append(future.result())

    created = sum(1 for r in entity_results if r.get("ok") and r.get("action") == "create")
    updated = sum(1 for r in entity_results if r.get("ok") and r.get("action") in ("append", "update", "merge"))
    failed = [{"path": r["path"], "error": r.get("error", "")} for r in entity_results if not r.get("ok")]
    written = len(entity_results) - len(failed)

    log.info("entity writer complete", written=written, created=created, updated=updated, failed=len(failed))

    # Save result to run/ for the linking step
    paths = VaultPaths(vault_path)
    result_file = paths.run / "entity-write-result.json"
    entity_list = [{"path": r["path"], "action": r["action"]} for r in entity_results if r.get("ok")]
    try:
        result_file.write_text(json.dumps({"entities": entity_list}), encoding="utf-8")
        log.debug("saved entity-write result", path=str(result_file))
    except Exception as e:
        log.warn(f"could not save entity-write result: {e}")

    return {
        "ok": written > 0 or len(entities) == 0,
        "written": written,
        "created": created,
        "updated": updated,
        "failed": failed,
        "entities": [{"path": r["path"], "action": r["action"]} for r in entity_results if r.get("ok")],
    }
