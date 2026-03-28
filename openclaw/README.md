# MemSpren — OpenClaw Skill

An [OpenClaw](https://openclaw.ai/) skill that turns your AI assistant into a thinking partner for managing a Zettelkasten-based second brain in Obsidian.

## What it does

You talk. MemSpren extracts entities, builds connections, and syncs everything to your Obsidian vault as linked atomic notes — automatically.

- **Brain dump → knowledge graph.** One messy paragraph becomes linked notes for people, projects, ideas, tasks, and learnings.
- **Three-layer memory.** Active memory (~2000 tokens) stays in context. A write-only buffer captures everything during conversation. Batch sync pushes rich entities to Obsidian.
- **Smart merge.** Description-based deduplication prevents duplicate files. Git safety checkpoints before every modification.
- **Zero maintenance.** No manual linking, no tagging, no folder management. The skill handles all of it.

## Prerequisites

- [Obsidian](https://obsidian.md) installed with a vault created
- Obsidian CLI enabled: **Settings → General → Enable CLI** (requires 1.12.4+)
- CLI in PATH: `export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"` (macOS)
- [Git](https://git-scm.com/) installed
- [OpenClaw](https://openclaw.ai/) installed

## Setup

1. Copy this `openclaw/` folder to `~/.openclaw/skills/` (or `~/.openclaw/workspace/skills/`)
2. Restart OpenClaw to load the skill
3. Say "check in" or "brain dump" — OpenClaw will guide you through first-time setup (~2 min)

Setup creates the vault structure, initializes git, and configures sync settings.

## How it works

### During conversation

You share brain dumps, check-ins, updates. The skill:

1. Responds using active memory (insights, goals, project state) for context
2. Appends detailed entries to a sync buffer (write-only, zero token cost)
3. Updates insights/goals if significant shifts are detected

No Obsidian interaction happens during conversation.

### During sync

Triggered by saying "sync now", on a cron interval, or at the end of a check-in:

1. Reads the sync buffer
2. Batch creates/updates Obsidian entities with full YAML frontmatter and `[[wiki links]]`
3. Runs smart merge — scans for similar files before creating, git commits before modifying
4. Recalculates insights, goals, and hot-memory
5. Archives and clears the buffer

### Entity types

| Entity | Vault path | Description |
|---|---|---|
| Project | `Work/Projects/[name].md` | Deadline-driven work with goals and progress notes |
| Idea | `Work/Ideas/[name].md` | Atomic thoughts, seeds for future projects |
| Person | `People/[name].md` | Interaction logs, connections to projects |
| Task | `Tasks/tasks-inbox.md` | Unified inbox, appended not created |
| Learning | `Notes/Learnings/[topic].md` | Things learned, connected to active work |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | One note per day, hub of all entities |
| KT | `Work/KT/[topic].md` | Knowledge transfer structured summaries |

## File structure

```
openclaw/
├── SKILL.md                          # Skill definition (loaded by OpenClaw)
├── README.md                         # This file
├── Protocols/
│   ├── setup-protocol.md             # First-run vault initialization
│   ├── check-in-protocol.md          # Daily check-in flow
│   ├── entity-protocol.md            # Entity creation/update rules
│   ├── linking-protocol.md           # Frontmatter + wikilink spec
│   └── sync-protocol.md              # Lobster pipeline invocation + approval gate
└── scripts/
    ├── check_cli.py                  # Verify obsidian-cli + vault access
    ├── scan_descriptions.py          # Extract frontmatter for smart merge
    ├── git_commit.py                 # Safety checkpoint before modifications
    └── update_connected.py           # Append to connected: YAML arrays
```

## Vault structure (created during setup)

```
[vault]/
├── .second-brain/                    # Skill state (not vault content)
│   ├── config.md                     # Settings, sync config, custom protocols
│   └── Memory/
│       ├── insights.md               # User patterns, energy, mindset (~700 tokens)
│       ├── goals.md                  # Priorities, weekly/quarterly goals (~500 tokens)
│       ├── hot-memory.md             # Active project/task state (~500 tokens)
│       ├── system-state.md           # Config flags, last sync timestamp
│       ├── sync-buffer.md            # Brain dump log (write-only during conversation)
│       └── sync-archive/             # Archived buffers after sync
├── Vision/                           # Values, long-term vision
├── Strategy/                         # Quarterly goals, active strategies
├── Work/Projects/                    # Deadline-driven work
├── Work/Ideas/                       # Lightweight captures
├── Work/KT/                          # Knowledge transfer docs
├── People/                           # Contacts and interaction logs
├── Tasks/                            # Unified task inbox
├── Log/Daily/                        # One note per check-in day
├── Notes/Learnings/                  # Things learned
├── Notes/Patterns/                   # Observed behavioral patterns
├── Inbox/                            # Unsorted catch-all
└── Archive/                          # Nothing gets deleted
```

## Key design decisions

- **Token efficiency.** Active memory stays under 2000 tokens total. Buffer is never read during conversation.
- **Obsidian-cli only.** All vault writes go through obsidian-cli during sync — never direct filesystem writes for vault content.
- **Git safety.** Every file modification is preceded by a git commit. Users can always `git diff` or `git revert`.
- **Description-based merge.** Every entity has a `description` frontmatter field used to detect duplicates before creating new files.
- **Nothing gets deleted.** Completed projects, old ideas, past tasks — everything is archived, never removed.
