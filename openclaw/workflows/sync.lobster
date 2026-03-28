# memspren sync pipeline — deterministic Lobster-based workflow
#
# CRITICAL: Every script step must emit valid JSON to stdout only.
# All debug/logging output must go to stderr. The runner wrapper
# (python -m scripts.runner) enforces this contract and routes stderr
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
# Lock safety: sync.lock is released in the release_lock step (Stage 5).
# Lobster does not document on_error/finally handlers. If the pipeline fails
# before reaching release_lock, the stale-lock detection in write_lock.py
# (default 2h threshold) will auto-release it on the next sync attempt.
# To release immediately: python scripts/write_lock.py --memory-path <path> --release

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

env:
  VAULT_PATH: "$LOBSTER_ARG_VAULT_PATH"
  VAULT_NAME: "$LOBSTER_ARG_VAULT_NAME"
  MEMORY_PATH: "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"

steps:

  # ─── STAGE 0: PRE-FLIGHT ──────────────────────────────────────────────────
  # Serial, blocking. All checks must pass. Failure writes to telemetry and
  # exits cleanly — no partial state is left behind.

  - id: lock
    run: python -m scripts.runner scripts/write_lock.py --memory-path "$MEMORY_PATH"
    # Output: { ok: bool, action: "locked"|"skipped", error: str|null }
    # Exit 1 on lock exists → Lobster aborts with SYNC SKIPPED

  - id: check_cli
    run: python -m scripts.runner scripts/check_cli.py --vault-path "$VAULT_PATH" --vault "$VAULT_NAME" --json
    # Output: { write_mode: "obsidian"|"filesystem", vault_name: str, last_sync: ISO|null }

  - id: vault_diff
    run: >
      python -m scripts.runner scripts/vault_diff_scanner.py
      --vault-path "$VAULT_PATH"
      --memory-path "$MEMORY_PATH"
      --since "$check_cli.json.last_sync"
    # Output: { changed_files: [...], changed_files_content_file: str, changed_count: int }
    # On no git repo: returns empty result, logs WARN to telemetry — non-fatal

  - id: task_inbox
    run: >
      python -m scripts.runner scripts/task_inbox_scanner.py
      --vault-path "$VAULT_PATH"
      --memory-path "$MEMORY_PATH"
    # Output: { tasks: [...], completed: [...], open_count: int, task_inbox_file: str }
    # Side-effect: saves full result to MEMORY_PATH/run/task-inbox.json

  - id: rotate_buffer
    run: >
      python -m scripts.runner scripts/rotate_buffer.py
      --vault-path "$VAULT_PATH"
      --memory-path "$MEMORY_PATH"
      --sync-check
    # Output: { has_content: bool, should_exit: bool, sealed_buffers: [...], buffer_content_file: str, entry_count: int }

  - id: exit_if_empty
    when: $rotate_buffer.json.should_exit
    run: >
      python -m scripts.runner scripts/clean_exit.py
      --message "Nothing to sync."
      --release-lock
      --memory-path "$MEMORY_PATH"

  # ─── STAGE 1: EXTRACTION ──────────────────────────────────────────────────
  # Single llm-task call. Heavy agent. Reads raw buffer once.
  # All downstream stages work from this structured output.
  # Raw buffer text is NEVER read again after this step.

  - id: extraction
    run: >
      python -m scripts.runner scripts/run_extraction.py
      --buffer-content-file "$rotate_buffer.json.buffer_content_file"
      --manual-edits-file "$vault_diff.json.changed_files_content_file"
      --agent memspren-heavy
      --memory-path "$MEMORY_PATH"
    # Output: { raw_insights, raw_goals, raw_tasks, raw_patterns, classifiers }
    # Prompt/schema are hardcoded in run_extraction.py; output also saved to
    # MEMORY_PATH/run/extraction-output.json for the entity_plan step.

  # ─── STAGE 2: PARALLEL REFINEMENT ─────────────────────────────────────────
  # Python dispatcher (ThreadPoolExecutor) runs 4 llm-task jobs simultaneously.
  # Each job returns a complete drop-in replacement for its target memory file.
  # Schema validation runs per-job immediately after each call.
  # A failed job retains the existing file — it does not block the others.

  - id: parallel_refinement
    run: >
      python -m scripts.runner scripts/parallel_memory.py
      --extraction-file "$MEMORY_PATH/run/extraction-output.json"
      --task-inbox-file "$task_inbox.json.task_inbox_file"
      --memory-path "$MEMORY_PATH"
    # Output: { insights: {ok, content}, goals: {ok, content}, tasks: {ok, content}, hot_memory: {ok, content} }

  # ─── STAGE 3: MERGE + WRITE LAYER 1 ───────────────────────────────────────
  # Pure collection and validation. No LLM involved.
  # Writes .second-brain/Memory/ files directly (not vault content).
  # Failure: invalid schema → keep existing file. All four fail → abort.

  - id: merge_layer1
    run: >
      python -m scripts.runner scripts/merge.py
      --results "$parallel_refinement.json"
      --memory-path "$MEMORY_PATH"
    # Output: { ok: bool, written: [...], fallback: [...], summary: str }

  # ─── STAGE 4a: FRONTMATTER BATCH READ ─────────────────────────────────────
  # Reads only YAML frontmatter (not body) for classifier-scoped vault folders.
  # Fast and low-token. Drives merge detection in entity plan step.

  - id: read_frontmatter
    run: >
      python -m scripts.runner scripts/read_frontmatter.py
      --vault-path "$VAULT_PATH"
      --classifiers "$extraction.json.classifiers"
      --memory-path "$MEMORY_PATH"
    # Output: { frontmatter_file: str, count: int }
    # Side-effect: saves frontmatter array to MEMORY_PATH/run/frontmatter.json
    # Note: --classifiers only interpolates classifier names (short safe strings, no quotes)

  # ─── STAGE 4b: ENTITY PLAN ────────────────────────────────────────────────
  # Single llm-task call. Heavy agent.
  # Generates the full vault write plan using extraction + frontmatter.
  # No links in content drafts — content and linking are separate directives.

  - id: entity_plan
    run: >
      python -m scripts.runner scripts/run_entity_plan.py
      --extraction-file "$MEMORY_PATH/run/extraction-output.json"
      --frontmatter-file "$read_frontmatter.json.frontmatter_file"
      --task-inbox-file "$task_inbox.json.task_inbox_file"
      --agent memspren-heavy
    # Output: { entities: [{path, action, content_draft, node_type}], summary: str }
    # Prompt/schema hardcoded in run_entity_plan.py. All heavy inputs read from files.

  # ─── STAGE 4d: APPROVAL GATE ──────────────────────────────────────────────
  # Pipeline pauses here. User reviews the full write plan before any vault writes.
  # approved: true  → continue to entity writes
  # approved: false → abort; buffer preserved; safe to re-trigger

  - id: approval
    approval: |
      Sync ready to write.

      Memory: $merge_layer1.json.summary
      Vault:  $entity_plan.json.summary
      Manual edits absorbed: $vault_diff.json.changed_count

      Proceed with vault writes?

  # ─── STAGE 4c: ENTITY WRITES ──────────────────────────────────────────────
  # Per-entity: content directive (light) → linking directive (light) → write.
  # Entities run in parallel via Python dispatcher.
  # git snapshot before every existing-file modification.
  # Write via obsidian-cli or filesystem fallback (resolved in Stage 0).

  - id: entity_writes
    when: $approval.approved
    run: >
      python -m scripts.runner scripts/entity_pipeline.py
      --plan "$entity_plan.json"
      --vault-path "$VAULT_PATH"
      --vault-name "$check_cli.json.vault_name"
      --write-mode "$check_cli.json.write_mode"
      --memory-path "$MEMORY_PATH"
    # Output: { ok, written, created, updated, merged, links_added, failed: [...] }

  # ─── STAGE 5: METRICS + CLEANUP ───────────────────────────────────────────
  # Write metrics.json, archive sealed buffers, update system-state.md,
  # append to system-log. Lock released at end.

  - id: metrics
    run: >
      python -m scripts.runner scripts/metrics_writer.py
      --memory-path "$MEMORY_PATH"
      --vault-path "$VAULT_PATH"
      --write-mode "$check_cli.json.write_mode"
      --vault-name "$check_cli.json.vault_name"
      --extraction-result "$extraction.json"
      --layer1-result "$merge_layer1.json"
      --entity-result "$entity_writes.json"
      --vault-diff-result "$vault_diff.json"
      --sealed-buffers "$rotate_buffer.json.sealed_buffers"
      --entity-writes-ok "$entity_writes.json.ok"

  - id: release_lock
    run: >
      python -m scripts.runner scripts/write_lock.py
      --memory-path "$MEMORY_PATH"
      --release
      --prune-tokens-older-than-hours 24
