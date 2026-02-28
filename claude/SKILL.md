---
name: managing-second-brain
description: >
  Manages a Zettelkasten-based second brain and personal knowledge graph in
  Obsidian. Use this skill whenever the user mentions their second brain,
  Obsidian vault, daily check-in, PKM, or when they share anything they want
  to capture: projects they're working on, ideas they had, people they talked
  to, tasks to track, reflections, or anything they don't want to forget.
  Trigger even if the user doesn't say "second brain" - any brain dump, daily
  recap, "I want to remember this", or "I had an idea" qualifies. Creates
  atomic linked notes with YAML frontmatter and wikilinks, and maintains
  persistent memory across sessions so the user never has to re-explain
  themselves.
---

# Managing Second Brain

Zettelkasten-powered knowledge graph in Obsidian. Every entity is a node.
Every connection is a `[[link]]`. Claude is the thinking partner — not just a
storage system. The core value is persistent context without manual effort.

## File locations

Two separate locations. Never mix them up.

| Location | What lives here | Path |
| --- | --- | --- |
| **Skill folder** | config.md, Memory/, operational files | `.second-brain/` in the mounted folder |
| **Vault** | All content: Work/, People/, Log/, etc. | `vault_path` from config.md |

The `.second-brain/` folder is at the root of the Cowork mounted folder.
It is hidden from Obsidian's graph by default (dot-prefix).
`vault_path` in config.md points to the user's Obsidian vault — this is
where all note content gets written.

If vault_path equals the mounted folder root, the vault and skill folder
are in the same place — that's fine. `.second-brain/` is still separate.

## Critical rules

- Nothing gets deleted — archive instead
- Every file gets YAML frontmatter and at least one `[[link]]`
- One idea per note — atomize brain dumps into discrete atomic notes
- Load files surgically — never all at once
- Always use forward slashes in file paths
- Skill files (config, Memory) → `.second-brain/`
- Vault content → `vault_path`

## Session start

```
Read .second-brain/config.md       ← always first
Load .second-brain/Memory/hot-memory.md if it exists
Load .second-brain/Memory/system-state.md if it exists
Check config.md → setup_complete?
        │
   ┌────┴────┐
  false     true
   │         │
   ▼         ▼
Read        Skip to
Protocols/  intent
setup-      detection
protocol.md
```

Neither Memory file exists on first run — that's expected.
Just read `.second-brain/config.md` and proceed to setup.

## Intent detection

| User says                              | Action                                                   |
| -------------------------------------- | -------------------------------------------------------- |
| Check-in / how was my day / brain dump | Read Protocols/check-in-protocol.md and follow its steps |
| New project / working on something     | Read Protocols/entity-protocol.md → Project              |
| New idea / thought / realization       | Read Protocols/entity-protocol.md → Idea                 |
| Met someone / talked to someone        | Read Protocols/entity-protocol.md → Person               |
| Task / reminder / need to do           | Read Protocols/entity-protocol.md → Task                 |
| What am I working on / status          | Read .second-brain/Memory/hot-memory.md → summarize      |
| What should I focus on                 | Use hot-memory.md context → advise on tasks and projects |

## Entity creation (quick reference)

| Entity    | Folder               | Filename pattern       |
| --------- | -------------------- | ---------------------- |
| Project   | Work/Projects/       | project-name.md        |
| Idea      | Work/Ideas/          | idea-name.md           |
| Person    | People/              | firstname-lastname.md  |
| Task      | Tasks/tasks-inbox.md | append, not a new file |
| Learning  | Notes/Learnings/     | learning-topic.md      |
| Daily log | Log/Daily/           | YYYY-MM-DD.md          |

All paths above are relative to `vault_path`.
Every file: YAML frontmatter with `node_type` + `connected` + at least
one `[[link]]` in the body. No orphan notes.

Full templates, confirmation prompts, and update rules:
→ `Protocols/entity-protocol.md`
→ `Protocols/linking-protocol.md`

## Memory loading rules

Load in order. Stop when context is sufficient.

1. `.second-brain/config.md` — vault path and setup status, always first
2. `.second-brain/Memory/hot-memory.md` — current week context, every session
3. `.second-brain/Memory/system-state.md` — active protocols and flags, every session
4. Individual vault entity files — only when user asks about something specific

## Reference files

| File                           | Load when                       |
| ------------------------------ | ------------------------------- |
| `Protocols/setup-protocol.md`  | setup_complete is false         |
| `Protocols/check-in-protocol.md` | User initiates a check-in     |
| `Protocols/entity-protocol.md` | Creating or updating any entity |
| `Protocols/linking-protocol.md` | Writing or updating any file   |

## Vault structure (content — lives at vault_path)

```
Vision/        Strategy/      Work/Projects/    Work/Ideas/
People/        Tasks/         Log/Daily/        Notes/
Inbox/         Archive/
```

## Skill folder structure (operational — lives at .second-brain/)

```
.second-brain/
├── config.md
└── Memory/
    ├── hot-memory.md
    └── system-state.md
```

## What never happens

- Deleting any vault file (archive it instead)
- Saving a note without YAML frontmatter
- Saving a note without at least one `[[link]]`
- Loading all reference files in a single session
- Storing over ~800 tokens in hot-memory.md
- Windows-style backslash paths
- Writing config.md or Memory files into the vault content folders
