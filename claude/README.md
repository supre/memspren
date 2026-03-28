# MemSpren — Claude Skill

A [Claude](https://claude.ai/) skill that turns Claude into a thinking partner for managing a Zettelkasten-based second brain in Obsidian.

## What it does

You talk. MemSpren extracts entities, builds connections, and syncs everything to your Obsidian vault as linked atomic notes — automatically.

- **Brain dump → knowledge graph.** One messy paragraph becomes linked notes for people, projects, ideas, tasks, patterns, and learnings.
- **Three-layer memory.** Active memory (~2000 tokens) stays in context. Rotating write-only buffers capture everything during conversation. Batch sync pushes rich entities to Obsidian.
- **Smart merge.** Description-based deduplication prevents duplicate files. Optional git safety checkpoints before every modification.
- **Zero maintenance.** No manual linking, no tagging, no folder management. The skill handles all of it.

---

## Prerequisites

- **Obsidian** (any recent version) with an existing vault, or a folder you want to use as one
- **Claude** with Cowork mode, with your Obsidian vault selected as the working folder
- **Git** (optional) — for safety checkpoints before file modifications

---

## How it works — two locations

The skill keeps its operational files separate from your vault content:

| Location | What lives here |
| --- | --- |
| `.second-brain/` | `config.md`, `Memory/` — Claude's state files. Hidden from Obsidian by default (dot-prefix). |
| `vault_path/` | All note content: `Work/`, `People/`, `Log/`, etc. This is your Obsidian vault. |

If you select your vault as the Cowork folder, both locations are inside the same folder — that's fine. `.second-brain/` is still separate from the vault content and won't clutter Obsidian's graph.

---

## Installation

1. In Cowork, select your Obsidian vault folder (or a folder you want to use as one)
2. Load the `memspren.skill` file
3. Start a conversation — Claude will detect that setup hasn't been run and guide you through it automatically

---

## Setup

Setup runs once on first use (~2 minutes). Claude will ask:

1. **Vault path** — the full path to your Obsidian vault on your computer
2. **Check-in time** — when you want your daily check-in (e.g. "9pm", "after work")
3. **Vision and goals** — optional starting context; can be added later
4. **Sync schedule** — how often to auto-sync brain dumps to your vault (or manual only)

After setup, Claude creates the full vault folder structure, seed files, and its own `.second-brain/` config folder.

---

## How it works

### During conversation

You share brain dumps, check-ins, updates. The skill:

1. Responds using active memory (insights, goals, project state) for context
2. Appends detailed entries to a rotating sync buffer (write-only, zero token cost)
3. Updates insights/goals if significant shifts are detected

No Obsidian interaction happens during conversation.

### During sync

Triggered by saying "sync now", on a cron interval, or at the end of a check-in:

1. Reads the oldest sealed sync buffer
2. Batch creates/updates Obsidian entities with full YAML frontmatter and `[[wiki links]]`
3. Runs smart merge — scans for similar files before creating, git commits before modifying (if available)
4. Recalculates insights, goals, and hot-memory
5. Archives and cleans up the processed buffer

---

## How to use

### Daily check-in

Say anything like:
- `"Check in"`
- `"Let's do my daily check-in"`
- `"End of day recap"`

Claude will open the conversation, let you brain-dump your day, ask targeted follow-up questions, then capture everything to the sync buffer.

### Capture a project

Say: `"I'm working on [name]"` or `"New project: [description]"`

Claude asks for goals and a deadline, then captures it for sync to `Work/Projects/`.

### Capture an idea

Say: `"I had an idea about..."` or `"I want to capture this thought..."`

Claude captures an atomic idea for sync to `Work/Ideas/` and links it to the current context.

### Log a person

Say: `"I talked to [name] about..."` or `"I met [name] today"`

Claude creates or updates a person file at `People/` with an interaction log entry.

### Add a task

Say: `"I need to [task]"` or `"Remind me to [task]"`

Claude adds it to `Tasks/tasks-inbox.md` with inferred priority.

### Sync your vault

Say: `"Sync now"` or `"Push to obsidian"`

Claude reads sealed sync buffers and batch-creates/updates vault entities with full context, wiki links, and proper frontmatter.

### Query your vault

- `"What am I working on?"` — Claude reads active memory and summarises active projects
- `"What should I focus on tomorrow?"` — Claude checks goals and active projects
- `"What do I know about [person/project/idea]?"` — Claude loads and summarises that entity file

---

## Entity types

| Entity | Vault path | Description |
|---|---|---|
| Project | `Work/Projects/[name].md` | Deadline-driven work with goals and progress notes |
| Idea | `Work/Ideas/[name].md` | Atomic thoughts, seeds for future projects |
| Person | `People/[name].md` | Interaction logs, connections to projects |
| Task | `Tasks/tasks-inbox.md` | Unified inbox, appended not created |
| Learning | `Notes/Learnings/[topic].md` | Things learned, connected to active work |
| Pattern | `Notes/Patterns/[name].md` | Recurring behavioral themes with evidence |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | One note per day, hub of all entities |

---

## Vault structure

```
[vault_path]/
├── Vision/          — values, long-term vision, guiding principles
├── Strategy/        — quarterly goals and active strategies
├── Work/
│   ├── Projects/    — deadline-driven work
│   └── Ideas/       — lightweight captures, no pressure
├── People/          — everyone you work with, linked to projects
├── Tasks/           — unified task inbox (tasks-inbox.md)
├── Log/Daily/       — one note per check-in day
├── Notes/
│   ├── Learnings/   — things learned, connected to work
│   └── Patterns/    — recurring behavioral themes
├── Inbox/           — unsorted catch-all
├── Logs/            — system logs
└── Archive/         — nothing ever deleted, everything archived here

.second-brain/       — skill state (hidden from Obsidian)
├── config.md        — vault path, check-in time, sync settings
└── Memory/
    ├── insights.md          — user patterns, energy, mindset (~700 tokens)
    ├── goals.md             — priorities, weekly/quarterly goals (~500 tokens)
    ├── hot-memory.md        — active project/task state (~500 tokens)
    ├── system-state.md      — config flags, last check-in/sync timestamps
    ├── sync-buffer-active.txt  — pointer to current active buffer ID
    ├── sync-buffer-001.md   — rotating sync buffer (write-only during conversation)
    └── sync-archive/        — archived buffers after sync
```

---

## Key design decisions

- **Token efficiency.** Active memory stays under 2000 tokens total. Buffers are never read during conversation.
- **Rotating buffers.** Each buffer is sealed at 1500 words, so each sync processes bounded data. Prevents context window overflow on heavy days.
- **Native file tools.** All vault writes go through Claude's Read/Write/Edit tools — no external CLI or plugins required.
- **Git safety (optional).** If git is available, every file modification is preceded by a git commit. Users can always `git diff` or `git revert`.
- **Description-based merge.** Every entity has a `description` frontmatter field used to detect duplicates before creating new files.
- **Nothing gets deleted.** Completed projects, old ideas, past tasks — everything is archived, never removed.

---

## Troubleshooting

**Setup runs again unexpectedly** — Check `.memspren-config` at workspace root and `.second-brain/config.md` both exist with `setup_complete: true`.

**Claude can't find vault files** — Confirm `vault_path` in `.second-brain/config.md` matches your actual vault location and that the vault folder is selected in Cowork.

**Memory not persisting between sessions** — Make sure the vault folder is selected in Cowork before starting a session. `.second-brain/` must be inside the mounted folder.

**Sync not running automatically** — Cron jobs are session-scoped and must be re-created each session. Check that the session start flow loaded config.md and re-created cron jobs. Say "sync now" to trigger manually.

**Reset setup** — Set `setup_complete: false` in `.memspren-config` and `.second-brain/config.md`, then Claude will run setup again on the next session.
