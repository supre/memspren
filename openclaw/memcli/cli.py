"""
cli.py — memcli Click command dispatcher.

Each pipeline step module exports a `run()` function with typed keyword
parameters. This CLI layer handles argument parsing (Click), JSON
serialization, and error formatting. No module is executed as a standalone
process — all logic flows through `run()`.
"""

from __future__ import annotations

import datetime
import json
import sys
import tempfile
from pathlib import Path

import click

_LOG_PATH = tempfile.gettempdir() + "/memcli.log"


def _log(cmd_name: str, kwargs: dict) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    args_str = " ".join(f"--{k}={v}" for k, v in kwargs.items() if v is not None and v is not False and v != "")
    line = f"[{ts}] {cmd_name} {args_str}\n"
    try:
        with open(_LOG_PATH, "a") as f:
            f.write(line)
    except OSError:
        pass


def _exec(cmd_name: str, fn, **kwargs):
    """Call a step's run() function, print JSON result, handle errors."""
    _log(cmd_name, kwargs)
    try:
        result = fn(**kwargs)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)
    print(json.dumps(result))


@click.group()
def cli() -> None:
    """memcli — memspren pipeline command dispatcher."""


# ── Stage 0: Pre-flight ─────────────────────────────────────────────────────

@cli.command("write-lock")
@click.option("--memory-path", required=True, type=click.Path())
@click.option("--release", is_flag=True, default=False)
@click.option("--prune-tokens-older-than-hours", type=float, default=None)
@click.option("--stale-lock-hours", type=float, default=2.0)
def write_lock_cmd(memory_path, release, prune_tokens_older_than_hours, stale_lock_hours):
    """Acquire or release the sync lock file."""
    from .preflight.write_lock import run
    _exec("write-lock", run,
          memory_path=Path(memory_path),
          release=release,
          prune_tokens_older_than_hours=prune_tokens_older_than_hours,
          stale_lock_hours=stale_lock_hours)


@cli.command("check-cli")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--vault", "vault_name", default="")
@click.option("--memory-path", default=None, type=click.Path())
@click.option("--json", "json_mode", is_flag=True, default=False)
def check_cli_cmd(vault_path, vault_name, memory_path, json_mode):
    """Verify obsidian-cli availability and resolve write mode."""
    from .preflight.check_cli import run
    _exec("check-cli", run,
          vault_path=Path(vault_path),
          vault_name=vault_name,
          memory_path=Path(memory_path) if memory_path else None,
          json_mode=json_mode)


@cli.command("clean-exit")
@click.option("--message", default="Nothing to sync.")
@click.option("--release-lock", is_flag=True, default=False)
@click.option("--memory-path", default=None, type=click.Path())
def clean_exit_cmd(message, release_lock, memory_path):
    """Emit a clean exit signal when there is nothing to sync."""
    from .preflight.clean_exit import run
    _exec("clean-exit", run,
          message=message,
          release_lock=release_lock,
          memory_path=Path(memory_path) if memory_path else None)


# ── Stage 1: Buffer management ─────────────────────────────────────────────

@cli.command("rotate-buffer")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--memory-path", default=None, type=click.Path())
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
def rotate_buffer_cmd(vault_path, memory_path, sync_check_mode, check, rotate_mode,
                      list_sealed_mode, list_all, active_path, cleanup, buffer_id, archive, max_words):
    """Manage rotating sync buffers."""
    from .buffer.rotate_buffer import run
    _exec("rotate-buffer", run,
          vault_path=vault_path,
          memory_path=memory_path,
          sync_check_mode=sync_check_mode,
          check=check,
          rotate_mode=rotate_mode,
          list_sealed_mode=list_sealed_mode,
          list_all=list_all,
          active_path=active_path,
          cleanup=cleanup,
          buffer_id=buffer_id,
          archive=archive,
          max_words=max_words)


# ── Stage 2: Scanning ──────────────────────────────────────────────────────

@cli.command("vault-diff")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--memory-path", required=True, type=click.Path())
@click.option("--since", default=None)
def vault_diff_cmd(vault_path, memory_path, since):
    """Scan vault for manually changed files since last sync."""
    from .scanning.vault_diff_scanner import run
    _exec("vault-diff", run,
          vault_path=Path(vault_path),
          memory_path=Path(memory_path),
          since=since)


@cli.command("task-inbox")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--memory-path", default=None, type=click.Path())
@click.option("--dedup-threshold", type=float, default=0.85)
def task_inbox_cmd(vault_path, memory_path, dedup_threshold):
    """Parse tasks-inbox.md and extract open/completed tasks."""
    from .scanning.task_inbox_scanner import run
    _exec("task-inbox", run,
          vault_path=Path(vault_path),
          memory_path=Path(memory_path) if memory_path else None,
          dedup_threshold=dedup_threshold)


@cli.command("read-frontmatter")
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--classifiers", required=True)
@click.option("--memory-path", default=None, type=click.Path())
def read_frontmatter_cmd(vault_path, classifiers, memory_path):
    """Batch-read YAML frontmatter from classifier-scoped vault folders."""
    from .scanning.read_frontmatter import run
    _exec("read-frontmatter", run,
          vault_path=Path(vault_path),
          classifiers=classifiers,
          memory_path=Path(memory_path) if memory_path else None)


# ── Stage 3: Extraction ────────────────────────────────────────────────────

@cli.command("run-extraction")
@click.option("--buffer-content-file", required=True, type=click.Path())
@click.option("--manual-edits-file", required=True, type=click.Path())
@click.option("--agent", default="main")
@click.option("--memory-path", required=True, type=click.Path())
@click.option("--timeout", type=int, default=120)
def run_extraction_cmd(buffer_content_file, manual_edits_file, agent, memory_path, timeout):
    """Call LLM extraction via OpenClaw Gateway."""
    from .extraction.run_extraction import run
    _exec("run-extraction", run,
          buffer_content_file=Path(buffer_content_file),
          manual_edits_file=Path(manual_edits_file),
          agent=agent,
          memory_path=Path(memory_path),
          timeout=timeout)


# ── Stage 4: Memory refinement ─────────────────────────────────────────────

@cli.command("parallel-memory")
@click.option("--extraction-file", required=True, type=click.Path())
@click.option("--task-inbox-file", required=True, type=click.Path())
@click.option("--memory-path", required=True, type=click.Path())
def parallel_memory_cmd(extraction_file, task_inbox_file, memory_path):
    """Dispatch 4 parallel memory refinement jobs via Gateway."""
    from .memory.parallel_memory import run
    _exec("parallel-memory", run,
          extraction_file=Path(extraction_file),
          task_inbox_file=Path(task_inbox_file),
          memory_path=Path(memory_path))


@cli.command("merge-layer1")
@click.option("--memory-path", required=True, type=click.Path())
def merge_layer1_cmd(memory_path):
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

    _exec("merge-layer1", run,
          memory_path=Path(memory_path),
          parallel_results=parallel_results)


# ── Stage 5: Entity planning & writes ─────────────────────────────────────

@cli.command("entity-plan")
@click.option("--extraction-file", required=True, type=click.Path())
@click.option("--frontmatter-file", default="")
@click.option("--task-inbox-file", default="")
@click.option("--agent", default="memspren-heavy")
@click.option("--timeout", type=int, default=120)
def entity_plan_cmd(extraction_file, frontmatter_file, task_inbox_file, agent, timeout):
    """Generate entity write plan via LLM."""
    from .entities.run_entity_plan import run
    _exec("entity-plan", run,
          extraction_file=Path(extraction_file),
          frontmatter_file=frontmatter_file,
          task_inbox_file=task_inbox_file,
          agent=agent,
          timeout=timeout)


@cli.command("entity-pipeline")
@click.option("--plan", required=True)
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--vault-name", default="")
@click.option("--write-mode", default="filesystem", type=click.Choice(["obsidian", "filesystem"]))
@click.option("--memory-path", required=True, type=click.Path())
def entity_pipeline_cmd(plan, vault_path, vault_name, write_mode, memory_path):
    """Run per-entity content generation, linking, and vault writes."""
    from .entities.entity_pipeline import run
    _exec("entity-pipeline", run,
          plan=plan,
          vault_path=Path(vault_path),
          vault_name=vault_name,
          write_mode=write_mode,
          memory_path=Path(memory_path))


# ── Stage 6: Metrics & finalization ────────────────────────────────────────

@cli.command("metrics")
@click.option("--memory-path", required=True, type=click.Path())
@click.option("--vault-path", required=True, type=click.Path())
@click.option("--write-mode", default="filesystem")
@click.option("--vault-name", default="")
@click.option("--extraction-result", default="{}")
@click.option("--layer1-result", default="{}")
@click.option("--entity-result", default="{}")
@click.option("--vault-diff-result", default="{}")
@click.option("--sealed-buffers", default="[]")
@click.option("--entity-writes-ok", default="false")
@click.option("--max-log-bytes", type=int, default=2097152)
@click.option("--keep-lines", type=int, default=2000)
def metrics_cmd(memory_path, vault_path, write_mode, vault_name,
                extraction_result, layer1_result, entity_result, vault_diff_result,
                sealed_buffers, entity_writes_ok, max_log_bytes, keep_lines):
    """Write metrics.json, archive buffers, update system-state.md."""
    from .finalize.metrics_writer import run
    _exec("metrics", run,
          memory_path=Path(memory_path),
          vault_path=Path(vault_path),
          write_mode=write_mode,
          vault_name=vault_name,
          extraction_result=extraction_result,
          layer1_result=layer1_result,
          entity_result=entity_result,
          vault_diff_result=vault_diff_result,
          sealed_buffers=sealed_buffers,
          entity_writes_ok=entity_writes_ok,
          max_log_bytes=max_log_bytes,
          keep_lines=keep_lines)


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
