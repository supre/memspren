# Memspren

A Zettelkasten-based personal knowledge management ecosystem. Multiple integrations for managing your second brain across different platforms and tools.

**Core concept:** Every entity is a node. Every connection is a link. Your thinking partner maintains persistent context without manual effort.

---

## Plugins

### Claude (`claude/`)

A Claude skill that turns Claude into your thinking partner for daily check-ins, capturing projects, ideas, people, and tasks as linked atomic notes in your Obsidian vault.

- **No CLI required** — uses Claude's native file tools
- **Daily check-in workflow** — brain dump → targeted follow-up → entity creation
- **Persistent memory** — hot-memory and system-state files maintain context across sessions
- **Full Zettelkasten** — YAML frontmatter + Obsidian wikilinks keep your graph connected

[Read more →](./claude/README.md)

---

## Architecture

### Two-location design

Every plugin follows this pattern:

| Location                | What lives here                              |
| ----------------------- | -------------------------------------------- |
| **Skill/Plugin folder** | `config.md`, Memory/, operational files      |
| **Vault**               | All note content: Work/, People/, Log/, etc. |

This separation keeps your knowledge graph clean while giving the AI system predictable places to store state.

### Entity types

- **Projects** — deadline-driven work with goals and progress notes
- **Ideas** — atomic thoughts, underdeveloped concepts, seeds for future projects
- **People** — everyone you work with, interaction logs, connections to projects
- **Tasks** — unified inbox with priority and connections to projects/ideas
- **Learnings** — things you've learned, read, understood, connected to active work
- **Daily logs** — one note per check-in, hub of all entities touched that day

Every entity has YAML frontmatter (`node_type`, `status`, `connected`, `tags`) and at least one `[[link]]` — no orphan notes.

### Core protocols

All plugins implement:

- **Setup protocol** — one-time initialization of vault structure and config
- **Check-in protocol** — structured daily reviews
- **Entity protocol** — creation and update rules for each entity type
- **Linking protocol** — frontmatter + wikilink system

[See full protocols →](./claude/Protocols/)

---

## Getting started

1. Pick a plugin below that matches your workflow
2. Follow its setup instructions
3. Start capturing: projects, ideas, people, tasks, reflections

---

## Future plugins

- **Obsidian plugin** — native Obsidian interface for entity creation and queries
- **Slack integration** — capture ideas and tasks from Slack, sync to vault
- **Calendar sync** — link daily logs to calendar events
- **Web clipper** — capture learnings from web articles
- **CLI tool** — command-line interface for vault queries and updates

---

## Philosophy

This isn't just a storage system. The goal is **persistent context without manual effort**:

- Claude (or any plugin) reads your recent notes on every interaction
- You never have to re-explain yourself
- Your thinking is captured atomically, linked, and queryable
- Nothing gets deleted — everything gets archived
- Your vault is the source of truth, portable, and yours forever

---

## License

See [LICENSE](./LICENSE)
