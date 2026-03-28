---
name: memspren
description: Manages a Zettelkasten-based second brain and personal knowledge graph in Obsidian. Use when the user mentions their second brain, Obsidian vault, daily check-in, PKM, brain dump, check-in, new project, new idea, met someone, task, or anything they want to capture. Also use when the user asks what they're working on, what to focus on, or wants to review their knowledge graph. Also triggers on "sync", "sync now", "push to obsidian" for vault synchronization.
---

# memspren

Zettelkasten-powered knowledge graph in Obsidian. Every entity is a node. Every connection is a `[[link]]`. Claude is the thinking partner — not just a storage system.

## Architecture: Memory + Buffer + Sync

Three-layer system optimized for token efficiency:

**Layer 1 — Active Memory** (read every session, stays in context ~2000 tokens total):
- `insights.md` (700 tokens) — inference about user: patterns, energy, mindset, what works/doesn't
- `goals.md` (500 tokens) — immediate priorities + weekly/quarterly micro-goal tracking
- `hot-memory.md` (500 tokens) — project/task state only
- `system-state.md` (~300 tokens) — config, flags, inventory

**Layer 2 — Rotating Sync Buffers** (write-only during conversation, NEVER read):
- `sync-buffer-001.md`, `sync-buffer-002.md`, etc. — detailed append-only log of conversation context
- `sync-buffer-active.txt` — pointer to the currently active buffer ID
- When active buffer hits 1500 words, seal it and create a new one
- Only read during sync. Each sync processes one sealed buffer (bounded context).

**Layer 3 — Obsidian Vault** (synced at intervals or user trigger):
- Full detailed entities with YAML frontmatter, `[[wiki links]]`, proper interlinking.
- Created from brain dump log during sync. Rich, contextual, properly linked.

### Key Rules
- During conversation: read ONLY Layer 1 memory. Write to Layer 2 buffer. ZERO vault interaction.
- During sync: read Layer 2 buffer → batch create/update Layer 3 vault entities → recalculate Layer 1 memory → archive buffer.
- Vault entities are DETAILED with full context, proper wiki links, rich content.

## File locations

Two separate locations. Never mix them up.

| Location | What lives here | Access method |
| --- | --- | --- |
| `.second-brain/` | config.md, Memory/ (insights, goals, hot-memory, system-state, sync buffers) | Read/Write/Edit tools directly |
| `vault_path` | All content: Work/, People/, Log/, Notes/, Tasks/, Inbox/, Archive/ | Read/Write/Edit tools (ONLY during sync) |

The `.second-brain/` folder is at the root of the Cowork mounted folder.
It is hidden from Obsidian's graph by default (dot-prefix).
`vault_path` in config.md points to the user's Obsidian vault — this is
where all note content gets written.

If vault_path equals the mounted folder root, the vault and skill folder
are in the same place — that's fine. `.second-brain/` is still separate.

## Session start

Every session, in this order:

1. **Check workspace root for `.memspren-config`** — contains vault_path + setup_complete flag
   - If exists → use vault_path from this file
   - If not exists → run setup (user provides vault path, then create `.memspren-config`)

2. Read `{vault_path}/.second-brain/config.md` — vault-specific settings (check-in time, thresholds, sync settings)

3. Load `{vault_path}/.second-brain/Memory/insights.md` — user understanding (patterns, energy, mindset)

4. Load `{vault_path}/.second-brain/Memory/goals.md` — immediate priorities + weekly/quarterly tracking

5. Load `{vault_path}/.second-brain/Memory/hot-memory.md` — project/task state

6. Load `{vault_path}/.second-brain/Memory/system-state.md` — active protocols and flags

7. Check for sealed sync buffers — read `sync-buffer-active.txt`, then check for any `sync-buffer-*.md` files with `state: sealed` in frontmatter:
   - If sealed buffers exist, notify user: "You have [X] unsynced entries. Want me to sync now or continue?"

8. **Re-create cron jobs** — read `sync_interval_cron` from config.md. If sync times are configured, re-create cron jobs using CronCreate (cron jobs are session-scoped and don't persist across sessions).

If setup hasn't run yet (no `.memspren-config` at workspace root), start setup protocol.

Memory files may not exist on first run — that's expected. Create them on first sync.

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
| Sync now / push to obsidian / sync my vault | Read `Protocols/sync-protocol.md` → execute sync |
| Matches a custom_protocol trigger in config.md | Load custom protocol from `.second-brain/Protocols/` |

## Conversation flow (during brain dumps and check-ins)

1. User shares brain dump / check-in / update
2. Claude responds conversationally using Layer 1 memory for context
3. Claude appends DETAILED entry to the active sync buffer (WRITE only — full context, not condensed)
4. If significant mindset/energy shift detected, update `insights.md` and `goals.md` in-place
5. Conversation continues — repeat steps 1-4
6. Synthesis tells user what was CAPTURED (not "logged to vault"): "Captured: project update for X, interaction with Y. These will sync to your vault on next sync."

**Never read sync buffers during conversation. Never interact with the vault during conversation.**

## Sync triggers

| Trigger | How |
| --- | --- |
| User explicit | "sync now", "push to obsidian", "sync my vault" |
| Cron interval | Every `sync_interval_cron` (from config.md, re-created each session via CronCreate) |
| End of check-in | If `auto_sync_on_checkin_close: true` in config.md |
| Buffer overflow | If active buffer exceeds 1500 words (seal and sync) |

When sync triggers → read `Protocols/sync-protocol.md` and execute.

## Protocol files (load only when needed)

| File | Load when |
| --- | --- |
| `Protocols/setup-protocol.md` | `setup_complete: false` |
| `Protocols/check-in-protocol.md` | User initiates a check-in |
| `Protocols/entity-protocol.md` | During sync — creating or updating vault entities |
| `Protocols/linking-protocol.md` | During sync — writing or updating vault files |
| `Protocols/sync-protocol.md` | Sync triggered (user, cron, or auto) |

**Custom protocols** (user's vault — `.second-brain/Protocols/`):

Loaded from `custom_protocols` section in config.md. Claude checks triggers at intent detection time.
Custom protocols are user-specific — they stay in the vault, never in the skill package.

When a user asks to create a new protocol, it is ALWAYS a custom protocol.
Only the project owner/admin can create global protocols (shipped with the skill).

Never load all protocol files at once.

## Native operations (no external scripts needed)

Claude performs all operations natively using built-in tools:

| Operation | How |
| --- | --- |
| Scan folder for descriptions | Glob to list `.md` files in target folder, Read each file's first ~20 lines for frontmatter `description` field |
| Update connected arrays | Read file, parse `connected:` YAML list, append new paths, deduplicate, Write back |
| Git safety checkpoints | If git is available, run `git add [file] && git commit -m "pre-sync snapshot"` via Bash before modifying existing vault files |
| Buffer rotation | Read `sync-buffer-active.txt` for current ID, check word count of active buffer, seal if >= 1500 words (Edit frontmatter `state: sealed`), create new buffer (Write), update pointer (Write) |

## Entity quick reference

| Entity | Vault path | Notes |
| --- | --- | --- |
| Project | `Work/Projects/[name].md` | — |
| Idea | `Work/Ideas/[name].md` | — |
| Person | `People/[firstname-lastname].md` | — |
| Task | `Tasks/tasks-inbox.md` | Append only, not a new file |
| Learning | `Notes/Learnings/[topic].md` | — |
| Pattern | `Notes/Patterns/[name].md` | Recurring behavioral themes with evidence |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | Created during sync |

## Critical rules

- Nothing gets deleted — archive instead
- Every vault file gets YAML frontmatter + at least one `[[link]]`
- Every vault file gets a `description` field in frontmatter (one-line summary for merge detection)
- One idea per note — atomize brain dumps
- Load files surgically — never all at once
- Always forward slashes in paths
- `connected:` arrays → Read file, parse, append, deduplicate, Write back
- insights.md stays under 700 tokens
- goals.md stays under 500 tokens
- hot-memory.md stays under 500 tokens
- Sync buffers are WRITE-ONLY during conversation, READ-ONLY during sync
- Brain dump log entries must be DETAILED with full context (not condensed/minimal)
- Vault entities created during sync must be DETAILED with proper wiki links

## Memory loading order

1. `.second-brain/config.md` — always first
2. `.second-brain/Memory/insights.md` — user understanding
3. `.second-brain/Memory/goals.md` — priorities + goal tracking
4. `.second-brain/Memory/hot-memory.md` — project/task state
5. `.second-brain/Memory/system-state.md` — config flags
6. `.second-brain/Memory/sync-buffer-active.txt` + sealed buffer check — check for pending syncs (do NOT read buffer entries)
7. Individual vault files — ONLY during sync or when user asks about something specific

## Vault structure (content — lives at vault_path)

```
Vision/        Strategy/      Work/Projects/    Work/Ideas/
People/        Tasks/         Log/Daily/        Notes/Learnings/
Notes/Patterns/               Inbox/            Archive/
Logs/
```

## Skill folder structure (operational — lives at .second-brain/)

```
.second-brain/
├── config.md
└── Memory/
    ├── insights.md
    ├── goals.md
    ├── hot-memory.md
    ├── system-state.md
    ├── sync-buffer-active.txt
    ├── sync-buffer-001.md
    └── sync-archive/
```

## What never happens

- Deleting any vault file (archive it instead)
- Saving a note without YAML frontmatter
- Saving a note without at least one `[[link]]`
- Saving a note without a `description` field in frontmatter
- Loading all reference files in a single session
- Reading sync buffers during conversation
- Interacting with the vault during conversation (only during sync)
- Windows-style backslash paths
- Writing config.md or Memory files into the vault content folders
