---
name: memspren
description: Manages a Zettelkasten-based second brain and personal knowledge graph in Obsidian using obsidian-cli. Use when the user mentions their second brain, Obsidian vault, daily check-in, PKM, brain dump, check-in, new project, new idea, met someone, task, or anything they want to capture. Also use when the user asks what they're working on, what to focus on, or wants to review their knowledge graph. Also triggers on "sync", "sync now", "push to obsidian" for vault synchronization.
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

**Layer 2 — Brain Dump Log** (write-only during conversation, NEVER read):
- `sync-buffer.md` — detailed append-only log of conversation context. Only read during sync.

**Layer 3 — Obsidian Vault** (synced at intervals or user trigger):
- Full detailed entities with YAML frontmatter, `[[wiki links]]`, proper interlinking.
- Created from brain dump log during sync. Rich, contextual, properly linked.

### Key Rules
- During conversation: read ONLY Layer 1 memory. Write to Layer 2 buffer. ZERO Obsidian interaction.
- During sync: read Layer 2 buffer → batch create/update Layer 3 Obsidian entities → recalculate Layer 1 memory → clear buffer.
- Obsidian entities are DETAILED with full context, proper wiki links, rich content.

## Prerequisites

Before any vault operation (during sync), verify obsidian-cli is available:

```bash
python scripts/check_cli.py --vault "<vault_name>"
```

**If `obsidian` command is not found:**

On macOS — install Obsidian via Homebrew:
```bash
brew install --cask obsidian
```

Then enable the CLI in Obsidian: **Settings → General → Enable CLI** (requires Obsidian 1.12.4+).

Then add it to PATH (add to `~/.zprofile` or `~/.bash_profile`):
```bash
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
source ~/.zprofile
```

Run `python scripts/check_cli.py` again to confirm all checks pass.

**If Obsidian is installed but not running:**
Tell the user: *"Obsidian needs to be open for me to sync your vault. Please open Obsidian and try again."* Never fall back to direct filesystem writes for vault content.

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

7. Check `{vault_path}/.second-brain/Memory/sync-buffer.md` — if `pending_sync: true`:
   - Notify user: "You have [X] unsynced entries. Want me to sync now or continue?"

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
2. Agent responds conversationally using Layer 1 memory for context
3. Agent appends DETAILED entry to `sync-buffer.md` (WRITE only — full context, not condensed)
4. If significant mindset/energy shift detected, update `insights.md` and `goals.md` in-place
5. Conversation continues — repeat steps 1-4
6. Synthesis tells user what was CAPTURED (not "logged to vault"): "Captured: project update for X, interaction with Y. These will sync to your vault on next sync."

**Never read sync-buffer.md during conversation. Never interact with Obsidian during conversation.**

## Sync triggers

| Trigger | How |
| --- | --- |
| User explicit | "sync now", "push to obsidian", "sync my vault" |
| Cron interval | Every `sync_interval_min` minutes (from config.md) |
| End of check-in | If `auto_sync_on_checkin_close: true` in config.md |
| Buffer overflow | If buffer exceeds `buffer_max_tokens` in config.md |

When sync triggers → read `Protocols/sync-protocol.md` and execute.

## Bundled scripts

| Script | Purpose |
| --- | --- |
| `scripts/check_cli.py` | Verify obsidian-cli is reachable and vault is accessible |
| `scripts/update_connected.py` | Safely append paths to a file's `connected:` YAML array |
| `scripts/scan_descriptions.py` | Extract frontmatter descriptions from a vault folder for smart merge decisions |
| `scripts/git_commit.py` | Commit file state before modification (safety checkpoint, nothing ever lost) |

Run `check_cli.py` before sync operations. Use `update_connected.py` for all `connected:` updates — never use `property:set` for arrays.

**Smart merge flow (during sync):** Before creating any file, run `scan_descriptions.py` to check if a similar file already exists. Before modifying any existing file, run `git_commit.py` to snapshot current state. See `Protocols/sync-protocol.md` for full flow.

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

When a user asks to create a new protocol, it is ALWAYS a custom protocol.
Only the project owner/admin can create global protocols (shipped with the skill).

Never load all protocol files at once.

## Two file locations — never mix them

| Location | What lives here | Access method |
| --- | --- | --- |
| `.second-brain/` | config.md, Memory/ (insights, goals, hot-memory, system-state, sync-buffer) | Write/Read/Edit tools directly |
| `vault_path` | All content: Work/, People/, Log/, Notes/, Tasks/, Inbox/, Archive/ | obsidian-cli (ONLY during sync) |

## Entity quick reference

| Entity | Vault path | Notes |
| --- | --- | --- |
| Project | `Work/Projects/[name].md` | — |
| Idea | `Work/Ideas/[name].md` | — |
| Person | `People/[firstname-lastname].md` | — |
| Task | `Tasks/tasks-inbox.md` | Append only, not a new file |
| Learning | `Notes/Learnings/[topic].md` | — |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | Created during sync |
| Knowledge Transfer | `Work/KT/[topic].md` + `Work/KT/Transcripts/[topic].md` | Structured doc + raw transcript |

## Critical rules

- Nothing gets deleted — archive instead
- Every vault file gets YAML frontmatter + at least one `[[link]]`
- One idea per note — atomize brain dumps
- Load files surgically — never all at once
- Always forward slashes in paths
- `connected:` arrays → always use `scripts/update_connected.py` (never `property:set`)
- insights.md stays under 700 tokens
- goals.md stays under 500 tokens
- hot-memory.md stays under 500 tokens
- sync-buffer.md is WRITE-ONLY during conversation, READ-ONLY during sync
- Brain dump log entries must be DETAILED with full context (not condensed/minimal)
- Obsidian vault entities created during sync must be DETAILED with proper wiki links

## Memory loading order

1. `.second-brain/config.md` — always first
2. `.second-brain/Memory/insights.md` — user understanding
3. `.second-brain/Memory/goals.md` — priorities + goal tracking
4. `.second-brain/Memory/hot-memory.md` — project/task state
5. `.second-brain/Memory/system-state.md` — config flags
6. `.second-brain/Memory/sync-buffer.md` — check pending_sync flag only (do NOT read entries)
7. Individual vault files — ONLY during sync or when user asks about something specific
