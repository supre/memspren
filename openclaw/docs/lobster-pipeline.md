# Lobster Sync Pipeline

---

## Why this exists

The v0.01 sync was an 11-step sequential process where the LLM orchestrated every step. Context accumulated across the session. The most inference-heavy steps — insights, goals, hot-memory recalculation — came last. When sync ran in a degraded cron environment (minimal shell, stale PATH, token pressure) those steps silently skipped with no error signal. The memory files drifted from reality. The user noticed days later.

Three confirmed failure modes from live usage:

- `insights.md` had not been updated since March 22 — a 5-day gap with no indication
- `goals.md` showed March 25 tasks as still open after they had been completed
- `hot-memory.md` was partially updating but inconsistently

Root cause: all three were steps 5, 6, and 7 of an 11-step monolith. A single upstream failure silently aborted everything downstream.

The Lobster pipeline addresses this by making the sync deterministic, decomposing memory updates into parallel schema-validated jobs, and adding an explicit approval gate before any vault writes.

---

## What changed

### Before (v0.01)

```
sync triggered
  → LLM reads buffer
  → LLM orchestrates 11 sequential steps
  → LLM writes entities, recalculates memory
  → LLM archives buffer
```

The LLM was in the loop between every step. Failures were silent. No telemetry. No approval before writing.

### After (Lobster pipeline)

```
sync triggered
  → one Lobster tool call
  → [pre-flight] → [extraction] → [parallel refinement]
  → [merge layer 1] → [entity pipeline] → [approval gate]
  → [entity writes] → [metrics + cleanup]
```

The LLM only runs inside explicit `llm-task` directive steps. Lobster handles execution, step ordering, and the approval gate. Every step emits a telemetry log entry. Missing entries prove exactly where a failure occurred.

---

## Architecture

### The three-layer memory model (unchanged)

The memory model from v0.01 is preserved:

| Layer | What | When |
|---|---|---|
| Layer 1 | `insights.md`, `goals.md`, `hot-memory.md`, `system-state.md` | Read every session (~2000 tokens) |
| Layer 2 | Rotating sync buffers | Write-only during conversation; read during sync |
| Layer 3 | Obsidian vault entities | Written during sync only |

### The pipeline (new)

The sync is now a **deterministic Lobster pipeline** defined in `workflows/sync.lobster`. One `lobster run` call fires the entire process. The LLM only runs inside the six `llm-task` directive steps.

```
Stage 0: Pre-flight      (serial, blocking)
Stage 1: Extraction      (1 llm-task, heavy agent)
Stage 2: Parallel refine (4 llm-task jobs, simultaneous)
Stage 3: Merge + write   (pure logic, no LLM)
Stage 4a: Frontmatter    (script, no LLM)
Stage 4b: Entity plan    (1 llm-task, heavy agent)
Stage 4d: Approval gate  (pause → resumeToken)
Stage 4c: Entity writes  (parallel, per entity)
Stage 5: Metrics/cleanup (scripts, no LLM)
```

### Data passing pattern

All large or user-authored data (buffer content, manual edits, extraction output, task titles, frontmatter descriptions) is passed between pipeline stages via files in `MEMORY_PATH/run/`, never as inline CLI arguments. Lobster interpolation (`$stepId.json.field`) is only used for short, safe values: file paths, booleans, counts, and classifier names. This prevents any user-typed text containing quotes, braces, or newlines from breaking the command line.

| File written by | File | Read by |
|---|---|---|
| `rotate_buffer.py` | `run/buffer-content.txt` | `run_extraction.py` |
| `vault_diff_scanner.py` | `run/manual-edits.txt` | `run_extraction.py` |
| `run_extraction.py` | `run/extraction-output.json` | `parallel_memory.py`, `run_entity_plan.py` |
| `task_inbox_scanner.py` | `run/task-inbox.json` | `parallel_memory.py`, `run_entity_plan.py` |
| `read_frontmatter.py` | `run/frontmatter.json` | `run_entity_plan.py` |

---

## Components

### `workflows/sync.lobster`

The pipeline definition. A YAML workflow file that Lobster executes as a single unified operation. Contains all step declarations, environment variable bindings, conditions, and the approval gate.

**Required args at invocation:**

| Arg | Description |
|---|---|
| `vault_path` | Absolute path to the Obsidian vault root |
| `vault_name` | Exact vault name as shown in Obsidian → Manage vaults (used for all CLI calls) |
| `config_path` | Path to `.second-brain/config.md` |

`vault_name` must match exactly — it is passed directly to `obsidian vault=<name>` CLI calls. A mismatch forces the pipeline into filesystem mode even when obsidian-cli is available.

**Key properties:**
- Steps are identified by `id:`, prior step outputs referenced as `$stepId.json.field`
- All `llm-task` invocations use `openclaw.invoke --tool llm-task --action invoke --agent <name>` with args passed as `{"args": {...}}` in the request body
- The approval gate (`id: approval`) pauses execution; resume with `lobster resume <token> --approve`
- All script steps are invoked via `python -m scripts.runner` — never directly
- Lobster does not support `on_error:`/`finally:` handlers. Lock safety relies on stale-lock auto-detection (2h) in `write_lock.py`. To release immediately after a crash: `python scripts/write_lock.py --memory-path <path> --release`

**Lobster limitations discovered during v0.4 implementation:**
1. **No JSON path access**: `$step.json.field` syntax not supported (only `$step.json`, `$step.stdout`, `$step.approved`, `$step.skipped`)
2. **env: variables don't expand**: `$LOBSTER_ARG_*` references in `env:` section remain literal
3. **when: clause limitations**: Only supports boolean step properties (`.approved`, `.skipped`), not arbitrary expressions like `$var.field == false`

**Workaround: State file pattern**
All scripts write their output to `{MEMORY_PATH}/run/state.json` using `scripts/state.py` helper module. Downstream scripts read from known file paths instead of relying on Lobster's JSON path interpolation. This enables multi-step workflows despite Lobster's interpolation limitations.

### `scripts/runner.py`

The most critical new script. Wraps every script call in the pipeline to enforce the **JSON-only stdout contract**.

Lobster parses stdout as a JSON envelope. Any stray `print()`, debug output, or exception traceback on stdout breaks the entire run. The runner:

- Executes the target script as a subprocess
- Captures stdout and validates it is parseable JSON before passing through
- Routes all stderr to `sync-telemetry.log`
- On any failure (empty stdout, invalid JSON, timeout, launch error): emits a structured JSON error object to stdout instead of crashing

Usage: `python -m scripts.runner scripts/foo.py --arg value`

This is the only way scripts should be invoked from Lobster steps.

### Stage 0 — Pre-flight scripts

Five serial checks that must all pass before the pipeline proceeds.

**`write_lock.py`**
Writes `sync.lock` to `.second-brain/Memory/`. If the lock already exists it inspects the `locked_at` timestamp — locks older than the configured threshold (default 2 hours) are treated as stale and auto-released rather than aborting. This handles the case where a previous pipeline crashed without releasing. Live locks still abort with SYNC SKIPPED. The `on_error`/`finally` handlers in `sync.lobster` ensure the lock is released even when the pipeline fails mid-run. Prunes stale Lobster resume tokens at the end of Stage 5.

**`check_cli.py`** (updated)
Supports `--json` flag for pipeline mode. Accepts `--vault <name>` explicitly — no longer derives vault_name from the folder path (which silently produced wrong names). Returns `{ write_mode, vault_name, last_sync }`. Probes obsidian-cli with the exact vault name provided. If the CLI is unavailable or vault access fails, sets `write_mode: "filesystem"` (non-fatal fallback).

**`vault_diff_scanner.py`** (new)
Detects vault files manually changed since the last sync. Checks both committed history (`git log --name-only --after=<last_sync>`) and the working tree (`git status --porcelain`, `git diff --name-only`) so uncommitted Obsidian edits are included. Writes concatenated file contents to `MEMORY_PATH/run/manual-edits.txt` and returns the file path as `changed_files_content_file`. The extraction step reads from that file. If the vault is not a git repo, logs a warning and returns empty (non-fatal).

**`task_inbox_scanner.py`** (new)
Parses `Tasks/tasks-inbox.md` and extracts open/completed tasks. Deduplicates by title similarity using Levenshtein ratio (default threshold: 0.85). Writes its full output to `MEMORY_PATH/run/task-inbox.json` and returns the file path as `task_inbox_file`. Downstream steps (Stage 2 dispatcher, Stage 4b entity plan) read from that file — task titles may contain quotes that would break CLI argument parsing.

**`rotate_buffer.py`** (updated)
`--sync-check` mode seals the active buffer if it has entries (regardless of word count — ensures nightly sync always runs even if the buffer never hit the rotation cap). Writes concatenated buffer content to `MEMORY_PATH/run/buffer-content.txt` and returns the path as `buffer_content_file`. If nothing to sync, pipeline exits cleanly.

### Stage 1 — Extraction

**`run_extraction.py`** (new wrapper)
Reads buffer content and manual edits from temp files, builds a payload, and calls the OpenClaw Gateway `/tools/invoke` endpoint directly via curl to avoid all shell quoting issues. The payload format is:

```json
{
  "tool": "llm-task",
  "action": "invoke",
  "args": {
    "prompt": "...",
    "input": {...},
    "schema": {...},
    "timeoutMs": 120000
  }
}
```

The script writes the payload to a temp JSON file and passes it via curl's `@file` syntax. Prompt and schema paths are hardcoded inside the script — they are not exposed as CLI flags. Saves the LLM output to `MEMORY_PATH/run/extraction-output.json` for downstream steps, then prints it to stdout.

**Why curl instead of Python subprocess → openclaw.invoke?**
After 6 hours of debugging, discovered that shell quoting of nested JSON payloads (buffer content with quotes, braces, newlines) breaks when passed through Python subprocess → Lobster → openclaw.invoke. Direct HTTP API call with curl bypasses all quoting layers and works reliably.

Extraction output:

```json
{
  "raw_insights":  [...],
  "raw_goals":     [...],
  "raw_tasks":     [...],
  "raw_patterns":  [...],
  "classifiers":   ["project:personal", "relationship", "pattern", "health", "log"]
}
```

All downstream stages work from this structured output. Raw buffer text is never read again. The `classifiers` field drives which vault folders the entity pipeline scans.

Validated against `schemas/extraction_schema.json`. **Note:** The classifier enum was initially strict (project:personal, project:work, idea, people, learning, log, pattern, relationship, vision, strategy, kt) but caused schema validation failures when the LLM output values like "health" or partial names. The schema was relaxed to accept any string in v0.4, with suggested values documented in the description field instead of a hard enum.

### Stage 2 — Parallel refinement dispatcher

**`parallel_memory.py`** (new)
Dispatches four `llm-task` jobs simultaneously via `ThreadPoolExecutor(max_workers=4)`. Reads extraction output from `MEMORY_PATH/run/extraction-output.json` and task inbox from the file path passed via `--task-inbox-file`. Each job reads its prompt and schema from disk, builds the payload as `{"tool": "llm-task", "action": "invoke", "args": {...}}`, and calls the OpenClaw Gateway `/tools/invoke` endpoint directly via curl (same pattern as run_extraction.py).

| Job | Agent | Input | Output |
|---|---|---|---|
| insights | heavy | raw_insights, raw_patterns, existing insights.md | complete replacement insights.md |
| goals | light | raw_goals, task_inbox, existing goals.md | complete replacement goals.md |
| tasks | light | raw_tasks, task_inbox, existing tasks.md | complete replacement tasks.md |
| hot_memory | light | raw_goals, raw_tasks, existing hot-memory.md | complete replacement hot-memory.md |

Each job validates its output against its schema immediately using `jsonschema`. A failed or invalid job does not block the others — its slot returns `ok: false` and the existing file is preserved by the merge step.

### Stage 3 — Merge

**`merge.py`** (new)
Pure collection and validation. No LLM. Reads the four parallel refinement results, validates each, and writes the files to `.second-brain/Memory/`. If all four fail, aborts before vault writes. If some fail, continues with the successful ones and logs the fallbacks in the approval gate summary.

### Stage 4a — Frontmatter scan

**`read_frontmatter.py`** (new)
Reads only YAML frontmatter (not body) for all files in classifier-scoped vault folders. Fast and low-token — pure filesystem I/O, no LLM. Writes the frontmatter array to `MEMORY_PATH/run/frontmatter.json` and returns `{ frontmatter_file, count }`. The entity plan step reads from the file (descriptions may contain quotes). The `entity_plan` step uses these descriptions for merge detection.

Classifier → folder mapping:

| Classifier | Folder |
|---|---|
| project:personal / project:work | Work/Projects/ |
| idea | Work/Ideas/ |
| people / relationship | People/ |
| learning | Notes/Learnings/ |
| log | Log/Daily/ |
| pattern | Notes/Patterns/ |
| vision | Vision/ |
| strategy | Strategy/ |
| kt | Work/KT/ |

### Stage 4b — Entity plan

**`run_entity_plan.py`** (new wrapper)
Reads extraction, frontmatter, and task inbox all from files (never from shell-interpolated CLI strings). Builds the payload as `{"tool": "llm-task", "action": "invoke", "args": {...}}` and calls the OpenClaw Gateway `/tools/invoke` endpoint via curl. Prompt and schema paths are hardcoded inside the script.

Entity plan output:

```json
{
  "entities": [
    { "path": "Work/Projects/memspren.md", "action": "append", "content_draft": "..." },
    { "path": "People/alice-chen.md",       "action": "create", "content_draft": "..." }
  ],
  "summary": "2 create, 1 append, 1 merge"
}
```

No links in content drafts at this stage. Content and linking are handled as separate directives in Stage 4c. Validated against `schemas/entity_plan_schema.json`.

### Stage 4d — Approval gate

The pipeline pauses and returns a `resumeToken`. The agent presents the write plan to the user before any irreversible vault writes occur:

```
Sync ready to write.

Memory: insights OK, goals OK, tasks OK, hot-memory FALLBACK
Vault:  2 create (daily log, person), 1 append (project), 1 merge (pattern)
Manual edits absorbed: 3

Proceed with vault writes?
```

User approves → `lobster resume <token> --approve`
User declines → `lobster resume <token> --decline` (buffer preserved, safe to retry)
Token expires (default 24h) → re-trigger sync (buffer intact)

### Stage 4c — Entity pipeline

**`entity_pipeline.py`** (new)
Runs three sequential steps per entity, entities in parallel via `ThreadPoolExecutor(max_workers=4)`. Each step calls the OpenClaw Gateway `/tools/invoke` endpoint directly via curl with `{"tool": "llm-task", "action": "invoke", "args": {...}}`.

1. **Content directive** (light agent) — takes `content_draft` from the entity plan, produces final frontmatter + body. `description` field is required. No wikilinks yet.
2. **Linking directive** (light agent) — takes the final content, returns `wikilinks` (appended as a footer) and `connected_additions`. The `update_connected_for` function updates both sides of each link:
   - `obsidian` mode: delegates to `update_connected.py --vault <vault_name> --file <vault-relative-path>` via obsidian-cli
   - `filesystem` mode: `_fs_add_connected()` performs a direct in-place frontmatter edit — linking works regardless of CLI availability
3. **Write** — git snapshot for existing files, then writes via obsidian-cli or direct filesystem depending on `write_mode`.

Validated against `schemas/entity_content_schema.json` and `schemas/entity_linking_schema.json`.

### Stage 5 — Metrics and cleanup

**`metrics_writer.py`** (new)
Collects results from all prior stages and writes `metrics.json` to `.second-brain/Memory/`. Routes `Logs/system-log.md` writes through obsidian-cli when `write_mode == "obsidian"` (so Obsidian's watchers are triggered), falls back to direct filesystem write otherwise.

**`last_sync` is only advanced when `entity_writes_ok` is true.** If the user declined the approval gate or Stage 4c failed, `last_sync` is not updated and the log entry reads "SYNC INCOMPLETE" instead of "SYNC COMPLETE". This ensures the next run's `vault_diff_scanner` still sees the un-synced manual edits — the diff checkpoint stays at the last successful write.

Archives sealed buffers to `sync-archive/` only after confirmed entity writes. Rotates `sync-telemetry.log` if it exceeds `max_log_bytes` (default 2 MB).

`metrics.json` structure:

```json
{
  "last_sync": "2026-03-28T...",
  "buffers_processed": 1,
  "entities_created": 2,
  "entities_updated": 1,
  "entities_merged": 1,
  "links_added": 4,
  "manual_edits_absorbed": 3,
  "memory_files_updated": ["insights", "goals", "tasks"],
  "inference_results": {
    "extraction": "ok",
    "insights": "ok",
    "goals": "ok",
    "tasks": "ok",
    "hot_memory": "fail",
    "entity_plan": "ok"
  }
}
```

### Schemas (`schemas/`)

Eight JSON Schema files. Every `llm-task` output is validated immediately after the call. Invalid output → existing file kept, logged as WARN. Pipeline never writes malformed data.

| Schema | Validates |
|---|---|
| `extraction_schema.json` | Stage 1 extraction output |
| `insights_schema.json` | insights.md replacement (enforces 3500 char ceiling ≈ 700 tokens) |
| `goals_schema.json` | goals.md replacement (2500 char ceiling ≈ 500 tokens) |
| `tasks_schema.json` | tasks.md replacement |
| `hot_memory_schema.json` | hot-memory.md replacement (2500 char ceiling ≈ 500 tokens) |
| `entity_plan_schema.json` | Stage 4b entity plan (path, action, content_draft per entity) |
| `entity_content_schema.json` | Stage 4c content directive output (frontmatter + body) |
| `entity_linking_schema.json` | Stage 4c linking directive output (wikilinks, connected_additions) |

### Prompts (`prompts/`)

Eight prompt files — one per `llm-task` directive. Separated from scripts and the workflow file so they can be edited independently without touching pipeline logic.

| Prompt | Used by |
|---|---|
| `extraction_prompt.txt` | Stage 1 extraction |
| `insights_prompt.txt` | Stage 2 insights job |
| `goals_prompt.txt` | Stage 2 goals job |
| `tasks_prompt.txt` | Stage 2 tasks job |
| `hot_memory_prompt.txt` | Stage 2 hot-memory job |
| `entity_plan_prompt.txt` | Stage 4b entity plan |
| `entity_content_prompt.txt` | Stage 4c content directive |
| `entity_linking_prompt.txt` | Stage 4c linking directive |

---

## Model routing

No directive hardcodes a model or provider. Model selection is owned entirely by the user via OpenClaw's agent configuration.

Two named agents in OpenClaw. Names stored in `config.md`:

```yaml
agents:
  heavy: memspren-heavy    # extraction, insights, entity plan
  light: memspren-light    # goals, tasks, hot-memory, content, linking
  default: main            # fallback if named agents not configured
```

The agent name is passed via `--agent <name>` to `openclaw.invoke` at each call site. Scripts never inherit agent names from environment variables — each `openclaw.invoke` call specifies its agent explicitly. This makes the routing visible in logs and avoids silent fallback to the wrong model.

---

## Telemetry

Every step writes to `.second-brain/Memory/sync-telemetry.log`:

```
[ISO ts] [LEVEL] [runner] action=run:check_cli.py result=OK
[ISO ts] [LEVEL] [runner] action=run:parallel_memory.py result=OK
[ISO ts] [ERROR] [runner] action=run:merge.py result=INVALID_JSON detail=...
```

To diagnose a failed sync: read the telemetry log. Missing entries prove exactly where the pipeline stopped.

Verbosity is configurable in `config.md`:

| Level | What is logged |
|---|---|
| `ERROR` | Failures, aborts, schema rejections |
| `WARN` | Fallbacks, retries, partial failures |
| `INFO` | Step completed, entity written, memory file updated (default) |
| `DEBUG` | Full prompt/response text, token counts, diffs |

---

## Installation and setup

### 1. Prerequisites

- Obsidian installed with a vault
- OpenClaw installed and running
- `lobster` installed: `pnpm install lobster` (provides `lobster` CLI)
- `llm-task` plugin installed ([setup guide](https://docs.openclaw.ai/tools/llm-task))
- Python 3.11+ (for the `match` syntax and type hints used in scripts)
- `jsonschema` Python package: `pip install jsonschema`
- Git initialized in your Obsidian vault root: `git init` (required for bidirectional sync)

Optional but recommended — Obsidian CLI:
```bash
brew install --cask obsidian
# Enable: Obsidian → Settings → General → Enable CLI (requires 1.12.4+)
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
source ~/.zprofile
```
If obsidian-cli is unavailable the pipeline falls back to filesystem writes automatically.

### 2. Enable tools in OpenClaw

Add to your OpenClaw agent configuration:

```json
{
  "tools": { "alsoAllow": ["lobster", "llm-task"] }
}
```

### 3. Create the two named agents

Run manually or use the setup script:

```bash
python scripts/create_agents.py
```

The script runs `openclaw agents add` for each agent — OpenClaw opens an interactive panel for each, where you select the model and confirm. Suggested models: Sonnet or Opus for heavy, Haiku or Sonnet for light.

Or add them manually one at a time:
```bash
openclaw agents add memspren-heavy
openclaw agents add memspren-light
```

If you skip this step, all directives fall back to your default agent — the pipeline still works, you just lose the heavy/light cost split.

### 4. Find your vault name

The `vault_name` arg must match exactly what appears in **Obsidian → Manage vaults**. It is used verbatim in `obsidian vault=<name>` CLI calls. To check:

```bash
# List vaults known to the CLI
obsidian list-vaults
```

Common mismatch: your vault folder is named `my-vault` but the Obsidian display name is `My Vault`. Use the display name.

### 5. Update config.md

Add these fields to `.second-brain/config.md` in your vault (create the file if it's your first setup):

```yaml
# Agent routing
agents:
  heavy: memspren-heavy
  light: memspren-light
  default: main

# Logging
logging:
  verbosity: INFO
  max_log_bytes: 2097152
  keep_lines: 2000

# Lobster
lobster:
  resume_token_ttl_hours: 24
```

### 6. Install the skill

Copy the `openclaw/` folder to your OpenClaw skills directory:

```bash
cp -r openclaw/ ~/.openclaw/skills/memspren/
```

Restart OpenClaw to load the skill.

### 7. Verify

Run the pre-flight checks manually before the first sync:

```bash
# Check obsidian-cli with your exact vault name
python scripts/check_cli.py --vault "Your Vault Name"

# Check buffer state
python scripts/rotate_buffer.py --vault-path "/path/to/vault" --check

# Test runner wrapper
python -m scripts.runner scripts/write_lock.py --memory-path "/tmp/test-memspren" && \
python -m scripts.runner scripts/write_lock.py --memory-path "/tmp/test-memspren" --release
```

Run a first sync from the session:
> "sync now"

The pipeline runs through pre-flight → extraction → parallel refinement → merge → entity plan, then pauses at the approval gate. Review the write plan and approve.

---

## Invoking the pipeline

```bash
lobster run workflows/sync.lobster \
  --args-json '{"vault_path":"/Users/you/Documents/My Vault","vault_name":"My Vault","config_path":"/Users/you/Documents/My Vault/.second-brain/config.md"}'
```

`vault_name` is required and must match the Obsidian display name exactly.

---

## Migrating from v0.01

### What you need to do

1. Note your exact Obsidian vault display name (Obsidian → Manage vaults)
2. Add the new config.md fields (Step 5 above)
3. Create the two named agents in OpenClaw (Step 3 above)
4. Install `jsonschema`: `pip install jsonschema`
5. Ensure your vault root has a git repo: `git init` (if not already)
6. Re-copy the skill folder — new scripts, schemas, prompts, and workflow are all in the package

### What carries forward unchanged

- Your existing vault files — no migration needed
- Your existing Layer 1 memory files (`insights.md`, `goals.md`, `hot-memory.md`, `system-state.md`)
- Your existing sync buffers — they will be processed on first sync
- Your custom protocols in `.second-brain/Protocols/`
- The entity schema and vault folder structure

### What changes in behaviour

| Behaviour | Before | After |
|---|---|---|
| Memory updates | Sequential, steps 5-7 of 11 | Parallel, schema-validated, in Stage 2 |
| Vault writes | Immediate, no approval | Gated — user reviews write plan first |
| Failures | Silent skip | Explicit telemetry log entry per step |
| obsidian-cli unavailable | Sync aborts | Filesystem fallback, sync continues |
| obsidian-cli linking | N/A | Filesystem fallback for `connected:` updates too |
| Manual Obsidian edits | Invisible to sync | Ingested via git diff (committed + working tree) |
| Buffer rotation | Word-count threshold only | Seals on any entries at sync time |
| last_sync on failed write | Always updated | Only updated when entity writes succeed |
| Lock on pipeline crash | Permanent until manual delete | Stale-lock auto-detection (2h); manual release: `python scripts/write_lock.py --release` |
| Vault name for CLI calls | Derived from folder name | Explicitly provided via vault_name arg |

---

## Implementation Notes: v0.4 Integration Breakthrough (2026-03-28)

After 6 hours of debugging, the full Stage 0 + Stage 1 extraction pipeline is working end-to-end. Key discoveries:

### OpenClaw Gateway API Format

The `/tools/invoke` endpoint expects:
```json
{
  "tool": "llm-task",
  "action": "invoke",
  "args": {
    "prompt": "...",
    "input": {...},
    "schema": {...},
    "timeoutMs": 120000
  }
}
```

**Not** `"action": "json"` (that's for different tools). **Not** parameters flattened at the top level. The `args` wrapper is required.

### Why Direct HTTP Calls

Initial attempts used:
1. Python `subprocess.run(['openclaw.invoke', '--tool', 'llm-task', '--args-json', json.dumps(payload)])` → shell quote escaping broke on nested JSON
2. Lobster pipeline string with `openclaw.invoke` → same quoting issues
3. Base64 encoding → still broke
4. Temp file + stdin piping → Lobster's stdin mode doesn't support openclaw.invoke
5. Python urllib.request with direct HTTP API call to `/tools/invoke` → **this works**
6. Switched to curl for reliability → **production solution**

The curl approach bypasses all shell/subprocess quoting layers by writing the payload to a temp JSON file and using curl's `@file` syntax. This is now the standard pattern for all LLM invocations in the pipeline.

### State File Pattern

Lobster's documented `$step.json.field` syntax for accessing nested JSON is not implemented. Workaround: all scripts write their complete output to `{MEMORY_PATH}/run/state.json` using the `scripts/state.py` helper module. Downstream scripts read from known file paths.

Current state fields:
- `check_cli_vault_name`, `check_cli_write_mode`, `check_cli_last_sync`
- `vault_diff_changed_count`
- `task_inbox_file`, `task_inbox_open_count`
- `rotate_buffer_sealed_buffers`

### Schema Validation

The extraction schema initially had a strict enum for classifiers. The LLM sometimes output values like "health" or partial names that weren't in the enum, causing validation failures. The schema was relaxed to accept any string, with suggested values moved to the description field. This allows the LLM to infer appropriate classifiers while still enforcing the array structure.

### Proven Working (as of 2026-03-28 19:16 EDT)

- ✅ Stage 0 (pre-flight): lock, obsidian-cli check, vault diff scan, task inbox parse, buffer rotation
- ✅ Stage 1 (extraction): LLM successfully parsed emotional complexity (bank rejection, inner critic spike, patterns) and returned structured output
- ⚠️ Stage 2-6: Not yet implemented (merge.py failure expected)

The extraction output quality validates the architecture. Raw insights like "Inner critic activation after bank rejection was LOUD: 'You're fat, you're old, you're short'" were correctly captured and structured.

---

## Open questions

These are documented as open questions from the design session and are not yet resolved:

1. **Lobster parallel sub-pipeline syntax** — does `.lobster` support a native `parallel:` block with named branches and `collect:` step? Until confirmed, Stage 2 uses the Python dispatcher. If confirmed, `parallel_memory.py` becomes redundant for Stage 2.

2. **Telemetry format** — `sync-telemetry.log` (plain text) vs. `sync-telemetry.jsonl` (JSONL). JSONL aligns with OpenClaw's gateway telemetry patterns and enables dashboard tailing without custom parsers. Decision before implementing a dashboard generator.

4. **Linking directive governance** — how much link logic belongs in the prompt vs. encoded in the schema? More prompt = flexible but less deterministic. More schema = deterministic but harder to extend.
