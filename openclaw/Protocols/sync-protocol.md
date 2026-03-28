# Sync Protocol

Governs batch synchronisation from rotating sync buffers to Obsidian vault.

**Triggered by:** user explicit ("sync now"), cron interval, end of check-in, or buffer overflow.

**Architecture:** deterministic Lobster pipeline. The agent fires one Lobster tool call;
Lobster executes the full pipeline and returns a structured result. The LLM is not in the
loop between steps — it is only invoked inside the explicit `llm-task` steps defined in
`workflows/sync.lobster`.

---

## How to invoke

When sync triggers, execute:

```bash
lobster run workflows/sync.lobster \
  --args-json '{"vault_path":"<absolute path to vault root>","vault_name":"<exact name shown in Obsidian → Manage vaults>","config_path":"<vault_path>/.second-brain/config.md"}'
```

The pipeline runs through Stage 0–3 automatically and pauses at the **approval gate** (Stage 4d).
It returns a `resumeToken`.

---

## Pipeline stages (summary)

| Stage | Name | What happens |
|---|---|---|
| 0 | Pre-flight | Lock file, obsidian-cli check, vault git diff, task inbox scan, buffer rotation |
| 1 | Extraction | Single heavy llm-task reads the buffer once, returns structured raw material |
| 2 | Parallel refinement | 4 llm-task jobs run simultaneously: insights, goals, tasks, hot-memory |
| 3 | Merge + write Layer 1 | Validates and writes `.second-brain/Memory/` files (no vault writes yet) |
| 4a | Frontmatter scan | Batch reads YAML frontmatter from classifier-scoped vault folders |
| 4b | Entity plan | Single heavy llm-task generates the full vault write plan |
| 4d | **Approval gate** | Pipeline pauses — agent presents write plan to user, waits for approval |
| 4c | Entity writes | Per-entity: content directive → linking directive → write (parallel) |
| 5 | Metrics + cleanup | metrics.json, buffer archive, system-state.md, system-log, lock release |

Full step-by-step spec is in `workflows/sync.lobster`.

---

## Handling the approval gate

When Lobster returns a `resumeToken`, present the approval message to the user:

```
Sync ready to write.

Memory: <Layer 1 summary — e.g. "insights OK, goals OK, tasks OK, hot-memory FALLBACK">
Vault:  <entity plan summary — e.g. "2 create, 1 append, 1 merge">
Manual edits absorbed: <N>

Proceed with vault writes?
```

**User says yes / approves:**
Resume the pipeline with the token:
```
lobster resume <resumeToken> --approve
```

**User says no / declines:**
```
lobster resume <resumeToken> --decline
```
Buffer is preserved. Safe to re-trigger sync — all data is intact.

**Token expires (default TTL: 24 hours):**
Sync must be re-triggered. Buffer is intact. Stale tokens are pruned at the end of Stage 5.

---

## Config requirements

The following fields must be present in `.second-brain/config.md` before the pipeline runs:

```yaml
# Agent routing (must exist in OpenClaw agents.list)
agents:
  heavy: memspren-heavy    # extraction, insights, entity plan
  light: memspren-light    # goals, tasks, hot-memory, content, linking
  default: main            # fallback if named agents not found

# Logging
logging:
  verbosity: INFO          # ERROR | WARN | INFO | DEBUG
  max_log_bytes: 2097152   # 2 MB telemetry log rotation threshold
  keep_lines: 2000         # lines to keep after rotation

# Lobster
lobster:
  resume_token_ttl_hours: 24
```

If `agents.heavy` or `agents.light` are absent, all directives fall back to `agents.default`.

---

## Agent prerequisites

Two named agents must exist in OpenClaw before the pipeline can run:

| Agent ID | Role | Suggested model |
|---|---|---|
| `memspren-heavy` | Extraction, insights, entity plan | Sonnet or Opus |
| `memspren-light` | Goals, tasks, hot-memory, content, linking | Haiku or Sonnet |

```bash
python scripts/create_agents.py
```

The script runs `openclaw agents add` for each agent and OpenClaw opens an interactive panel to set the model. Or add them manually:

```bash
openclaw agents add memspren-heavy
openclaw agents add memspren-light
```

If neither agent is configured, all directives fall back to `default` — this works but loses
the heavy/light routing benefit.

---

## Pre-flight failure modes

| Failure | Pipeline behaviour |
|---|---|
| `sync.lock` exists | Exit with SYNC SKIPPED (concurrent run) — buffer safe |
| obsidian-cli unavailable | Switch to filesystem write mode — pipeline continues |
| vault not a git repo | Skip bidirectional edit ingestion — pipeline continues |
| no sealed buffers + active buffer empty | Exit with "Nothing to sync." |
| rotate_buffer fails | Log ERROR, abort — buffer intact |

---

## Stage 2 failure handling

Each of the 4 parallel refinement jobs is independent:

| Job result | What happens |
|---|---|
| OK + schema valid | File written to `.second-brain/Memory/` |
| llm-task failed / timed out | Existing file kept, logged as WARN |
| Schema validation failed | Existing file kept, logged as WARN |
| All 4 fail | Pipeline aborts before vault writes |

---

## Telemetry

Every step writes to `.second-brain/Memory/sync-telemetry.log`. Log format:

```
[ISO ts] [LEVEL] [runner] action=<step> result=OK|FAIL|TIMEOUT detail=<...>
```

Check this file to diagnose exactly where a failure occurred.
Set `logging.verbosity: DEBUG` in config.md to capture full prompt/response pairs.

---

## Confirming to user

After Lobster returns final results, send a natural confirmation:

> "Synced. Created [X], updated [Y]. Memory files updated: insights, goals, tasks, hot-memory."

If any entity writes failed, name them:
> "Synced. 3 of 4 entities written. Failed: Work/Projects/foo.md (write error — check telemetry log)."

If Stage 2 had fallbacks:
> "Synced. Vault is up to date. Note: hot-memory update fell back to existing file — will retry on next sync."

---

## Filesystem fallback path

When obsidian-cli is unavailable, the pipeline uses direct filesystem writes.
Output is identical. The git_commit.py safety snapshot runs regardless of write path.

After a filesystem-mode sync, allow Obsidian to complete its rescan on next launch
before triggering another sync (Obsidian reconciles its index against changed files).
