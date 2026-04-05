"""
cli.py — memcli Click command dispatcher.

Each command creates a Logger and VaultPaths, then calls the module's run().
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .log import make_logger, Level
from .paths import VaultPaths

VERBOSITY_CHOICES = click.Choice(["debug", "info", "warn", "error"])


def _exec(cmd_name: str, fn, log_dir: Path | None, verbosity: str, **kwargs):
    """Call a step's run() function with a Logger, print JSON result, handle errors."""
    log = make_logger(cmd_name, verbosity=verbosity, log_dir=log_dir)
    log.debug(f"starting {cmd_name}", **{k: str(v) for k, v in kwargs.items() if v is not None and v is not False and v != ""})
    try:
        result = fn(**kwargs, log=log)
    except RuntimeError as exc:
        log.error(f"{cmd_name} failed", error=str(exc))
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)
    print(json.dumps(result))


def _log_dir(vault_path: str | None) -> Path | None:
    if vault_path:
        return Path("/tmp/memcli")
    return None


@click.group()
def cli() -> None:
    """memcli — memspren pipeline command dispatcher."""


# ── Stage 0: Pre-flight ─────────────────────────────────────────────────────

@cli.command("write-lock")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--release", is_flag=True, default=False)
@click.option("--prune-tokens-older-than-hours", type=float, default=None)
@click.option("--stale-lock-hours", type=float, default=2.0)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def write_lock_cmd(vault_path, release, prune_tokens_older_than_hours, stale_lock_hours, verbosity):
    """Acquire or release the sync lock file."""
    from .preflight.write_lock import run
    _exec("write-lock", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), release=release,
          prune_tokens_older_than_hours=prune_tokens_older_than_hours,
          stale_lock_hours=stale_lock_hours)


@cli.command("check-cli")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--vault", "vault_name", default="")
@click.option("--json", "json_mode", is_flag=True, default=False)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def check_cli_cmd(vault_path, vault_name, json_mode, verbosity):
    """Verify obsidian-cli availability and resolve write mode."""
    from .preflight.check_cli import run
    _exec("check-cli", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), vault_name=vault_name, json_mode=json_mode)


@cli.command("clean-exit")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--message", default="Nothing to sync.")
@click.option("--release-lock", is_flag=True, default=False)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def clean_exit_cmd(vault_path, message, release_lock, verbosity):
    """Emit a clean exit signal when there is nothing to sync."""
    from .preflight.clean_exit import run
    _exec("clean-exit", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), message=message, release_lock=release_lock)


@cli.command("sync-gate")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def sync_gate_cmd(vault_path, verbosity):
    """Halt the pipeline if rotate-buffer found nothing to sync. Exits 1 (clean) if nothing to do."""
    from .preflight.sync_gate import run
    from .paths import VaultPaths
    log = make_logger("sync-gate", verbosity=verbosity, log_dir=_log_dir(vault_path))
    paths = VaultPaths(vault_path)
    paths.ensure()
    run(vault_path=vault_path, log=log)


# ── Stage 1: Buffer management ─────────────────────────────────────────────

@cli.command("rotate-buffer")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--sync-check", "sync_check_mode", is_flag=True, default=False)
@click.option("--check", is_flag=True, default=False)
@click.option("--rotate", "rotate_mode", is_flag=True, default=False)
@click.option("--list-sealed", "list_sealed_mode", is_flag=True, default=False)
@click.option("--list-all", is_flag=True, default=False)
@click.option("--active-path", is_flag=True, default=False)
@click.option("--cleanup", is_flag=True, default=False)
@click.option("--buffer-id", default="")
@click.option("--archive", is_flag=True, default=True)
@click.option("--max-words", type=int, default=1500)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def rotate_buffer_cmd(vault_path, sync_check_mode, check, rotate_mode,
                      list_sealed_mode, list_all, active_path, cleanup,
                      buffer_id, archive, max_words, verbosity):
    """Manage rotating sync buffers."""
    from .buffer.rotate_buffer import run
    _exec("rotate-buffer", run, _log_dir(vault_path), verbosity,
          vault_path=vault_path,
          sync_check_mode=sync_check_mode, check=check, rotate_mode=rotate_mode,
          list_sealed_mode=list_sealed_mode, list_all=list_all, active_path=active_path,
          cleanup=cleanup, buffer_id=buffer_id, archive=archive, max_words=max_words)


@cli.command("append-buffer")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--content", default="", help="Entry text to append (use --content-file for multi-line content).")
@click.option("--content-file", default=None, type=click.Path(), help="Path to a file containing the entry text.")
@click.option("--max-words", type=int, default=1500)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def append_buffer_cmd(vault_path, content, content_file, max_words, verbosity):
    """Append an entry to the active sync buffer.

    Finds the active buffer, auto-rotates if over the word limit, appends the
    entry, and updates word_count, entry_count, and last_updated in frontmatter.

    Output: {"ok": true, "buffer_id": "...", "entry_count": N, "word_count": N, "rotated": bool}
    """
    from .buffer.append_buffer import run
    _exec("append-buffer", run, _log_dir(vault_path), verbosity,
          vault_path=vault_path,
          content=content,
          content_file=Path(content_file) if content_file else None,
          max_words=max_words)


@cli.command("get-active-buffer")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--max-words", type=int, default=1500)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def get_active_buffer_cmd(vault_path, max_words, verbosity):
    """Return path to the active sync buffer, rotating if over the word limit.

    Output: {"path": "...", "rotated": bool, "entry_count": N}
    Use this before appending any entry during conversation.
    """
    from .buffer.rotate_buffer import get_active_buffer_with_rotation
    from .paths import VaultPaths
    log = make_logger("get-active-buffer", verbosity=verbosity)
    paths = VaultPaths(vault_path)
    paths.ensure()
    result = get_active_buffer_with_rotation(str(paths.buffers), max_words)
    log.debug("active buffer", **{k: str(v) for k, v in result.items()})
    print(json.dumps(result))


@cli.command("setup")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--vault-name", default="")
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def setup_cmd(vault_path, vault_name, verbosity):
    """Idempotent vault scaffold — creates missing folders, seed files, memory stubs, and git repo.

    Safe to call at any time. Never overwrites existing content.
    """
    from .setup import run
    _exec("setup", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), vault_name=vault_name)


# ── Stage 2: Scanning ──────────────────────────────────────────────────────

@cli.command("vault-diff")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--since", default=None)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def vault_diff_cmd(vault_path, since, verbosity):
    """Scan vault for manually changed files since last sync."""
    from .scanning.vault_diff_scanner import run
    _exec("vault-diff", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), since=since)


@cli.command("task-inbox")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--dedup-threshold", type=float, default=0.85)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def task_inbox_cmd(vault_path, dedup_threshold, verbosity):
    """Parse tasks-inbox.md and extract open/completed tasks."""
    from .scanning.task_inbox_scanner import run
    _exec("task-inbox", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), dedup_threshold=dedup_threshold)


@cli.command("read-frontmatter")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--classifiers", required=True)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def read_frontmatter_cmd(vault_path, classifiers, verbosity):
    """Batch-read YAML frontmatter from classifier-scoped vault folders."""
    from .scanning.read_frontmatter import run
    _exec("read-frontmatter", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), classifiers=classifiers)


# ── Stage 3: Extraction ────────────────────────────────────────────────────

@cli.command("run-extraction")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--buffer-content-file", required=True, type=click.Path())
@click.option("--manual-edits-file", required=True, type=click.Path())
@click.option("--agent", default="main")
@click.option("--timeout", type=int, default=600)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def run_extraction_cmd(vault_path, buffer_content_file, manual_edits_file, agent, timeout, verbosity):
    """Call LLM extraction via OpenClaw Gateway."""
    from .extraction.run_extraction import run
    _exec("run-extraction", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path),
          buffer_content_file=Path(buffer_content_file),
          manual_edits_file=Path(manual_edits_file),
          agent=agent, timeout=timeout)


# ── Stage 4: memory refinement ─────────────────────────────────────────────

@cli.command("parallel-memory")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--extraction-file", required=True, type=click.Path())
@click.option("--task-inbox-file", required=True, type=click.Path())
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def parallel_memory_cmd(vault_path, extraction_file, task_inbox_file, verbosity):
    """Dispatch 4 parallel memory refinement jobs via Gateway."""
    from .memory.parallel_memory import run
    _exec("parallel-memory", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path),
          extraction_file=Path(extraction_file),
          task_inbox_file=Path(task_inbox_file))


@cli.command("merge-layer1")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def merge_layer1_cmd(vault_path, verbosity):
    """Collect parallel refinement results and write memory files (reads stdin)."""
    from .memory.merge import run

    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        print(json.dumps({
            "ok": False, "error": "empty input from parallel_memory",
            "written": [], "fallback": [], "summary": "",
        }))
        sys.exit(1)

    try:
        parallel_results = json.loads(stdin_text)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "ok": False, "error": f"invalid results JSON: {e}",
            "written": [], "fallback": [], "summary": "",
        }))
        sys.exit(1)

    _exec("merge-layer1", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), parallel_results=parallel_results)


# ── Stage 5: Entity planning, writing & linking ──────────────────────────

@cli.command("entity-plan")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--buffer-content-file", required=True, type=click.Path())
@click.option("--manual-edits-file", required=True, type=click.Path())
@click.option("--frontmatter-file", default="")
@click.option("--agent", default="main")
@click.option("--timeout", type=int, default=600)
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def entity_plan_cmd(vault_path, buffer_content_file, manual_edits_file,
                    frontmatter_file, agent, timeout, verbosity):
    """Generate entity write plan from raw buffer content via LLM."""
    from .entities.run_entity_plan import run
    _exec("entity-plan", run, _log_dir(vault_path), verbosity,
          buffer_content_file=Path(buffer_content_file),
          manual_edits_file=Path(manual_edits_file),
          frontmatter_file=frontmatter_file,
          agent=agent, timeout=timeout)


@cli.command("entity-write")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--plan", required=True)
@click.option("--vault-name", default="")
@click.option("--write-mode", default="filesystem", type=click.Choice(["obsidian", "filesystem"]))
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def entity_write_cmd(vault_path, plan, vault_name, write_mode, verbosity):
    """Write entities to vault (create directly, merge existing via LLM)."""
    from .entities.entity_writer import run
    _exec("entity-write", run, _log_dir(vault_path), verbosity,
          plan=plan, vault_path=Path(vault_path),
          vault_name=vault_name, write_mode=write_mode)


@cli.command("entity-link")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--written-entities", default="[]")
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def entity_link_cmd(vault_path, written_entities, verbosity):
    """Determine and write wikilinks for newly written entities."""
    from .entities.entity_linker import run
    _exec("entity-link", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path),
          written_entities=written_entities)


# ── Stage 6: Metrics & finalization ────────────────────────────────────────

@cli.command("metrics")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--write-mode", default="filesystem")
@click.option("--vault-name", default="")
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def metrics_cmd(vault_path, write_mode, vault_name, verbosity):
    """Write metrics.json, archive buffers, update system-state.md."""
    from .finalize.metrics_writer import run
    _exec("metrics", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path), write_mode=write_mode, vault_name=vault_name)


@cli.command("archive-run")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--verbosity", default="debug", type=VERBOSITY_CHOICES)
def archive_run_cmd(vault_path, verbosity):
    """Move all run/ artifacts to run/archive/ with a timestamp suffix."""
    from .finalize.archive_run import run
    _exec("archive-run", run, _log_dir(vault_path), verbosity,
          vault_path=Path(vault_path))


def main() -> None:
    try:
        cli(standalone_mode=False)
    except SystemExit:
        raise
    except click.exceptions.UsageError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(2)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"internal error: {exc}"}))
        sys.exit(1)
