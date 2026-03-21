# Entity Protocol

Governs creation and updating of all entities in the vault.
Read `Protocols/linking-protocol.md` before writing any file.

All file paths are relative to `vault_path` stored in config.md.
All vault file operations use obsidian-cli (create, read, append, property updates).

## Sync Mode Awareness

Check `sync_mode` in `.second-brain/config.md`:

- **`sync_mode: batch`** (default) — This protocol is ONLY executed during sync
  (triggered by `Protocols/sync-protocol.md`). During conversation, entities are
  extracted and written to `sync-buffer.md` instead. Do NOT use obsidian-cli
  during conversation.

- **`sync_mode: immediate`** (legacy) — Entities are created/updated immediately
  during conversation using obsidian-cli as described below.

---

## Core Rules

- **Every file MUST have a `description` field in frontmatter** — one-line summary of what the file is about. This is the search key for finding similar files and preventing duplicates.
- Always confirm before creating a new entity (except tasks)
- Never delete existing content — always append
- Always check if entity already exists before creating
- Every entity gets YAML frontmatter and at least one `[[link]]`
- One concept per file — atomize
- Use obsidian-cli for all vault operations
- **File naming:** Convert user input to readable title case (e.g., "My Project" not "my-project", "John Smith" not "john-smith")

---

## Entity Existence Check

Before creating any entity, check whether it already exists:

**Use obsidian-cli search:**
```bash
obsidian vault="[vault_name]" search query="[entity name]"
```

Or **read** the expected path directly:
```bash
obsidian vault="[vault_name]" read path="Work/Projects/[Project Name].md"
```

**Note:** Always use readable title case for file names (not snake_case).

If a match is found → load the existing file → append, do not create.
If no match → confirm with user → create new file.

Confirmation phrasing (keep it light, one line):

> "I don't have a file for [name/topic] yet — want me to create one?"

If user confirms → create.
If user says no → capture inline in daily log only.

---

## Entities

### Project

**Folder:** `Work/Projects/[Project Name].md` (use readable title case from user input)
**When to create:** User mentions active work with a goal and delivery intent.
**When to update:** Any mention of progress, blockers, tools, people, costs.

**Confirmation:**
> "Sounds like [name] is a real project — want me to set it up
> with goals and a deadline?"

**New file template:**
```markdown
---
node_type: project
created: [TODAY]
status: active
deadline: [date or TBD]
connected:
  - [source idea if converted]
  - [people involved]
  - [strategy it serves]
tags: []
last_modified: [TODAY]
---

# [Project Name]

## Vision
[Why this project matters — link to Vision or Strategy if relevant]
[[Strategy/quarterly-goals|Quarterly Goals]]

## Objectives
- [ ] [Specific goal with deadline]

## Progress Notes

### [TODAY]
[First progress note]

## Resources and Tools
| Tool | Cost | Notes |
| ---- | ---- | ----- |

## People
- [[People/[name]|Name]] — [role]

## Linked Ideas
- [[Work/Ideas/[idea]|Idea name]]

## Open Questions
```

→ **Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path="Work/Projects/[Project Name].md" \
  content="---\nnode_type: project\ncreated: [TODAY]\nstatus: active\ndeadline: [date]\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# [Project Name]\n\n## Vision\n[content]\n\n## Objectives\n- [ ] [goal]\n\n## Progress Notes\n\n### [TODAY]\n[note]\n\n## Resources and Tools\n\n## People\n\n## Linked Ideas\n\n## Open Questions"
```

**Note:** Replace `[Project Name]` with the user's input in readable title case. Example: "Marketing Campaign 2026" not "marketing-campaign-2026".

**When updating:**
- **Read** the file using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" read path="Work/Projects/[Project Name].md"
  ```
- Append a new `### [TODAY]` section under `## Progress Notes`
- Update `last_modified` in frontmatter
- Add the log entry path to the `connected:` array:
  ```bash
  python scripts/update_connected.py \
    --vault "[vault_name]" \
    --file "Work/Projects/[Project Name].md" \
    --add "Log/Daily/YYYY-MM-DD.md"
  ```
- **Write** the updated file back using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" create \
    path="Work/Projects/[Project Name].md" \
    content="[full updated content]" \
    overwrite
  ```

**Idle check:** If `last_modified` is older than
`project_idle_threshold_days` in config.md, flag in
next check-in synthesis.

---

### Idea

**Folder:** `Work/Ideas/[Idea Name].md` (use readable title case from user input)
**When to create:** User surfaces a new thought, concept, or possibility
that isn't a project yet.
**When to update:** User adds context, connects it to something, or
develops it further.

**Confirmation:**
> "Want me to capture [idea] as an idea file?"

**New file template:**
```markdown
---
node_type: idea
created: [TODAY]
status: active
maturity: seed
connected:
  - [related ideas]
  - [related projects]
  - [source log entry]
tags: []
last_modified: [TODAY]
---

# [Idea Name]

## Core Thought
[One or two sentences — the atomic idea]

## Why It Matters
[Why this is interesting or relevant]

## Connections
- [[Log/Daily/[date]|Captured from]]
- [[Work/Projects/[project]|Related project]]

## Open Questions
[What needs to be figured out before this becomes a project]

## Notes Log

### [TODAY]
[Initial capture]
```

→ **Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path="Work/Ideas/[Idea Name].md" \
  content="---\nnode_type: idea\ncreated: [TODAY]\nstatus: active\nmaturity: seed\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# [Idea Name]\n\n## Core Thought\n[content]\n\n## Why It Matters\n[content]\n\n## Connections\n\n## Open Questions\n\n## Notes Log\n\n### [TODAY]\n[initial capture]"
```

**Note:** Replace `[Idea Name]` with the user's input in readable title case. Example: "Podcast Interview Series" not "podcast-interview-series".

**When updating:**
- **Read** the file
- Append a new `### [TODAY]` section under `## Notes Log`
- Update `last_modified` in frontmatter
- **Write** the updated file back with overwrite

**Maturity values:** `seed` → `developing` → `ready` → `converted`

Update maturity in frontmatter as the idea grows using:
```bash
obsidian vault="[vault_name]" property:set \
  path="Work/Ideas/[Idea Name].md" \
  property=maturity \
  value=developing
```

When converting to project:
1. Update maturity and status:
   ```bash
   obsidian vault="[vault_name]" property:set \
     path="Work/Ideas/[Idea Name].md" \
     property=status \
     value=converted
   obsidian vault="[vault_name]" property:set \
     path="Work/Ideas/[Idea Name].md" \
     property=converted_to \
     value="Work/Projects/[Project Name].md"
   ```
2. Create new project file with `[[link]]` back to this idea
3. Do not move or delete idea file

---

### Person

**Folder:** `People/[First Name Last Name].md` (use readable title case from user input)
**When to create:** User mentions someone by name in a meaningful context —
worked with them, talked to them, they influenced something.
**When to update:** Any new interaction, connection to a project, or
new context about them.

**Confirmation:**
> "I don't have anyone called [name] yet — want me to create
> a file for them?"

**New file template:**
```markdown
---
node_type: person
created: [TODAY]
status: active
connected:
  - [projects they're involved in]
  - [ideas they influenced]
  - [log entries they appear in]
tags: []
last_modified: [TODAY]
---

# [Full Name]

## Who They Are
[Brief description — role, how user knows them, context]

## Connected To
- [[Work/Projects/[project]|Project name]] — [their role]
- [[Work/Ideas/[idea]|Idea name]] — [how they're connected]

## Interaction Log

### [TODAY]
[What happened, what was discussed, what they contributed]

## Notes
[Anything else worth knowing]
```

→ **Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path="People/[First Name Last Name].md" \
  content="---\nnode_type: person\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# [Full Name]\n\n## Who They Are\n[content]\n\n## Connected To\n\n## Interaction Log\n\n### [TODAY]\n[interaction note]\n\n## Notes"
```

**Note:** Replace `[First Name Last Name]` with the actual name in readable format. Example: "Sarah Johnson" not "sarah-johnson".

**When updating — append to Interaction Log only:**
- **Read** the file
- Append a new `### [TODAY]` section under `## Interaction Log`:
  ```bash
  obsidian vault="[vault_name]" append \
    path="People/[First Name Last Name].md" \
    content="\n### [TODAY]\n[interaction note]"
  ```
- Update `last_modified` in frontmatter
- Add the log entry path to the `connected:` array using helper script
- **Write** the updated file back

Never overwrite existing interaction entries.

---

### Task

**Folder:** `Tasks/tasks-inbox.md`
**When to create:** User mentions something they need to do, finish,
follow up on, or remember.
**When to update:** Status changes — completed, blocked, reprioritized.

Tasks live in `tasks-inbox.md` — not individual files.
No confirmation needed for tasks. Add immediately.

**New task format:**
```
- [ ] [Task description]
  priority: high | medium | low
  due: [date or blank]
  tags: #project | #idea | #life | #strategy
  connected: [[Work/Projects/[name]|Project]]
  created: [TODAY]
```

→ **Add task using obsidian-cli append:**
```bash
obsidian vault="[vault_name]" append \
  path=Tasks/tasks-inbox.md \
  content="\n- [ ] [Task description]\n  priority: high | medium | low\n  due: [date]\n  tags: #project\n  created: [TODAY]"
```

**Completing a task:**
- **Read** tasks-inbox.md using obsidian-cli
- Change `- [ ]` to `- [x]` on the matching line
- Add `completed: [TODAY]` beneath it
- **Write** the file back with overwrite

**Blocked task:**
- **Append** status info:
  ```bash
  obsidian vault="[vault_name]" append \
    path=Tasks/tasks-inbox.md \
    content="\n  status: blocked\n  blocked_reason: [why]"
  ```
- Flag in hot-memory if blocking an active project

> **Phase 2:** Completed tasks older than `task_archive_after_days`
> in config.md are moved to `Archive/Tasks/` by the daily sync
> protocol. For MMVP, completed tasks stay in tasks-inbox.md.

---

### Learning

**Folder:** `Notes/Learnings/[Learning Topic].md` (use readable title case from user input)
**When to create:** User shares something they learned, read, watched,
or understood for the first time.
**When to update:** User adds more to the same topic or connects it
to something new.

**Confirmation:**
> "Want me to capture that as a learning note?"

**New file template:**
```markdown
---
node_type: learning
created: [TODAY]
status: active
source: [where it came from — article, conversation, book, etc.]
connected:
  - [related projects]
  - [related ideas]
  - [log entry it came from]
tags: []
last_modified: [TODAY]
---

# [Learning Topic]

## The Core Insight
[One or two sentences — what was actually learned]

## Why It Matters
[How this connects to current work, goals, or thinking]

## Source
[Title, URL, person, or context]

## Connected To
- [[Work/Projects/[project]|Project]]
- [[Work/Ideas/[idea]|Idea]]

## Notes Log

### [TODAY]
[Full capture of the learning]
```

→ **Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path="Notes/Learnings/[Learning Topic].md" \
  content="---\nnode_type: learning\ncreated: [TODAY]\nstatus: active\nsource: [source]\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# [Learning Topic]\n\n## The Core Insight\n[content]\n\n## Why It Matters\n[content]\n\n## Source\n[source]\n\n## Connected To\n\n## Notes Log\n\n### [TODAY]\n[full capture]"
```

**Note:** Replace `[Learning Topic]` with the user's input in readable title case. Example: "Machine Learning Fundamentals" not "machine-learning-fundamentals".

**When updating:**
- **Read** the file:
  ```bash
  obsidian vault="[vault_name]" read path="Notes/Learnings/[Learning Topic].md"
  ```
- Append a new `### [TODAY]` section under `## Notes Log`
- Update `last_modified` in frontmatter
- **Write** the file back:
  ```bash
  obsidian vault="[vault_name]" create \
    path="Notes/Learnings/[Learning Topic].md" \
    content="[full updated content]" \
    overwrite
  ```

---

### Daily Log

**Folder:** `Log/Daily/YYYY-MM-DD.md`
**When to create:** Once per check-in. Always. No confirmation needed.
**When to update:** Never updated after creation — each day is its own
atomic file.

**New file template:**
```markdown
---
node_type: log-entry
created: [TODAY]
status: active
connected:
  - [project files updated today]
  - [idea files created today]
  - [people files updated today]
tags: []
---

# [YYYY-MM-DD]

## What Happened
[Natural prose — what the user did, worked on, experienced]

## Energy and Focus
[How they felt — inferred from tone if not stated]

## Open Threads
[Unresolved items, pending decisions, things to follow up]

## Reflections
[Journaling responses if journaling is enabled — leave blank otherwise]

## Linked Updates
[List of files updated during this check-in with [[links]]]
```

→ **Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path=Log/Daily/YYYY-MM-DD.md \
  content="---\nnode_type: log-entry\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\n---\n\n# [TODAY]\n\n## What Happened\n[content]\n\n## Energy and Focus\n[content]\n\n## Open Threads\n[content]\n\n## Reflections\n\n## Linked Updates"
```

This file is the hub of the day. Every other entity created
or updated during the check-in gets a `[[link]]` back here.

---

### MOC — Map of Content *(Phase 2)*

> **MMVP note:** MOCs are suggested automatically when a node crosses
> `moc_suggestion_link_threshold` in config.md (default: 8 connections).
> For MMVP, skip MOC creation — it requires the index to track link
> frequency. Introduce in Phase 2 with Context-Docs/index.md.

**Folder:** anywhere relevant to the topic
**When to create:** When `moc_suggestion_link_threshold` in config.md
is crossed — 8+ notes connecting to the same topic or concept.
**When to update:** As new notes join the cluster.

**Confirmation:**
> "You have [X] notes connected around [topic] — want me to
> create a Map of Content to synthesize them?"

**New file template:**
```markdown
---
node_type: moc
created: [TODAY]
status: active
topic: [topic name]
connected:
  - [all notes in this cluster]
tags: []
last_modified: [TODAY]
---

# [Topic] — Map of Content

## What This Is
[One paragraph — what this cluster of notes is about and
why it emerged]

## The Nodes

### Core ideas
- [[Work/Ideas/[idea]|Idea]] — [one line summary]

### Related projects
- [[Work/Projects/[project]|Project]] — [one line summary]

### Log entries where this came up
- [[Log/Daily/[date]|Date]] — [context]

### Learnings
- [[Notes/Learnings/[topic]|Learning]] — [one line summary]

## Synthesis
[What patterns emerge when you look at all these notes together?
What's the insight that didn't exist in any single note?]

## Open Questions
[What's missing from this cluster? What bridging idea doesn't
exist yet?]

## Next Action
[Does this cluster want to become a project? A strategy? A vision
update? Or just sit here as a reference?]
```

**When updating using obsidian-cli append:**
Add new connected notes to the node list.
Update synthesis if new patterns emerge.
Never remove existing nodes — they are graph history.

---

## Index Update *(Phase 2)*

> **MMVP note:** Skip until `Context-Docs/index.md` exists.
> Entity files are self-describing via their YAML frontmatter
> and `connected` fields — no central index needed for MMVP.

After creating or updating any entity, update
`Context-Docs/index.md`:
```markdown
## Node Registry

| File                          | Node Type | Status | Created    | Key Connections        |
| ----------------------------- | --------- | ------ | ---------- | ---------------------- |
| Work/Projects/second-brain.md | project   | active | 2026-02-28 | jason, quarterly-goals |
```

Update link frequency count for any node that gained
new `[[links]]` today.

---

## Error Handling

| Problem                                      | Action                                                          |
| -------------------------------------------- | --------------------------------------------------------------- |
| obsidian-cli returns error                   | Check if Obsidian is running. If not: "Obsidian needs to be open for me to update your vault." |
| Ambiguous entity type                        | Default to Idea — easier to promote than demote                 |
| User mentions someone with only a first name | Create file as `People/[firstname].md` — note full name unknown |
| Project mentioned with no clear goal         | Create with `deadline: TBD` — flag in synthesis to clarify      |
| Duplicate topic detected                     | Load existing file with obsidian-cli read — append, do not create second file |
| User declines confirmation                   | Capture inline in daily log only — no standalone file           |
