"""
cli.py — memcli Click command dispatcher.

Every pipeline script is registered here as a Click command. The commands
use the stub pattern: reconstruct sys.argv and delegate to the module's
existing argparse-based main() function.  This keeps argparse logic intact
with zero regressions; individual commands can migrate to native Click
@click.option declarations incrementally.

Usage:
    memcli write-lock --memory-path /path/to/Memory
    memcli run-extraction --buffer-content-file ... --manual-edits-file ...
"""

from __future__ import annotations

import sys

import click


@click.group()
def cli() -> None:
    """memcli — memspren pipeline command dispatcher."""


# ── Helper ─────────────────────────────────────────────────────────────────

def _run(main_fn, cmd_name: str, extra_args: tuple) -> None:
    """Reconstruct sys.argv and call a module's main()."""
    old_argv = sys.argv[:]
    sys.argv = [cmd_name] + list(extra_args)
    try:
        main_fn()
    finally:
        sys.argv = old_argv


# ── Stage 0: Pre-flight ─────────────────────────────────────────────────────

@cli.command("write-lock", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def write_lock_cmd(ctx: click.Context) -> None:
    """Acquire or release the sync lock file."""
    from .preflight.write_lock import main
    _run(main, "write-lock", ctx.args)


@cli.command("check-cli", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def check_cli_cmd(ctx: click.Context) -> None:
    """Verify obsidian-cli availability and resolve write mode."""
    from .preflight.check_cli import main
    _run(main, "check-cli", ctx.args)


@cli.command("clean-exit", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def clean_exit_cmd(ctx: click.Context) -> None:
    """Emit a clean exit signal when there is nothing to sync."""
    from .preflight.clean_exit import main
    _run(main, "clean-exit", ctx.args)


# ── Stage 1: Buffer management ─────────────────────────────────────────────

@cli.command("rotate-buffer", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def rotate_buffer_cmd(ctx: click.Context) -> None:
    """Manage rotating sync buffers (check, rotate, seal, cleanup)."""
    from .buffer.rotate_buffer import main
    _run(main, "rotate-buffer", ctx.args)


# ── Stage 2: Scanning ──────────────────────────────────────────────────────

@cli.command("vault-diff", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def vault_diff_cmd(ctx: click.Context) -> None:
    """Scan vault for manually changed files since last sync."""
    from .scanning.vault_diff_scanner import main
    _run(main, "vault-diff", ctx.args)


@cli.command("task-inbox", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def task_inbox_cmd(ctx: click.Context) -> None:
    """Parse tasks-inbox.md and extract open/completed tasks."""
    from .scanning.task_inbox_scanner import main
    _run(main, "task-inbox", ctx.args)


@cli.command("read-frontmatter", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def read_frontmatter_cmd(ctx: click.Context) -> None:
    """Batch-read YAML frontmatter from classifier-scoped vault folders."""
    from .scanning.read_frontmatter import main
    _run(main, "read-frontmatter", ctx.args)


# ── Stage 3: Extraction ────────────────────────────────────────────────────

@cli.command("run-extraction", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def run_extraction_cmd(ctx: click.Context) -> None:
    """Call LLM extraction via OpenClaw Gateway."""
    from .extraction.run_extraction import main
    _run(main, "run-extraction", ctx.args)


# ── Stage 4: Memory refinement ─────────────────────────────────────────────

@cli.command("parallel-memory", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def parallel_memory_cmd(ctx: click.Context) -> None:
    """Dispatch 4 parallel memory refinement jobs via Gateway."""
    from .memory.parallel_memory import main
    _run(main, "parallel-memory", ctx.args)


@cli.command("merge-layer1", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def merge_layer1_cmd(ctx: click.Context) -> None:
    """Collect parallel refinement results and write memory files (reads stdin)."""
    from .memory.merge import main
    _run(main, "merge-layer1", ctx.args)


# ── Stage 5: Entity planning & writes ─────────────────────────────────────

@cli.command("entity-plan", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def entity_plan_cmd(ctx: click.Context) -> None:
    """Generate entity write plan via LLM."""
    from .entities.run_entity_plan import main
    _run(main, "entity-plan", ctx.args)


@cli.command("entity-pipeline", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def entity_pipeline_cmd(ctx: click.Context) -> None:
    """Run per-entity content generation, linking, and vault writes."""
    from .entities.entity_pipeline import main
    _run(main, "entity-pipeline", ctx.args)


# ── Stage 6: Metrics & finalization ────────────────────────────────────────

@cli.command("metrics", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def metrics_cmd(ctx: click.Context) -> None:
    """Write metrics.json, archive buffers, update system-state.md."""
    from .finalize.metrics_writer import main
    _run(main, "metrics", ctx.args)


def main() -> None:
    import json as _json
    try:
        cli(standalone_mode=False)
    except SystemExit:
        raise  # commands use sys.exit() to signal their own exit codes — let them through
    except click.exceptions.UsageError as exc:
        print(_json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(2)
    except Exception as exc:
        print(_json.dumps({"ok": False, "error": f"internal error: {exc}"}))
        sys.exit(1)
