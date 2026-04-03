"""rotate_buffer.py — Manage rotating sync buffers for MemSpren.

Buffers are identified by scanning frontmatter — no pointer file needed.
The active buffer is whichever sync-buffer-*.md has `state: active`.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from datetime import datetime

from .. import state
from ..log import Logger
from ..paths import VaultPaths

BUFFER_PREFIX = "sync-buffer-"
DEFAULT_MAX_WORDS = 1500


def _buf_path(buffers_dir: str, buffer_id: str) -> str:
    return os.path.join(buffers_dir, f"{BUFFER_PREFIX}{buffer_id}.md")


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    yaml_block = content[3:end].strip()
    result = {}
    for line in yaml_block.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("-"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def count_words(content: str) -> int:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:]
    return len(content.split())


def list_buffer_files(buffers_dir: str) -> list:
    """Scan all sync-buffer-*.md files and return their metadata, sorted by buffer ID."""
    pattern = os.path.join(buffers_dir, f"{BUFFER_PREFIX}*.md")
    files = glob.glob(pattern)
    results = []
    for f in sorted(files):
        filename = os.path.basename(f)
        match = re.search(r"sync-buffer-(\d+)\.md", filename)
        if not match:
            continue
        buffer_id = match.group(1)
        with open(f, "r") as fh:
            content = fh.read()
        meta = parse_frontmatter(content)
        words = count_words(content)
        results.append({
            "buffer_id": buffer_id,
            "path": f,
            "state": meta.get("state", "unknown"),
            "word_count": words,
            "entry_count": int(meta.get("entry_count", 0)),
            "created": meta.get("created"),
            "sealed_at": meta.get("sealed_at"),
        })
    return results


def find_active_buffer(buffers_dir: str) -> dict | None:
    """Find the active buffer by scanning frontmatters. Returns buffer info or None."""
    for buf in list_buffer_files(buffers_dir):
        if buf["state"] == "active":
            return buf
    return None


def next_buffer_id(current_id: str) -> str:
    return f"{int(current_id) + 1:03d}"


def create_buffer(buffers_dir: str, buffer_id: str) -> str:
    """Create a new active buffer file. Returns the path."""
    now = datetime.now().astimezone().isoformat()
    content = f"""---
node_type: sync-buffer
buffer_id: "{buffer_id}"
state: active
created: {now}
sealed_at: null
word_count: 0
entry_count: 0
---
"""
    path = _buf_path(buffers_dir, buffer_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path


def seal_buffer(buffers_dir: str, buffer_id: str) -> dict:
    path = _buf_path(buffers_dir, buffer_id)
    if not os.path.exists(path):
        return {"error": f"Buffer {buffer_id} not found"}
    with open(path, "r") as f:
        content = f.read()
    now = datetime.now().astimezone().isoformat()
    words = count_words(content)
    content = re.sub(r"state:\s*\w+", "state: sealed", content)
    content = re.sub(r"sealed_at:\s*\S+", f"sealed_at: {now}", content)
    content = re.sub(r"word_count:\s*\d+", f"word_count: {words}", content)
    with open(path, "w") as f:
        f.write(content)
    return {"buffer_id": buffer_id, "state": "sealed", "sealed_at": now, "word_count": words}


def list_sealed(buffers_dir: str) -> list:
    return [b for b in list_buffer_files(buffers_dir) if b["state"] == "sealed"]


def check_status(buffers_dir: str, max_words: int) -> dict:
    buf = find_active_buffer(buffers_dir)
    if not buf:
        return {"active_buffer": None, "needs_initialization": True}
    return {
        "active_buffer": buf["buffer_id"],
        "word_count": buf["word_count"],
        "entry_count": buf["entry_count"],
        "max_words": max_words,
        "needs_rotation": buf["word_count"] >= max_words,
        "state": buf["state"],
        "needs_initialization": False,
    }


def rotate(buffers_dir: str) -> dict:
    buf = find_active_buffer(buffers_dir)
    if not buf:
        create_buffer(buffers_dir, "001")
        return {"action": "initialized", "new_active": "001"}
    seal_result = seal_buffer(buffers_dir, buf["buffer_id"])
    if "error" in seal_result:
        return seal_result
    new_id = next_buffer_id(buf["buffer_id"])
    create_buffer(buffers_dir, new_id)
    return {
        "action": "rotated",
        "sealed": buf["buffer_id"],
        "sealed_word_count": seal_result["word_count"],
        "new_active": new_id,
    }


def get_active_path(buffers_dir: str) -> dict:
    buf = find_active_buffer(buffers_dir)
    if not buf:
        path = create_buffer(buffers_dir, "001")
        return {"active_buffer": "001", "path": path, "initialized": True}
    if not os.path.exists(buf["path"]):
        path = create_buffer(buffers_dir, buf["buffer_id"])
        return {"active_buffer": buf["buffer_id"], "path": path, "recreated": True}
    return {"active_buffer": buf["buffer_id"], "path": buf["path"]}


def get_active_buffer_with_rotation(buffers_dir: str, max_words: int) -> dict:
    """Return active buffer path, rotating first if over the word limit.

    Used by the `get-active-buffer` CLI command during conversation to get
    the correct buffer path before appending a new entry.

    Returns: {"path": str, "rotated": bool, "entry_count": int}
    """
    buf = find_active_buffer(buffers_dir)

    if buf is None:
        path = create_buffer(buffers_dir, "001")
        return {"path": path, "rotated": False, "entry_count": 0}

    if buf["word_count"] >= max_words:
        seal_buffer(buffers_dir, buf["buffer_id"])
        new_id = next_buffer_id(buf["buffer_id"])
        path = create_buffer(buffers_dir, new_id)
        return {"path": path, "rotated": True, "entry_count": 0}

    return {
        "path": buf["path"],
        "rotated": False,
        "entry_count": buf["entry_count"],
    }


def cleanup_buffer(buffers_dir: str, buffer_id: str, archive_dir: str = None) -> dict:
    path = _buf_path(buffers_dir, buffer_id)
    if not os.path.exists(path):
        return {"action": "skipped", "reason": "file not found", "buffer_id": buffer_id}
    if archive_dir:
        archive_path = os.path.join(
            buffers_dir, "sync-archive",
            f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{buffer_id}.md",
        )
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(path, "r") as src:
            content = src.read()
        with open(archive_path, "w") as dst:
            dst.write(content)
    os.remove(path)
    # After cleanup, reset buffer numbering if no sealed buffers remain
    remaining = list_sealed(buffers_dir)
    if not remaining:
        buf = find_active_buffer(buffers_dir)
        if buf and int(buf["buffer_id"]) > 1:
            old_path = buf["path"]
            new_path = _buf_path(buffers_dir, "001")
            if os.path.exists(old_path) and old_path != new_path:
                with open(old_path, "r") as f:
                    content = f.read()
                content = re.sub(r'buffer_id:\s*"\d+"', 'buffer_id: "001"', content)
                with open(new_path, "w") as f:
                    f.write(content)
                os.remove(old_path)
    return {"action": "cleaned", "buffer_id": buffer_id}


def sync_check(buffers_dir: str, run_path: str) -> dict:
    empty = {
        "has_content": False,
        "should_exit": True,
        "sealed_buffers": [],
        "buffer_content_file": "",
        "entry_count": 0,
    }

    # Seal active buffer if it has content
    buf = find_active_buffer(buffers_dir)
    if buf and buf["word_count"] > 0 and buf["entry_count"] > 0:
        seal_buffer(buffers_dir, buf["buffer_id"])
        new_id = next_buffer_id(buf["buffer_id"])
        create_buffer(buffers_dir, new_id)

    sealed = list_sealed(buffers_dir)
    if not sealed:
        return empty

    parts = []
    total_entries = 0
    for buf in sealed:
        buf_path = buf.get("path", "")
        if os.path.exists(buf_path):
            with open(buf_path, "r") as f:
                buf_content = f.read()
            if buf_content.startswith("---"):
                end = buf_content.find("---", 3)
                if end != -1:
                    buf_content = buf_content[end + 3:].strip()
            parts.append(buf_content)
            total_entries += buf.get("entry_count", 0)

    combined = "\n\n---\n\n".join(parts)
    content_file = os.path.join(run_path, "buffer-content.txt")
    try:
        os.makedirs(run_path, exist_ok=True)
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(combined)
    except Exception as e:
        print(json.dumps({"warn": f"could not write buffer-content file: {e}"}), file=sys.stderr)
        content_file = ""

    return {
        "has_content": bool(parts),
        "should_exit": not bool(parts),
        "sealed_buffers": sealed,
        "buffer_content_file": content_file,
        "entry_count": total_entries,
    }


def run(
    *,
    vault_path: str,
    sync_check_mode: bool = False,
    check: bool = False,
    rotate_mode: bool = False,
    list_sealed_mode: bool = False,
    list_all: bool = False,
    active_path: bool = False,
    cleanup: bool = False,
    buffer_id: str = "",
    archive: bool = True,
    max_words: int = DEFAULT_MAX_WORDS,
    log: Logger,
) -> dict | list:
    paths = VaultPaths(vault_path)
    paths.ensure()
    bd = str(paths.buffers)

    if sync_check_mode:
        log.info("sync-check mode")
        result = sync_check(bd, str(paths.run))
        if result.get("sealed_buffers"):
            state.write_state(str(paths.run), {
                "rotate_buffer_sealed_buffers": result["sealed_buffers"],
            })
        log.debug("sync-check result", has_content=result["has_content"], entry_count=result["entry_count"])
        return result
    if check:
        return check_status(bd, max_words)
    if rotate_mode:
        return rotate(bd)
    if list_sealed_mode:
        return list_sealed(bd)
    if list_all:
        return list_buffer_files(bd)
    if active_path:
        return get_active_path(bd)
    if cleanup:
        if not buffer_id:
            raise RuntimeError("provide --buffer-id for cleanup")
        return cleanup_buffer(bd, buffer_id, "archive" if archive else None)
    raise RuntimeError("provide one of: --check, --rotate, --list-sealed, --list-all, --active-path, --cleanup")
