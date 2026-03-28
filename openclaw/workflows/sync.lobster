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

steps:

  # ─── STAGE 0: PRE-FLIGHT ──────────────────────────────────────────────────
  # Serial, blocking. All checks must pass. Failure writes to telemetry and
  # exits cleanly — no partial state is left behind.

  - id: lock
    run: python -m scripts.runner scripts/write_lock.py --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Output: { ok: bool, action: "locked"|"skipped", error: str|null }
    # Exit 1 on lock exists → Lobster aborts with SYNC SKIPPED

  - id: check_cli
    run: python -m scripts.runner scripts/check_cli.py --vault-path "$LOBSTER_ARG_VAULT_PATH" --vault "$LOBSTER_ARG_VAULT_NAME" --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory" --json
    # Output: { write_mode: "obsidian"|"filesystem", vault_name: str, last_sync: ISO|null }
    # Also writes to state: check_cli_vault_name, check_cli_write_mode, check_cli_last_sync

  - id: vault_diff
    run: >
      python -m scripts.runner scripts/vault_diff_scanner.py
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Reads check_cli_last_sync from state file
    # Output: { changed_files: [...], changed_files_content_file: str, changed_count: int }
    # On no git repo: returns empty result, logs WARN to telemetry — non-fatal

  - id: task_inbox
    run: >
      python -m scripts.runner scripts/task_inbox_scanner.py
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Output: { tasks: [...], completed: [...], open_count: int, task_inbox_file: str }
    # Side-effect: saves full result to MEMORY_PATH/run/task-inbox.json

  - id: rotate_buffer
    run: >
      python -m scripts.runner scripts/rotate_buffer.py
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
      --sync-check
    # Output: { has_content: bool, should_exit: bool, sealed_buffers: [...], buffer_content_file: str, entry_count: int }

  # Note: If rotate_buffer returns has_content=false, extraction and downstream
  # steps will handle empty input gracefully. No early exit needed.

  # ─── STAGE 1: EXTRACTION ──────────────────────────────────────────────────
  # Single llm-task call. Heavy agent. Reads raw buffer once.
  # All downstream stages work from this structured output.
  # Raw buffer text is NEVER read again after this step.

  - id: prepare_extraction
    run: >
      python -m scripts.runner scripts/prepare_extraction.py
      --buffer-content-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/buffer-content.txt"
      --manual-edits-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/manual-edits.txt"
    # Output: { input: {...}, schema: {...} }

  - id: extraction
    pipeline: >
      llm.invoke --provider openclaw --prompt "$(cat prompts/extraction_prompt.txt)"
    stdin: $prepare_extraction.json
    # Output from llm.invoke: { raw_insights, raw_goals, raw_tasks, raw_patterns, classifiers }

  - id: save_extraction
    run: >
      python -m scripts.runner scripts/save_extraction.py
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    stdin: $extraction.stdout
    # Saves extraction output to MEMORY_PATH/run/extraction-output.json for entity_plan step
    # Output: { raw_insights, raw_goals, raw_tasks, raw_patterns, classifiers }

  # ─── STAGE 2: PARALLEL REFINEMENT ─────────────────────────────────────────
  # Python dispatcher (ThreadPoolExecutor) runs 4 llm-task jobs simultaneously.
  # Each job returns a complete drop-in replacement for its target memory file.
  # Schema validation runs per-job immediately after each call.
  # A failed job retains the existing file — it does not block the others.

  - id: parallel_refinement
    run: >
      python -m scripts.runner scripts/parallel_memory.py
      --extraction-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/extraction-output.json"
      --task-inbox-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/task-inbox.json"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Output: { insights: {ok, content}, goals: {ok, content}, tasks: {ok, content}, hot_memory: {ok, content} }

  # ─── STAGE 3: MERGE + WRITE LAYER 1 ───────────────────────────────────────
  # Pure collection and validation. No LLM involved.
  # Writes .second-brain/Memory/ files directly (not vault content).
  # Failure: invalid schema → keep existing file. All four fail → abort.

  - id: merge_layer1
    run: >
      python -m scripts.runner scripts/merge.py
      --results "$parallel_refinement.json"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Output: { ok: bool, written: [...], fallback: [...], summary: str }

  # ─── STAGE 4a: FRONTMATTER BATCH READ ─────────────────────────────────────
  # Reads only YAML frontmatter (not body) for classifier-scoped vault folders.
  # Fast and low-token. Drives merge detection in entity plan step.

  - id: read_frontmatter
    run: >
      python -m scripts.runner scripts/read_frontmatter.py
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --classifiers "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/extraction-output.json"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
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
      --extraction-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/extraction-output.json"
      --frontmatter-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/frontmatter.json"
      --task-inbox-file "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory/run/task-inbox.json"
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

      Check state.json for details: memory updated, entity plan ready.

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
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --vault-name "$LOBSTER_ARG_VAULT_NAME"
      --write-mode "filesystem"
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
    # Output: { ok, written, created, updated, merged, links_added, failed: [...] }

  # ─── STAGE 5: METRICS + CLEANUP ───────────────────────────────────────────
  # Write metrics.json, archive sealed buffers, update system-state.md,
  # append to system-log. Lock released at end.

  - id: metrics
    run: >
      python -m scripts.runner scripts/metrics_writer.py
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
      --vault-path "$LOBSTER_ARG_VAULT_PATH"
      --write-mode "filesystem"
      --vault-name "$LOBSTER_ARG_VAULT_NAME"
      --extraction-result "$extraction.json"
      --layer1-result "$merge_layer1.json"
      --entity-result "$entity_writes.json"
      --vault-diff-result "$vault_diff.json"
    # Reads sealed_buffers and entity_writes_ok from state

  - id: release_lock
    run: >
      python -m scripts.runner scripts/write_lock.py
      --memory-path "$LOBSTER_ARG_VAULT_PATH/.second-brain/Memory"
      --release
      --prune-tokens-older-than-hours 24
