# memspren sync pipeline — deterministic Lobster-based workflow
#
# CRITICAL: Every script step must emit valid JSON to stdout only.
# All debug/logging output must go to stderr. The runner wrapper
# (uv run -m scripts.runner) enforces this contract and routes stderr
# to the telemetry log. Any stray stdout breaks Lobster's envelope parsing.
#
# Model routing: llm-task directives pass --agent <name> to `openclaw.invoke` directly.
# The agent name is resolved at call time — not via env var.
#
# Agent prerequisites (must exist in OpenClaw agents.list before first run):
#   memspren-heavy — complex reasoning: extraction, insights, entity plan
#   memspren-light — action directives: goals, tasks, hot-memory, linking, frontmatter
# If neither agent is configured, all directives fall back to default.
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
    run: >
      uv run scripts/memcli.py
      write-lock
      --vault-path "$LOBSTER_ARG_VAULT_PATH"

  - id: check_cli
    run: >
      uv run scripts/memcli.py
      check-cli
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --vault "$LOBSTER_ARG_VAULT_NAME"
      --json

  - id: vault_diff
    run: >
      uv run scripts/memcli.py
      vault-diff
      --vault-path "$LOBSTER_ARG_VAULT_PATH"

  - id: task_inbox
    run: >
      uv run scripts/memcli.py
      task-inbox
      --vault-path "$LOBSTER_ARG_VAULT_PATH"

  - id: rotate_buffer
    run: >
      uv run scripts/memcli.py
      rotate-buffer
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --sync-check

  # ─── STAGE 1: EXTRACTION ──────────────────────────────────────────────────

  - id: extraction
    run: >
      uv run scripts/memcli.py
      run-extraction
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --buffer-content-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/buffer-content.txt"
      --manual-edits-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/manual-edits.txt"
      --agent memspren-heavy

  # ─── STAGE 2: PARALLEL REFINEMENT ─────────────────────────────────────────

  - id: parallel_refinement
    run: >
      uv run scripts/memcli.py
      parallel-memory
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --extraction-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/extraction-output.json"
      --task-inbox-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/task-inbox.json"

  # ─── STAGE 3: MERGE + WRITE LAYER 1 ───────────────────────────────────────

  - id: merge_layer1
    run: >
      uv run scripts/memcli.py
      merge-layer1
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
    stdin: $parallel_refinement.stdout

  # ─── STAGE 4a: FRONTMATTER BATCH READ ─────────────────────────────────────

  - id: read_frontmatter
    run: >
      uv run scripts/memcli.py
      read-frontmatter
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --classifiers "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/extraction-output.json"

  # ─── STAGE 4b: ENTITY PLAN ────────────────────────────────────────────────
  # Uses raw buffer content + manual edits (not extraction output) for full context.

  - id: entity_plan
    run: >
      uv run scripts/memcli.py
      entity-plan
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --buffer-content-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/buffer-content.txt"
      --manual-edits-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/manual-edits.txt"
      --frontmatter-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/frontmatter.json"
      --agent memspren-heavy

  # ─── STAGE 4c: ENTITY WRITES ──────────────────────────────────────────────
  # Creates write directly. Append/merge/update get LLM refinement with existing content.

  - id: entity_writes
    run: >
      uv run scripts/memcli.py
      entity-write
      --plan "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/entity-plan.json"
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --vault-name "$LOBSTER_ARG_VAULT_NAME"
      --write-mode "filesystem"

  # ─── STAGE 4d: ENTITY LINKING ─────────────────────────────────────────────
  # Separate step: determine wikilinks, create stubs for missing targets.
  # Reads written entities from the entity-write output saved to run/.

  - id: entity_links
    run: >
      uv run scripts/memcli.py
      entity-link
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --written-entities "$LOBSTER_ARG_VAULT_PATH/.second-brain/run/entity-write-result.json"

  # ─── STAGE 5: METRICS + CLEANUP ───────────────────────────────────────────

  - id: metrics
    run: >
      uv run scripts/memcli.py
      metrics
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --write-mode "filesystem"
      --vault-name "$LOBSTER_ARG_VAULT_NAME"
      --extraction-result "$extraction.json"
      --layer1-result "$merge_layer1.json"
      --entity-result "$entity_writes.json"
      --vault-diff-result "$vault_diff.json"

  - id: release_lock
    run: >
      uv run scripts/memcli.py
      write-lock
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --release
      --prune-tokens-older-than-hours 24
