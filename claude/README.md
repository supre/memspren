# Managing Second Brain

A Zettelkasten-based personal knowledge management skill for Claude. It turns Claude into a thinking partner that runs structured daily check-ins, captures projects, ideas, people, and tasks as linked atomic notes in your Obsidian vault, and maintains persistent memory across sessions.

Every entity is a node. Every connection is a `[[link]]`. Claude reads and writes vault files directly using its file tools — no CLI or plugins required.

---

## Prerequisites

- **Obsidian** (any recent version) with an existing vault, or a folder you want to use as one
- **Claude** with Cowork mode, with your Obsidian vault selected as the working folder

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
2. Load the `managing-second-brain.skill` file
3. Start a conversation — Claude will detect that setup hasn't been run and guide you through it automatically

---

## Setup

Setup runs once on first use (~2 minutes). Claude will ask:

1. **Vault path** — the full path to your Obsidian vault on your computer (e.g. `/Users/yourname/Documents/My Second Brain`). If you've already selected your vault as the Cowork folder, Claude will confirm this automatically.
2. **Check-in time** — when you want your daily check-in (e.g. "9pm", "after work")
3. **Vision and goals** — optional starting context; can be added later

After setup, Claude creates the full vault folder structure, seed files, and its own `.second-brain/` config folder.

---

## How to use

### Daily check-in

Say anything like:
- `"Check in"`
- `"Let's do my daily check-in"`
- `"End of day recap"`

Claude will open the conversation, let you brain-dump your day, ask targeted follow-up questions, then create or update your vault notes automatically.

### Capture a project

Say: `"I'm working on [name]"` or `"New project: [description]"`

Claude asks for goals and a deadline, then creates a project file at `Work/Projects/`.

### Capture an idea

Say: `"I had an idea about..."` or `"I want to capture this thought..."`

Claude creates an atomic idea file at `Work/Ideas/` and links it to the current context.

### Log a person

Say: `"I talked to [name] about..."` or `"I met [name] today"`

Claude creates or updates a person file at `People/` with an interaction log entry.

### Add a task

Say: `"I need to [task]"` or `"Remind me to [task]"`

Claude adds it to `Tasks/tasks-inbox.md` with inferred priority.

### Query your vault

- `"What am I working on?"` — Claude reads hot-memory and summarises active projects
- `"What should I focus on tomorrow?"` — Claude checks your task inbox and active projects
- `"What do I know about [person/project/idea]?"` — Claude loads and summarises that entity file

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
├── Notes/Learnings/ — things learned, connected to work
├── Inbox/           — unsorted catch-all
└── Archive/         — nothing ever deleted, everything archived here

.second-brain/       — skill state (hidden from Obsidian)
├── config.md        — vault path, check-in time, setup status
└── Memory/
    ├── hot-memory.md     — active context Claude loads every session
    └── system-state.md   — protocol flags, last check-in date
```

---

## Troubleshooting

**Setup runs again unexpectedly** — Check `.second-brain/config.md` exists and `setup_complete: true` is set.

**Claude can't find vault files** — Confirm `vault_path` in `.second-brain/config.md` matches your actual vault location and that the vault folder is selected in Cowork.

**Memory not persisting between sessions** — Make sure the vault folder is selected in Cowork before starting a session. `.second-brain/` must be inside the mounted folder.

**Reset setup** — Set `setup_complete: false` in `.second-brain/config.md` and Claude will run setup again on the next session.
