#!/usr/bin/env python3
"""
entity_pipeline.py — Per-entity content generation, linking, and vault writes.

Stage 4c: for each entity in the write plan, runs three sequential steps in parallel
across entities via ThreadPoolExecutor:
  1. Content directive  (light agent) — refine content_draft into final frontmatter + body
  2. Linking directive  (light agent) — determine wikilinks and connected entries
  3. Write             — git snapshot for existing files, then write to vault

Write routing:
  write_mode=obsidian   → use obsidian-cli for all vault operations
  write_mode=filesystem → direct filesystem writes (fallback path)

Returns JSON to stdout:
{
  "ok": bool,
  "written": int,
  "created": int,
  "updated": int,
  "merged": int,
  "links_added": int,
  "failed": [{ "path": str, "error": str }]
}
"""

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SCHEMA_DIR  = SCRIPT_DIR.parent / "schemas"
PROMPT_DIR  = SCRIPT_DIR.parent / "prompts"
MAX_WORKERS = 4
CONTENT_TASK_TIMEOUT = 90
LINK_TASK_TIMEOUT    = 60


def run_llm_task(
    prompt_file: str,
    input_data: dict,
    schema_file: str,
    agent: str,
    timeout: int = CONTENT_TASK_TIMEOUT,
) -> dict | None:
    """Invoke openclaw.invoke --tool llm-task with an --args-json payload.
    Returns parsed JSON output, or None on any failure.
    """
    try:
        prompt = (PROMPT_DIR / prompt_file).read_text(encoding="utf-8").strip()
        schema = json.loads((SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
    except Exception:
        return None

    payload = {"prompt": prompt, "input": input_data, "schema": schema}
    cmd = [
        "openclaw.invoke", "--tool", "llm-task", "--action", "json",
        "--agent",    agent,
        "--args-json", json.dumps(payload),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 10,
        )
        if proc.returncode != 0:
            return None
        return json.loads(proc.stdout.strip())
    except Exception:
        return None


def git_snapshot(vault_path: Path, rel_path: str) -> None:
    """Best-effort git commit before modifying an existing vault file."""
    try:
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "git_commit.py"),
             "--vault-path", str(vault_path),
             "--file", rel_path,
             "--message", "pre-sync snapshot"],
            capture_output=True, timeout=30, cwd=str(vault_path),
        )
    except Exception:
        pass


def obsidian_write(vault_name: str, rel_path: str, content: str, action: str) -> None:
    """Write or append to a vault file via obsidian-cli.

    action=create/merge/update → obsidian write (overwrites)
    action=append              → obsidian append (adds to existing)
    """
    cli_action = "append" if action == "append" else "write"
    subprocess.run(
        ["obsidian", f"vault={vault_name}", cli_action,
         f"path={rel_path}", f"content={content}"],
        capture_output=True, text=True, timeout=30, check=True,
    )


def filesystem_write(vault_path: Path, rel_path: str, full_content: str, body_only: str, action: str) -> None:
    """Write entity content via direct filesystem I/O.

    create/merge/update → write full_content (frontmatter + body)
    append              → append body_only to existing file (no extra frontmatter)
    """
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
    """Route vault write through obsidian-cli or filesystem based on write_mode."""
    if write_mode == "obsidian" and vault_name:
        # For append via obsidian-cli, send only the new body section
        content_to_send = body_only if action == "append" else full_content
        obsidian_write(vault_name, rel_path, content_to_send, action)
    else:
        filesystem_write(vault_path, rel_path, full_content, body_only, action)


def _fs_add_connected(full_path: Path, source_path: str) -> None:
    """Filesystem-only fallback: add source_path to `connected:` in a vault file."""
    try:
        content = full_path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if not fm_match:
            return
        fm_inner, body = fm_match.group(1), fm_match.group(2)

        # Parse existing connected list
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
            # connected: absent — check for inline empty form
            new_fm = re.sub(r"^connected:\s*\[\s*\]", new_connected, fm_inner, flags=re.MULTILINE)
            if new_fm == fm_inner:
                new_fm = fm_inner.rstrip() + f"\n{new_connected}"

        full_path.write_text(f"---\n{new_fm}\n---\n{body}", encoding="utf-8")
    except Exception:
        pass


def update_connected_for(
    vault_path: Path, vault_name: str, target_path: str, source_path: str, write_mode: str
) -> None:
    """Add source_path to target file's connected: array.

    obsidian mode → delegates to update_connected.py (uses obsidian-cli for both read/write)
    filesystem mode → direct in-place edit via _fs_add_connected
    """
    if write_mode == "obsidian" and vault_name:
        try:
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "update_connected.py"),
                 "--vault", vault_name,
                 "--file",  target_path,   # vault-relative path
                 "--add",   source_path],
                capture_output=True, timeout=15,
            )
        except Exception:
            pass
    else:
        _fs_add_connected(vault_path / target_path, source_path)


def build_frontmatter_block(frontmatter: dict) -> str:
    """Render frontmatter dict to a YAML block string (without trailing newline)."""
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
    """Run content → linking → write for a single entity."""
    path   = entity.get("path", "")
    action = entity.get("action", "create")
    draft  = entity.get("content_draft", "")

    # ── Step 1: Content directive ──────────────────────────────────────────
    content_result = run_llm_task(
        "entity_content_prompt.txt",
        {"content_draft": draft, "action": action, "path": path},
        "entity_content_schema.json",
        "memspren-light",
        timeout=CONTENT_TASK_TIMEOUT,
    )

    if not content_result:
        return {"path": path, "ok": False, "error": "content directive failed", "action": action}

    body        = content_result.get("body", draft)
    frontmatter = content_result.get("frontmatter", {})

    # full_content = frontmatter block + body (used for create/merge/update)
    # body_only    = body section only     (used for append — no extra frontmatter)
    full_content = build_frontmatter_block(frontmatter) + "\n\n" + body
    body_only    = body

    # ── Step 2: Linking directive ──────────────────────────────────────────
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
        "entity_linking_schema.json",   # correct schema: { wikilinks, connected_additions }
        "memspren-light",
        timeout=LINK_TASK_TIMEOUT,
    )

    links_added = 0
    if linking_result:
        wikilinks           = linking_result.get("wikilinks", [])
        connected_additions = linking_result.get("connected_additions", [])

        if wikilinks:
            link_text = "  ".join(f"[[{w}]]" for w in wikilinks)
            # Append links footer to body — affects both full_content and body_only
            footer = f"\n\n---\n*Related: {link_text}*"
            full_content += footer
            body_only    += footer
            links_added = len(wikilinks)

        for target in connected_additions:
            update_connected_for(vault_path, vault_name, target, path, write_mode)

    # ── Step 3: Write ──────────────────────────────────────────────────────
    if action in ("append", "merge", "update") and full_path.exists():
        git_snapshot(vault_path, path)

    try:
        write_entity(vault_path, vault_name, path, full_content, body_only, action, write_mode)
    except Exception as e:
        return {"path": path, "ok": False, "error": f"write failed: {e}", "action": action}

    return {"path": path, "ok": True, "action": action, "links_added": links_added}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan",        required=True, help="JSON string of entity write plan")
    parser.add_argument("--vault-path",  required=True)
    parser.add_argument("--vault-name",  default="",   help="Obsidian vault name for CLI routing")
    parser.add_argument("--write-mode",  default="filesystem", choices=["obsidian", "filesystem"])
    parser.add_argument("--memory-path", required=True)
    args = parser.parse_args()

    try:
        plan = json.loads(args.plan)
        entities = plan.get("entities", plan) if isinstance(plan, dict) else plan
        if not isinstance(entities, list):
            entities = []
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid plan JSON: {e}"}))
        sys.exit(1)

    vault_path = Path(args.vault_path)
    entity_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_entity, entity, vault_path, args.vault_name, args.write_mode
            ): entity
            for entity in entities
        }
        for future in as_completed(futures):
            entity_results.append(future.result())

    created     = sum(1 for r in entity_results if r.get("ok") and r.get("action") == "create")
    updated     = sum(1 for r in entity_results if r.get("ok") and r.get("action") in ("append", "update"))
    merged      = sum(1 for r in entity_results if r.get("ok") and r.get("action") == "merge")
    links_added = sum(r.get("links_added", 0) for r in entity_results)
    failed      = [{"path": r["path"], "error": r["error"]} for r in entity_results if not r.get("ok")]
    written     = len(entity_results) - len(failed)

    print(json.dumps({
        "ok":          written > 0 or len(entities) == 0,
        "written":     written,
        "created":     created,
        "updated":     updated,
        "merged":      merged,
        "links_added": links_added,
        "failed":      failed,
    }))


if __name__ == "__main__":
    main()
