#!/usr/bin/env python3
"""
rotate_buffer.py — Manage rotating sync buffers for MemSpren.

Handles buffer rotation: check size, seal current buffer when it hits
the word cap, create new active buffer, list sealed buffers ready for sync.

Usage:
    # Check current buffer status
    python3 -m openclaw.scripts.buffer.rotate_buffer --vault-path "/path/to/vault" --check

    # Rotate: seal current buffer, create new active
    python3 -m openclaw.scripts.buffer.rotate_buffer --vault-path "/path/to/vault" --rotate

    # List all sealed buffers ready for sync
    python3 -m openclaw.scripts.buffer.rotate_buffer --vault-path "/path/to/vault" --list-sealed

    # Get path to active buffer (for writing)
    python3 -m openclaw.scripts.buffer.rotate_buffer --vault-path "/path/to/vault" --active-path

    # Clean up after sync: delete processed buffer
    python3 -m openclaw.scripts.buffer.rotate_buffer --vault-path "/path/to/vault" --cleanup --buffer-id 001

Output: JSON to stdout
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from datetime import datetime

from .. import state


MEMORY_DIR = ".second-brain/Memory"
BUFFER_PREFIX = "sync-buffer-"
ACTIVE_POINTER = "sync-buffer-active.txt"
DEFAULT_MAX_WORDS = 1500


def get_memory_path(vault_path: str) -> str:
    return os.path.join(vault_path, MEMORY_DIR)


def get_active_pointer_path(vault_path: str) -> str:
    return os.path.join(get_memory_path(vault_path), ACTIVE_POINTER)


def get_buffer_path(vault_path: str, buffer_id: str) -> str:
    return os.path.join(get_memory_path(vault_path), f"{BUFFER_PREFIX}{buffer_id}.md")


def read_active_id(vault_path: str) -> str:
    """Read the current active buffer ID from pointer file."""
    pointer_path = get_active_pointer_path(vault_path)
    if os.path.exists(pointer_path):
        with open(pointer_path, 'r') as f:
            return f.read().strip()
    return None


def write_active_id(vault_path: str, buffer_id: str):
    """Write the active buffer ID to pointer file."""
    pointer_path = get_active_pointer_path(vault_path)
    with open(pointer_path, 'w') as f:
        f.write(buffer_id)


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from buffer file."""
    if not content.startswith('---'):
        return {}
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
            result[key] = value
    return result


def count_words(content: str) -> int:
    """Count words in buffer content (excluding frontmatter)."""
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            content = content[end + 3:]
    return len(content.split())


def create_buffer(vault_path: str, buffer_id: str) -> str:
    """Create a new empty buffer file."""
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
    path = get_buffer_path(vault_path, buffer_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    write_active_id(vault_path, buffer_id)
    return path


def seal_buffer(vault_path: str, buffer_id: str) -> dict:
    """Seal a buffer (mark as ready for sync)."""
    path = get_buffer_path(vault_path, buffer_id)
    if not os.path.exists(path):
        return {"error": f"Buffer {buffer_id} not found"}

    with open(path, 'r') as f:
        content = f.read()

    now = datetime.now().astimezone().isoformat()
    words = count_words(content)

    # Update frontmatter
    content = re.sub(r'state:\s*\w+', 'state: sealed', content)
    content = re.sub(r'sealed_at:\s*\S+', f'sealed_at: {now}', content)
    content = re.sub(r'word_count:\s*\d+', f'word_count: {words}', content)

    with open(path, 'w') as f:
        f.write(content)

    return {"buffer_id": buffer_id, "state": "sealed", "sealed_at": now, "word_count": words}


def next_buffer_id(current_id: str) -> str:
    """Increment buffer ID (e.g., '001' -> '002')."""
    num = int(current_id) + 1
    return f"{num:03d}"


def list_buffer_files(vault_path: str) -> list:
    """List all sync buffer files (not the pointer)."""
    memory_path = get_memory_path(vault_path)
    pattern = os.path.join(memory_path, f"{BUFFER_PREFIX}*.md")
    files = glob.glob(pattern)
    results = []
    for f in sorted(files):
        filename = os.path.basename(f)
        # Extract buffer ID from filename
        match = re.search(r'sync-buffer-(\d+)\.md', filename)
        if not match:
            continue
        buffer_id = match.group(1)
        with open(f, 'r') as fh:
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


def check_status(vault_path: str, max_words: int) -> dict:
    """Check current active buffer status."""
    active_id = read_active_id(vault_path)
    if not active_id:
        return {"active_buffer": None, "needs_initialization": True}

    path = get_buffer_path(vault_path, active_id)
    if not os.path.exists(path):
        return {"active_buffer": active_id, "needs_initialization": True, "reason": "file missing"}

    with open(path, 'r') as f:
        content = f.read()

    meta = parse_frontmatter(content)
    words = count_words(content)

    return {
        "active_buffer": active_id,
        "word_count": words,
        "entry_count": int(meta.get("entry_count", 0)),
        "max_words": max_words,
        "needs_rotation": words >= max_words,
        "state": meta.get("state", "unknown"),
        "needs_initialization": False,
    }


def rotate(vault_path: str) -> dict:
    """Seal current buffer, create new active buffer."""
    active_id = read_active_id(vault_path)

    if not active_id:
        # No active buffer — create first one
        create_buffer(vault_path, "001")
        return {"action": "initialized", "new_active": "001"}

    # Seal current
    seal_result = seal_buffer(vault_path, active_id)
    if "error" in seal_result:
        return seal_result

    # Create new
    new_id = next_buffer_id(active_id)
    create_buffer(vault_path, new_id)

    return {
        "action": "rotated",
        "sealed": active_id,
        "sealed_word_count": seal_result["word_count"],
        "new_active": new_id,
    }


def get_active_path(vault_path: str) -> dict:
    """Get the path to the currently active buffer."""
    active_id = read_active_id(vault_path)
    if not active_id:
        # Initialize first buffer
        path = create_buffer(vault_path, "001")
        return {"active_buffer": "001", "path": path, "initialized": True}

    path = get_buffer_path(vault_path, active_id)
    if not os.path.exists(path):
        path = create_buffer(vault_path, active_id)
        return {"active_buffer": active_id, "path": path, "recreated": True}

    return {"active_buffer": active_id, "path": path}


def list_sealed(vault_path: str) -> list:
    """List only sealed buffers (ready for sync)."""
    all_buffers = list_buffer_files(vault_path)
    return [b for b in all_buffers if b["state"] == "sealed"]


def cleanup_buffer(vault_path: str, buffer_id: str, archive_dir: str = None) -> dict:
    """Archive and delete a processed buffer."""
    path = get_buffer_path(vault_path, buffer_id)
    if not os.path.exists(path):
        return {"action": "skipped", "reason": "file not found", "buffer_id": buffer_id}

    # Archive if archive dir specified
    if archive_dir:
        archive_path = os.path.join(
            get_memory_path(vault_path),
            "sync-archive",
            f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{buffer_id}.md"
        )
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(path, 'r') as src:
            content = src.read()
        with open(archive_path, 'w') as dst:
            dst.write(content)

    os.remove(path)

    # Reset IDs if no sealed buffers remain
    remaining_sealed = list_sealed(vault_path)
    if not remaining_sealed:
        active_id = read_active_id(vault_path)
        if active_id and int(active_id) > 1:
            # Rename active buffer to 001
            old_path = get_buffer_path(vault_path, active_id)
            new_path = get_buffer_path(vault_path, "001")
            if os.path.exists(old_path) and old_path != new_path:
                # Update frontmatter
                with open(old_path, 'r') as f:
                    content = f.read()
                content = re.sub(r'buffer_id:\s*"\d+"', 'buffer_id: "001"', content)
                with open(new_path, 'w') as f:
                    f.write(content)
                os.remove(old_path)
                write_active_id(vault_path, "001")

    return {"action": "cleaned", "buffer_id": buffer_id}


def sync_check(vault_path: str, memory_path: str = None) -> dict:
    """
    Pre-flight check for the Lobster sync pipeline (--sync-check mode).

    Seals the active buffer if it has entries, concatenates all sealed buffer
    content, writes it to MEMORY_PATH/run/buffer-content.txt, and returns the
    file path as buffer_content_file. The downstream run_extraction.py reads
    from that file — this avoids shell interpolation of raw text in Lobster YAML.

    Returns JSON-ready dict.
    """
    empty = {
        "has_content":         False,
        "should_exit":         True,
        "sealed_buffers":      [],
        "buffer_content_file": "",
        "entry_count":         0,
    }

    active_id = read_active_id(vault_path)
    if not active_id:
        return empty

    active_path = get_buffer_path(vault_path, active_id)
    if os.path.exists(active_path):
        with open(active_path, "r") as f:
            content = f.read()
        meta  = parse_frontmatter(content)
        words = count_words(content)
        count = int(meta.get("entry_count", 0))

        if words > 0 and count > 0:
            # Seal the active buffer so it's included in the sync
            seal_buffer(vault_path, active_id)
            new_id = next_buffer_id(active_id)
            create_buffer(vault_path, new_id)

    # Collect all sealed buffers
    sealed = list_sealed(vault_path)
    if not sealed:
        return empty

    # Concatenate content from all sealed buffers (oldest first)
    parts = []
    total_entries = 0
    for buf in sealed:
        buf_path = buf.get("path", "")
        if os.path.exists(buf_path):
            with open(buf_path, "r") as f:
                buf_content = f.read()
            # Strip frontmatter
            if buf_content.startswith("---"):
                end = buf_content.find("---", 3)
                if end != -1:
                    buf_content = buf_content[end + 3:].strip()
            parts.append(buf_content)
            total_entries += buf.get("entry_count", 0)

    combined = "\n\n---\n\n".join(parts)

    # Write to file so run_extraction.py can read without shell interpolation
    derived_memory = memory_path or get_memory_path(vault_path)
    run_dir = os.path.join(derived_memory, "run")
    content_file = os.path.join(run_dir, "buffer-content.txt")
    try:
        os.makedirs(run_dir, exist_ok=True)
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(combined)
    except Exception as e:
        print(json.dumps({"warn": f"could not write buffer-content file: {e}"}),
              file=sys.stderr)
        content_file = ""

    return {
        "has_content":         bool(parts),
        "should_exit":         not bool(parts),
        "sealed_buffers":      sealed,
        "buffer_content_file": content_file,
        "entry_count":         total_entries,
    }


def run(
    *,
    vault_path: str,
    memory_path: str | None = None,
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
) -> dict | list:
    if sync_check_mode:
        result = sync_check(vault_path, memory_path=memory_path)
        if memory_path and result.get("sealed_buffers"):
            state.write_state(memory_path, {
                "rotate_buffer_sealed_buffers": result["sealed_buffers"],
            })
        return result
    if check:
        return check_status(vault_path, max_words)
    if rotate_mode:
        return rotate(vault_path)
    if list_sealed_mode:
        return list_sealed(vault_path)
    if list_all:
        return list_buffer_files(vault_path)
    if active_path:
        return get_active_path(vault_path)
    if cleanup:
        if not buffer_id:
            raise RuntimeError("provide --buffer-id for cleanup")
        return cleanup_buffer(vault_path, buffer_id, "archive" if archive else None)
    raise RuntimeError("provide one of: --check, --rotate, --list-sealed, --list-all, --active-path, --cleanup")
