---
name: memspren
description: Manages a Zettelkasten-based second brain and personal knowledge graph in Obsidian using obsidian-cli. Use when the user mentions their second brain, Obsidian vault, daily check-in, PKM, brain dump, check-in, new project, new idea, met someone, task, or anything they want to capture. Also use when the user asks what they're working on, what to focus on, or wants to review their knowledge graph.
---

# memspren

Zettelkasten-powered knowledge graph in Obsidian. Every entity is a node. Every connection is a `[[link]]`. Claude is the thinking partner — not just a storage system.

## Prerequisites

Before any vault operation, verify obsidian-cli is available:

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
Tell the user: *"Obsidian needs to be open for me to update your vault. Please open Obsidian and try again."* Never fall back to direct filesystem writes.

## Session start

Every session, in this order:

1. Read `.second-brain/config.md` — always first (vault path, setup status)
2. Load `.second-brain/Memory/hot-memory.md` — current week context
3. Load `.second-brain/Memory/system-state.md` — active protocols and flags
4. Check `setup_complete` in config.md

If `setup_complete: false` → read `Protocols/setup-protocol.md` and follow it.
If `setup_complete: true` → proceed to intent detection.

Neither Memory file exists on first run — that's expected. Just read config.md.

## Intent detection

| User says | Action |
| --- | --- |
| Check-in / how was my day / brain dump / end of day | Read `Protocols/check-in-protocol.md` |
| New project / working on something | Read `Protocols/entity-protocol.md` → Project |
| New idea / thought / realization | Read `Protocols/entity-protocol.md` → Idea |
| Met someone / talked to someone | Read `Protocols/entity-protocol.md` → Person |
| Task / reminder / need to do | Read `Protocols/entity-protocol.md` → Task |
| Something I learned / read / figured out | Read `Protocols/entity-protocol.md` → Learning |
| What am I working on / status | Read `.second-brain/Memory/hot-memory.md` → summarize |
| What should I focus on | Use hot-memory.md context → advise on tasks and projects |

## Bundled scripts

| Script | Purpose |
| --- | --- |
| `scripts/check_cli.py` | Verify obsidian-cli is reachable and vault is accessible |
| `scripts/update_connected.py` | Safely append paths to a file's `connected:` YAML array |

Run `check_cli.py` at session start. Use `update_connected.py` for all `connected:` updates — never use `property:set` for arrays.

## Protocol files (load only when needed)

| File | Load when |
| --- | --- |
| `Protocols/setup-protocol.md` | `setup_complete: false` |
| `Protocols/check-in-protocol.md` | User initiates a check-in |
| `Protocols/entity-protocol.md` | Creating or updating any entity |
| `Protocols/linking-protocol.md` | Writing or updating any vault file |

Never load all protocol files at once.

## Two file locations — never mix them

| Location | What lives here |
| --- | --- |
| `.second-brain/` | config.md, Memory/ — skill operational files, NOT in vault |
| `vault_path` (from config.md) | All content: Work/, People/, Log/, Notes/, Tasks/, Inbox/, Archive/ |

Skill files (config, hot-memory, system-state) → use Write/Read/Edit tools directly.
Vault content → always use obsidian-cli.

## Entity quick reference

| Entity | Vault path | Notes |
| --- | --- | --- |
| Project | `Work/Projects/[name].md` | — |
| Idea | `Work/Ideas/[name].md` | — |
| Person | `People/[firstname-lastname].md` | — |
| Task | `Tasks/tasks-inbox.md` | Append only, not a new file |
| Learning | `Notes/Learnings/[topic].md` | — |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | Created once per check-in |

## Critical rules

- Nothing gets deleted — archive instead
- Every vault file gets YAML frontmatter + at least one `[[link]]`
- One idea per note — atomize brain dumps
- Load files surgically — never all at once
- Always forward slashes in paths
- `connected:` arrays → always use `scripts/update_connected.py` (never `property:set`)
- hot-memory.md stays under 800 tokens

## Memory loading order

1. `.second-brain/config.md` — always first
2. `.second-brain/Memory/hot-memory.md` — every session
3. `.second-brain/Memory/system-state.md` — every session
4. Individual vault files — only when user asks about something specific
