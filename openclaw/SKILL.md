---
name: memspren
description: Manages a Zettelkasten-based second brain and personal knowledge graph in Obsidian using obsidian-cli and a deterministic Lobster sync pipeline. Use when the user mentions their second brain, Obsidian vault, daily check-in, PKM, brain dump, check-in, new project, new idea, met someone, task, or anything they want to capture. Also use when the user asks what they're working on, what to focus on, or wants to review their knowledge graph. Also triggers on "sync", "sync now", "push to obsidian" for vault synchronization.
---

# memspren

Zettelkasten-powered knowledge graph in Obsidian. Every entity is a node. Every connection is a `[[link]]`. The agent is the thinking partner — not just a storage system.

## Architecture: Memory + Buffer + Sync

Three-layer system optimized for token efficiency:

**Layer 1 — Active Memory** (read every session, stays in context ~2000 tokens total):
- `insights.md` (700 tokens) — inference about user: patterns, energy, mindset, what works/doesn't
- `goals.md` (500 tokens) — immediate priorities + weekly/quarterly micro-goal tracking
- `hot-memory.md` (500 tokens) — project/task state only
- `system-state.md` (~300 tokens) — config, flags, inventory

**Layer 2 — Rotating Sync Buffers** (write-only during conversation, NEVER read):
- `sync-buffer.md` — detailed append-only log of conversation context. Only read during sync.

**Layer 3 — Obsidian Vault** (synced at intervals or user trigger):
- Full detailed entities with YAML frontmatter, `[[wiki links]]`, proper interlinking.
- Created from brain dump log during sync. Rich, contextual, properly linked.

### Key Rules
- During conversation: read ONLY Layer 1 memory. Write to Layer 2 buffer. ZERO Obsidian interaction.
- During sync: Lobster pipeline reads Layer 2 buffer → batch create/update Layer 3 vault entities → recalculate Layer 1 memory → archive buffer.
- Vault entities are DETAILED with full context, proper wiki links, rich content.

## Sync pipeline

The sync is a **deterministic Lobster pipeline** — not LLM-orchestrated steps. One Lobster tool call fires the entire pipeline; the LLM only runs inside the explicit `llm-task` directives defined in `workflows/sync.lobster`.

```
[trigger] → [pre-flight] → [extraction] → [parallel refinement]
          → [merge layer 1] → [entity pipeline] → [approval gate]
          → [entity writes] → [metrics + cleanup]
```

See `Protocols/sync-protocol.md` for invocation, approval gate handling, and error reference.
See `workflows/sync.lobster` for the full pipeline spec.

### Tool requirements

Enable both tools in your OpenClaw agent config:

```json
{
  "tools": { "alsoAllow": ["lobster", "llm-task"] }
}
```

### Agent prerequisites

Two named agents must exist in OpenClaw before the pipeline can run:

| Agent ID | Role | Suggested model |
|---|---|---|
| `memspren-heavy` | Extraction, insights, entity plan | Sonnet or Opus |
| `memspren-light` | Goals, tasks, hot-memory, content, linking | Haiku or Sonnet |

```bash
openclaw agents add memspren-heavy
openclaw agents add memspren-light
```

If neither exists, all directives fall back to the `default` agent.

## Prerequisites

Install and configure Obsidian CLI before first sync (obsidian-cli is optional — filesystem fallback activates automatically when it's unavailable):

```bash
brew install --cask obsidian
# Enable CLI in Obsidian: Settings → General → Enable CLI (requires 1.12.4+)
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
```

Verify: `python scripts/check_cli.py --vault "<vault_name>"`

## Session start

Every session, in this order:

1. **Check workspace root for `.memspren-config`** — contains vault_path + setup_complete flag
   - If exists → use vault_path from this file
   - If not exists → run setup (user provides vault path, then create `.memspren-config`)

2. Read `{vault_path}/.second-brain/config.md` — vault-specific settings

3. Load `{vault_path}/.second-brain/Memory/insights.md` — user understanding

4. Load `{vault_path}/.second-brain/Memory/goals.md` — immediate priorities + tracking

5. Load `{vault_path}/.second-brain/Memory/hot-memory.md` — project/task state

6. Load `{vault_path}/.second-brain/Memory/system-state.md` — active protocols and flags

7. Check `{vault_path}/.second-brain/Memory/sync-buffer.md` — if `pending_sync: true`:
   - Notify user: "You have [X] unsynced entries. Want me to sync now or continue?"

If setup hasn't run yet (no `.memspren-config` at workspace root), start setup protocol.

## Intent detection

| User says | Action |
| --- | --- |
| Check-in / how was my day / brain dump / end of day | Read `Protocols/check-in-protocol.md` |
| New project / working on something | Read `Protocols/entity-protocol.md` → Project |
| New idea / thought / realization | Read `Protocols/entity-protocol.md` → Idea |
| Met someone / talked to someone | Read `Protocols/entity-protocol.md` → Person |
| Task / reminder / need to do | Read `Protocols/entity-protocol.md` → Task |
| Something I learned / read / figured out | Read `Protocols/entity-protocol.md` → Learning |
| What am I working on / status | Use active memory (insights + goals + hot-memory) → summarize |
| What should I focus on | Use goals.md + insights.md → advise |
| Sync now / push to obsidian / sync my vault | Read `Protocols/sync-protocol.md` → invoke Lobster pipeline |
| Matches a custom_protocol trigger in config.md | Load custom protocol from `.second-brain/Protocols/` |

## Conversation flow (during brain dumps and check-ins)

1. User shares brain dump / check-in / update
2. Agent responds conversationally using Layer 1 memory for context
3. Agent appends DETAILED entry to `sync-buffer.md` (WRITE only — full context, not condensed)
4. If significant mindset/energy shift detected, update `insights.md` and `goals.md` in-place
5. Conversation continues — repeat steps 1-4
6. Synthesis tells user what was CAPTURED: "Captured: project update for X, interaction with Y. These will sync to your vault on next sync."

**Never read sync-buffer.md during conversation. Never interact with Obsidian during conversation.**

## Sync triggers

| Trigger | How |
| --- | --- |
| User explicit | "sync now", "push to obsidian", "sync my vault" |
| Cron interval | Every `sync_interval_min` minutes (from config.md) |
| End of check-in | If `auto_sync_on_checkin_close: true` in config.md |
| Buffer overflow | If buffer exceeds `buffer_max_tokens` in config.md |

When sync triggers → read `Protocols/sync-protocol.md` and invoke the Lobster pipeline.

## Bundled scripts

| Script | Status | Purpose |
| --- | --- | --- |
| `scripts/check_cli.py` | Existing (updated) | Verify obsidian-cli; resolve write mode (--json flag for pipeline) |
| `scripts/rotate_buffer.py` | Existing (updated) | Buffer rotation; --sync-check mode for pipeline pre-flight |
| `scripts/runner.py` | New | Enforce JSON-only stdout contract for all Lobster script steps |
| `scripts/write_lock.py` | New | Write/release sync.lock; prune stale Lobster resume tokens |
| `scripts/clean_exit.py` | New | Clean exit signal when nothing to sync |
| `scripts/vault_diff_scanner.py` | New | Git diff since last_sync → manually changed vault files |
| `scripts/task_inbox_scanner.py` | New | Parse + deduplicate tasks-inbox.md |
| `scripts/read_frontmatter.py` | New | Classifier-scoped batch frontmatter read for merge detection |
| `scripts/parallel_memory.py` | New | ThreadPoolExecutor dispatcher for Stage 2 parallel refinement |
| `scripts/merge.py` | New | Collect + validate Stage 2 outputs + write Layer 1 memory files |
| `scripts/entity_pipeline.py` | New | Per-entity content directive, linking directive, and vault write |
| `scripts/metrics_writer.py` | New | Write metrics.json, archive buffers, update system-state.md |
| `scripts/git_commit.py` | Existing | Pre-modification git snapshot (nothing ever lost) |
| `scripts/update_connected.py` | Existing | Safe connected: array updates |
| `scripts/scan_descriptions.py` | Existing | Merge decision support |

**Critical stdout contract:** every script run by Lobster must emit ONLY valid JSON to stdout.
Always invoke scripts via `python -m scripts.runner scripts/foo.py` — the runner wrapper
enforces the contract, captures stderr to the telemetry log, and emits structured JSON errors
on failure. Never run scripts directly from a Lobster step.

## Protocol files (load only when needed)

| File | Load when |
| --- | --- |
| `Protocols/setup-protocol.md` | `setup_complete: false` |
| `Protocols/check-in-protocol.md` | User initiates a check-in |
| `Protocols/entity-protocol.md` | During sync — creating or updating vault entities |
| `Protocols/linking-protocol.md` | During sync — writing or updating vault files |
| `Protocols/sync-protocol.md` | Sync triggered (user, cron, or auto) |

**Custom protocols** (user's vault — `.second-brain/Protocols/`):
Loaded from `custom_protocols` section in config.md. Agent checks triggers at intent detection time.
Custom protocols are user-specific — they stay in the vault, never in the skill package.

Never load all protocol files at once.

## config.md required fields

The following fields must exist in `.second-brain/config.md` for the new pipeline:

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

## Two file locations — never mix them

| Location | What lives here | Access method |
| --- | --- | --- |
| `.second-brain/` | config.md, Memory/ (insights, goals, hot-memory, system-state, sync-buffer, metrics.json, sync-telemetry.log) | Write/Read/Edit tools directly |
| `vault_path` | All content: Work/, People/, Log/, Notes/, Tasks/, Inbox/, Archive/, Logs/ | obsidian-cli or filesystem (ONLY during sync) |

## Skill folder structure

```
openclaw/
├── SKILL.md
├── Protocols/
│   ├── sync-protocol.md       ← invocation + approval gate reference
│   ├── check-in-protocol.md
│   ├── entity-protocol.md
│   ├── linking-protocol.md
│   └── setup-protocol.md
├── workflows/
│   └── sync.lobster           ← full pipeline spec (6 stages)
├── schemas/
│   ├── extraction_schema.json
│   ├── insights_schema.json
│   ├── goals_schema.json
│   ├── tasks_schema.json
│   ├── hot_memory_schema.json
│   ├── entity_plan_schema.json
│   ├── entity_content_schema.json
│   └── entity_linking_schema.json
├── prompts/
│   ├── extraction_prompt.txt
│   ├── insights_prompt.txt
│   ├── goals_prompt.txt
│   ├── tasks_prompt.txt
│   ├── hot_memory_prompt.txt
│   ├── entity_plan_prompt.txt
│   ├── entity_content_prompt.txt
│   └── entity_linking_prompt.txt
└── scripts/
    ├── runner.py              ← JSON stdout enforcer (wrap ALL Lobster script calls)
    ├── write_lock.py
    ├── clean_exit.py
    ├── vault_diff_scanner.py
    ├── task_inbox_scanner.py
    ├── read_frontmatter.py
    ├── parallel_memory.py
    ├── merge.py
    ├── entity_pipeline.py
    ├── metrics_writer.py
    ├── check_cli.py           ← updated with --json flag
    ├── rotate_buffer.py       ← updated with --sync-check flag
    ├── git_commit.py
    ├── update_connected.py
    ├── scan_descriptions.py
    ├── run_extraction.py
    ├── run_entity_plan.py
    └── create_agents.py        ← one-time setup: adds memspren-heavy/light agents
```

## Entity quick reference

| Entity | Vault path | Notes |
| --- | --- | --- |
| Project | `Work/Projects/[name].md` | — |
| Idea | `Work/Ideas/[name].md` | — |
| Person | `People/[firstname-lastname].md` | — |
| Task | `Tasks/tasks-inbox.md` | Append only, not a new file |
| Learning | `Notes/Learnings/[topic].md` | — |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | Created during sync |
| Knowledge Transfer | `Work/KT/[topic].md` | — |

## Critical rules

- Nothing gets deleted — archive instead
- Every vault file gets YAML frontmatter + at least one `[[link]]`
- Every vault file gets a `description` field in frontmatter (merge detection key)
- One idea per note — atomize brain dumps
- Load files surgically — never all at once
- Always forward slashes in paths
- `connected:` arrays → always use `scripts/update_connected.py`
- insights.md stays under 700 tokens
- goals.md stays under 500 tokens
- hot-memory.md stays under 500 tokens
- Sync buffers are WRITE-ONLY during conversation, READ-ONLY during sync
- Brain dump entries must be DETAILED with full context (not condensed)
- Vault entities created during sync must be DETAILED with proper wiki links
- All Lobster script steps must use `python -m scripts.runner` — never raw script invocation

## What never happens

- Deleting any vault file (archive it instead)
- Saving a note without YAML frontmatter
- Saving a note without a `description` field in frontmatter
- Saving a note without at least one `[[link]]`
- Loading all protocol files in a single session
- Reading sync buffers during conversation
- Interacting with the vault during conversation (only during sync)
- Windows-style backslash paths
- Writing config.md or Memory files into vault content folders
- Emitting non-JSON text to stdout from any Lobster script step
