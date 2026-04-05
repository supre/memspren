---
name: memspren
description: Manages a Zettelkasten-based second brain and personal knowledge graph in Obsidian using a deterministic Lobster sync pipeline. Use when the user mentions their second brain, Obsidian vault, daily check-in, PKM, brain dump, check-in, new project, new idea, met someone, task, or anything they want to capture. Also use when the user asks what they're working on, what to focus on, or wants to review their knowledge graph. Also triggers on "sync", "sync now", "push to obsidian" for vault synchronization.
---

# memspren

Zettelkasten-powered knowledge graph in Obsidian. Every entity is a node. Every connection is a `[[link]]`. The agent is the thinking partner — not just a storage system.

## Architecture: Memory + Buffer + Sync

Three-layer system optimized for token efficiency:

**Layer 1 — Active memory** (read every session, stays in context):

- `insights.md` — inference about user: patterns, energy, mindset, what works/doesn't
- `goals.md` — immediate priorities + weekly/quarterly micro-goal tracking
- `tasks.md` — open tasks, recently completed, blocked
- `hot-memory.md` — project/task state only
- `system-state.md` — config, flags, inventory

**Layer 2 — Rotating Sync Buffers** (write-only during conversation, NEVER read):

- `sync-buffer-NNN.md` — detailed append-only log of conversation context. Only read during sync.

**Layer 3 — Obsidian Vault** (synced at intervals or user trigger):

- Full detailed entities with YAML frontmatter, `[[wiki links]]`, proper interlinking.
- Created from buffer during sync by the Lobster pipeline.

### Key Rules

- During conversation: read ONLY Layer 1 memory. Write to Layer 2 buffer. ZERO Obsidian interaction.
- During sync: Lobster pipeline reads Layer 2 buffer → batch create/update Layer 3 vault entities → recalculate Layer 1 memory → archive buffer.

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

| Agent ID         | Role                                       | Suggested model |
| ---------------- | ------------------------------------------ | --------------- |
| `memspren-heavy` | Extraction, insights, entity plan          | Sonnet or Opus  |
| `memspren-light` | Goals, tasks, hot-memory, content, linking | Haiku or Sonnet |

```bash
openclaw agents add memspren-heavy
openclaw agents add memspren-light
```

If neither exists, all directives fall back to the `default` agent.

## Session start

Every session, in this order:

1. **Check workspace root for `.memspren-config`** — contains vault_path + setup_complete flag
   - If exists → verify vault_path is accessible (`.second-brain/config.md` must exist)
   - If not exists → run setup (user provides vault path, then create `.memspren-config`)

2. Read `{vault_path}/.second-brain/config.md` — vault-specific settings

3. Load `{vault_path}/.second-brain/memory/insights.md` — user understanding

4. Load `{vault_path}/.second-brain/memory/goals.md` — immediate priorities + tracking

5. Load `{vault_path}/.second-brain/memory/tasks.md` — open tasks, blocked, recently done

6. Load `{vault_path}/.second-brain/memory/hot-memory.md` — project/task state

7. Load `{vault_path}/.second-brain/memory/system-state.md` — active protocols and flags

8. Check for unsynced buffer content:
   ```bash
   uv run -m scripts.memcli get-active-buffer --vault-path "{vault_path}"
   ```
   If `entry_count > 0` → notify user: "You have [X] unsynced entries. Want me to sync now or continue?"

If setup hasn't run yet (no `.memspren-config` at workspace root), start setup protocol.

## Intent detection

| User says                                                                     | Action                                                        |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Check-in / how was my day / brain dump / end of day                           | Read `Protocols/check-in-protocol.md`                         |
| New project / working on / new idea / met someone / task / learned something  | Capture to sync buffer (append entry to active buffer)        |
| What am I working on / status                                                 | Use active memory (insights + goals + hot-memory) → summarize |
| What should I focus on                                                        | Use goals.md + insights.md → advise                           |
| Sync now / push to obsidian / sync my vault                                   | Read `Protocols/sync-protocol.md` → invoke Lobster pipeline   |
| Matches a custom_protocol trigger in config.md                                | Load custom protocol from `.second-brain/Protocols/`          |

## Conversation flow (during brain dumps and check-ins)

1. User shares brain dump / check-in / update
2. Agent responds conversationally using Layer 1 memory for context
3. Before appending, get the active buffer path:
   ```bash
   uv run -m scripts.memcli get-active-buffer --vault-path "{vault_path}"
   ```
   Use the returned `path` to append the entry. If `rotated: true`, a new buffer was created — note it.
4. Agent appends DETAILED entry to the active buffer (WRITE only — full context, not condensed)
5. If significant mindset/energy shift detected, update `insights.md` and `goals.md` in-place
6. Conversation continues — repeat steps 1–5
7. Synthesis tells user what was captured: "Captured: project update for X, interaction with Y. These will sync to your vault on next sync."

**Never read sync buffers during conversation. Never interact with Obsidian during conversation.**

## Sync triggers

| Trigger         | How                                                |
| --------------- | -------------------------------------------------- |
| User explicit   | "sync now", "push to obsidian", "sync my vault"    |
| Cron interval   | Every `sync_interval_min` minutes (from config.md) |
| End of check-in | If `auto_sync_on_checkin_close: true` in config.md |
| Buffer overflow | If buffer exceeds `buffer_max_tokens` in config.md |

When sync triggers → read `Protocols/sync-protocol.md` and invoke the Lobster pipeline.

## memcli — sync engine

`memcli` is the CLI that drives the Lobster sync pipeline. It is installed as a standalone command.

**Running memcli:**
- Execute directly: `memcli <command> [args]`
- If the `memcli` command is not found, it has not been installed — do not try `uv run -m scripts.memcli` as a fallback; tell the user to run the install step.

**Logs:**
- All memcli output is logged to `/tmp/memcli/memcli-YYYY-MM-DD.log` (daily rotation)
- To check what happened during the last sync: read today's log at `/tmp/memcli/memcli-$(date +%Y-%m-%d).log`
- Logs include DEBUG, INFO, WARN, ERROR entries — scan for ERROR/WARN lines when diagnosing failures

**Common memcli commands:**
- `memcli check-cli --vault-path <path> --vault <name> --json` — verify obsidian-cli works
- `memcli vault-diff --vault-path <path>` — show recent vault changes
- `memcli rotate-buffer --vault-path <path> --sync-check` — rotate/check buffer state

## Protocol files (load only when needed)

| File                             | Load when                            |
| -------------------------------- | ------------------------------------ |
| `Protocols/setup-protocol.md`    | `setup_complete: false`              |
| `Protocols/check-in-protocol.md` | User initiates a check-in            |
| `Protocols/sync-protocol.md`     | Sync triggered (user, cron, or auto) |

**Custom protocols** (user's vault — `.second-brain/Protocols/`):
Loaded from `custom_protocols` section in config.md. Agent checks triggers at intent detection time.
Custom protocols are user-specific — they stay in the vault, never in the skill package.

Never load all protocol files at once.

## config.md required fields

The following fields must exist in `.second-brain/config.md` for the pipeline:

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

## File locations

| Location                   | What lives here                                                                | Access                                   |
| -------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------- |
| `.second-brain/memory/`    | insights.md, goals.md, tasks.md, hot-memory.md, system-state.md, metrics.json | Write/Read/Edit tools directly           |
| `.second-brain/buffers/`   | sync-buffer-NNN.md (rotating, append-only during conversation)                 | Write/Edit tools directly                |
| `.second-brain/run/`       | Pipeline run artifacts (buffer-content.txt, state files)                       | Written by memcli, not by agent directly |
| `.second-brain/logs/`      | sync-telemetry.log (Lobster envelope trace)                                    | Written by Lobster runner                |
| `/tmp/memcli/`             | memcli-YYYY-MM-DD.log (daily rotation, detailed step logs)                     | Written by memcli                        |
| `.second-brain/config.md`  | Vault-specific settings, agent routing, sync schedule                          | Read tool                                |
| `vault_path` (content)     | Work/, People/, Log/, Notes/, Tasks/, Inbox/, Archive/, Logs/                  | Lobster pipeline only (never during conversation) |

## Entity quick reference

| Entity             | Vault path                                      | Notes                       |
| ------------------ | ----------------------------------------------- | --------------------------- |
| Project            | `Work/Projects/[name].md`                       | —                           |
| Idea               | `Work/Ideas/[name].md`                          | —                           |
| Person             | `People/[firstname-lastname].md`                | —                           |
| Task               | `Tasks/tasks-inbox.md`                          | Append only, not a new file |
| Learning           | `Notes/Learnings/[category]/[topic].md`         | e.g. `business/pricing-strategy.md` |
| Pattern            | `Notes/Patterns/[name].md`                      | —                           |
| Daily log          | `Log/Daily/YYYY-MM-DD.md`                       | Created during sync         |
| Knowledge Transfer | `Work/KT/[topic].md`                            | —                           |

## Critical rules

- Nothing gets deleted — archive instead
- Always forward slashes in paths
- Sync buffers are WRITE-ONLY during conversation, READ-ONLY during sync
- Brain dump entries must be DETAILED with full context (not condensed)

## What never happens

- Deleting any vault file (archive it instead)
- Reading sync buffers during conversation
- Interacting with the vault during conversation (only during sync)
- Loading all protocol files in a single session
- Writing config.md or memory files into vault content folders
- Windows-style backslash paths
