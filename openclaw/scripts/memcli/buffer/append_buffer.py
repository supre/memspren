"""append_buffer.py — Append an entry to the active sync buffer.

Finds the active buffer (auto-rotating if over the word limit), appends the
entry content, then updates frontmatter: word_count, entry_count, last_updated.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .rotate_buffer import (
    DEFAULT_MAX_WORDS,
    count_words,
    get_active_buffer_with_rotation,
)
from ..log import Logger
from ..paths import VaultPaths


def _split_frontmatter(content: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). frontmatter_block includes both --- delimiters."""
    if not content.startswith("---"):
        return "", content
    end = content.find("---", 3)
    if end == -1:
        return "", content
    return content[: end + 3], content[end + 3 :]


def run(
    *,
    vault_path: str,
    content: str = "",
    content_file: Path | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()
    buffers_dir = str(paths.buffers)

    # Resolve entry text
    if content_file is not None:
        if not Path(content_file).exists():
            raise RuntimeError(f"content file not found: {content_file}")
        entry_text = Path(content_file).read_text(encoding="utf-8").strip()
    elif content:
        entry_text = content.strip()
    else:
        raise RuntimeError("provide --content or --content-file")

    if not entry_text:
        raise RuntimeError("entry content is empty")

    # Get or create active buffer — auto-rotates if over word limit
    buf = get_active_buffer_with_rotation(buffers_dir, max_words)
    buf_path = Path(buf["path"])
    rotated = buf["rotated"]

    if rotated:
        log.info("buffer rotated before append", new_buffer=buf_path.name)

    current_content = buf_path.read_text(encoding="utf-8") if buf_path.exists() else ""
    fm_block, old_body = _split_frontmatter(current_content)

    # Append entry — blank line separator if body already has content
    if old_body.strip():
        new_body = old_body.rstrip() + "\n\n" + entry_text + "\n"
    else:
        new_body = "\n\n" + entry_text + "\n"

    updated_content = fm_block + new_body

    # Recount words from updated body (count_words strips frontmatter internally)
    new_word_count = count_words(updated_content)
    new_entry_count = (buf.get("entry_count") or 0) + 1
    now = datetime.now().astimezone().isoformat()

    # Update word_count and entry_count
    fm_block = re.sub(r"(word_count:\s*)\d+", rf"\g<1>{new_word_count}", fm_block)
    fm_block = re.sub(r"(entry_count:\s*)\d+", rf"\g<1>{new_entry_count}", fm_block)

    # Update last_updated — insert before closing --- if not already present
    if re.search(r"^last_updated:", fm_block, re.MULTILINE):
        fm_block = re.sub(
            r"(last_updated:\s*)\S+",
            rf"\g<1>{now}",
            fm_block,
            flags=re.MULTILINE,
        )
    else:
        fm_block = fm_block[:-3].rstrip() + f"\nlast_updated: {now}\n---"

    buf_path.write_text(fm_block + new_body, encoding="utf-8")

    m = re.search(r"sync-buffer-(\d+)\.md", buf_path.name)
    buffer_id = m.group(1) if m else "?"

    log.info(
        "buffer entry appended",
        buffer_id=buffer_id,
        entry_count=new_entry_count,
        word_count=new_word_count,
        rotated=rotated,
    )

    return {
        "ok": True,
        "buffer_id": buffer_id,
        "buffer_path": str(buf_path),
        "entry_count": new_entry_count,
        "word_count": new_word_count,
        "rotated": rotated,
    }
