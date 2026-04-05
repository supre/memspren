# memspren sync pipeline — deterministic Lobster-based workflow
#
# CRITICAL: Every script step must emit valid JSON to stdout only.
# All debug/logging output must go to stderr. The runner wrapper
# (uv run -m scripts.runner) enforces this contract and routes stderr
# to the telemetry log. Any stray stdout breaks Lobster's envelope parsing.
#
# Model routing: all llm-task directives use the `main` agent.
# The agent can be overridden per-step via --agent if needed in future.
#
# Directory layout (under vault/.second-brain/):
#   memory/   — insights.md, goals.md, tasks.md, hot-memory.md, system-state.md
#   run/      — state.json, extraction-output.json, frontmatter.json, metrics.json
#   buffers/  — sync-buffer-*.md, sync.lock, sync-archive/
#   logs/     — memcli-YYYY-MM-DD.log (daily)
#
# Lock safety: Stage 0 acquires buffers/sync.lock via write_lock.py
# and Stage 5 releases it. A stale lock (default 2h) is auto-released.

name: memspren-sync

args:
  vault_path:
    type: string
    description: Absolute path to the Obsidian vault root
    required: true
  vault_name:
    type: string
    description: >
      Exact Obsidian vault name as it appears in Obsidian → Manage vaults.
      Must match precisely — used for all obsidian-cli calls (vault=<name>).
      Example: "My Second Brain"
    required: true
  config_path:
    type: string
    description: Path to .second-brain/config.md
    required: true

steps:

  # ─── STAGE 0: PRE-FLIGHT ──────────────────────────────────────────────────

  - id: lock
    command: >
      uv run -m scripts.memcli
      write-lock
      --vault-path "${vault_path}"

  - id: check_cli
    command: >
      uv run -m scripts.memcli
      check-cli
      --vault-path "${vault_path}"
      --vault "${vault_name}"
      --json

  - id: vault_diff
    command: >
      uv run -m scripts.memcli
      vault-diff
      --vault-path "${vault_path}"

  - id: task_inbox
    command: >
      uv run -m scripts.memcli
      task-inbox
      --vault-path "${vault_path}"

  - id: rotate_buffer
    command: >
      uv run -m scripts.memcli
      rotate-buffer
      --vault-path "${vault_path}"
      --sync-check

  - id: sync_gate
    command: >
      uv run -m scripts.memcli
      sync-gate
      --vault-path "${vault_path}"

  # ─── STAGE 1: EXTRACTION ──────────────────────────────────────────────────

  - id: extraction
    command: >
      uv run -m scripts.memcli
      run-extraction
      --vault-path "${vault_path}"
      --buffer-content-file "${vault_path}/.second-brain/run/buffer-content.txt"
      --manual-edits-file "${vault_path}/.second-brain/run/manual-edits.txt"

  # ─── STAGE 2: PARALLEL REFINEMENT ─────────────────────────────────────────

  - id: parallel_refinement
    command: >
      uv run -m scripts.memcli
      parallel-memory
      --vault-path "${vault_path}"
      --extraction-file "${vault_path}/.second-brain/run/extraction-output.json"
      --task-inbox-file "${vault_path}/.second-brain/run/task-inbox.json"

  # ─── STAGE 3: MERGE + WRITE LAYER 1 ───────────────────────────────────────

  - id: merge_layer1
    command: >
      uv run -m scripts.memcli
      merge-layer1
      --vault-path "${vault_path}"
    stdin: $parallel_refinement.stdout

  # ─── STAGE 4a: FRONTMATTER BATCH READ ─────────────────────────────────────

  - id: read_frontmatter
    command: >
      uv run -m scripts.memcli
      read-frontmatter
      --vault-path "${vault_path}"
      --classifiers "${vault_path}/.second-brain/run/extraction-output.json"

  # ─── STAGE 4b: ENTITY PLAN ────────────────────────────────────────────────
  # Uses raw buffer content + manual edits (not extraction output) for full context.

  - id: entity_plan
    command: >
      uv run -m scripts.memcli
      entity-plan
      --vault-path "${vault_path}"
      --buffer-content-file "${vault_path}/.second-brain/run/buffer-content.txt"
      --manual-edits-file "${vault_path}/.second-brain/run/manual-edits.txt"
      --frontmatter-file "${vault_path}/.second-brain/run/frontmatter.json"

  # ─── STAGE 4c: ENTITY WRITES ──────────────────────────────────────────────
  # Creates write directly. Append/merge/update get LLM refinement with existing content.

  - id: entity_writes
    command: >
      uv run -m scripts.memcli
      entity-write
      --plan "${vault_path}/.second-brain/run/entity-plan.json"
      --vault-path "${vault_path}"
      --vault-name "${vault_name}"
      --write-mode "filesystem"

  # ─── STAGE 4d: ENTITY LINKING ─────────────────────────────────────────────
  # Separate step: determine wikilinks, create stubs for missing targets.
  # Reads written entities from the entity-write output saved to run/.

  - id: entity_links
    command: >
      uv run -m scripts.memcli
      entity-link
      --vault-path "${vault_path}"
      --written-entities "${vault_path}/.second-brain/run/entity-write-result.json"

  # ─── STAGE 5: METRICS + CLEANUP ───────────────────────────────────────────

  - id: metrics
    command: >
      uv run -m scripts.memcli
      metrics
      --vault-path "${vault_path}"
      --write-mode "filesystem"
      --vault-name "${vault_name}"

  - id: archive_run
    command: >
      uv run -m scripts.memcli
      archive-run
      --vault-path "${vault_path}"

  - id: release_lock
    command: >
      uv run -m scripts.memcli
      write-lock
      --vault-path "${vault_path}"
      --release
      --prune-tokens-older-than-hours 24
