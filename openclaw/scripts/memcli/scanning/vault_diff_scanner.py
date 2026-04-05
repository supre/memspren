"""vault_diff_scanner.py — Scan vault for manually changed files since last sync."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .. import state
from ..log import Logger
from ..paths import VaultPaths


def _parse_since_timestamp(since: str | None) -> datetime | None:
    if not since:
        return None
    value = since.strip()
    if value.lower() in ("null", "none", ""):
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _file_change_epoch_seconds(path: Path) -> float | None:
    try:
        st = path.stat()
    except Exception:
        return None
    created_ts = getattr(st, "st_birthtime", None)
    if created_ts is None:
        created_ts = st.st_ctime
    return max(st.st_mtime, created_ts)


def run(
    *,
    vault_path: Path,
    since: str | None = None,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()
    empty = {"changed_files": [], "changed_files_content_file": "", "changed_count": 0}

    if not since:
        since = state.get_field(str(paths.run), "check_cli_last_sync")
    if not since:
        system_state_path = paths.memory / "system-state.md"
        if system_state_path.exists():
            try:
                for line in system_state_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("last_sync:"):
                        since = line.split(":", 1)[1].strip()
                        break
            except Exception:
                pass

    since_dt = _parse_since_timestamp(since)

    if not vault_path.exists():
        log.warn("vault path not found", vault_path=str(vault_path))
        return empty

    if since_dt is None:
        log.info("no prior successful sync timestamp found; skipping manual edit ingestion")
        return empty

    changed_files: list[str] = []
    since_epoch = since_dt.timestamp()
    for full_path in vault_path.rglob("*.md"):
        try:
            rel_path = full_path.relative_to(vault_path).as_posix()
        except Exception:
            continue
        if "/.second-brain/" in f"/{rel_path}" or rel_path.startswith(".second-brain/"):
            continue
        changed_ts = _file_change_epoch_seconds(full_path)
        if changed_ts is None:
            continue
        if changed_ts > since_epoch:
            changed_files.append(rel_path)

    content_parts: list[str] = []
    valid_files: list[str] = []
    for rel_path in changed_files:
        full_path = vault_path / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
            content_parts.append(f"=== {rel_path} ===\n{content}\n")
            valid_files.append(rel_path)
        except Exception:
            pass

    combined = "\n".join(content_parts)

    content_file = str(paths.run / "manual-edits.txt")
    try:
        (paths.run / "manual-edits.txt").write_text(combined, encoding="utf-8")
    except Exception as e:
        log.warn(f"could not write manual-edits file: {e}")
        content_file = ""

    log.info("vault diff scan complete", changed_count=len(valid_files))

    state.write_state(str(paths.run), {"vault_diff_changed_count": len(valid_files)})

    return {
        "changed_files": valid_files,
        "changed_files_content_file": content_file,
        "changed_count": len(valid_files),
    }
