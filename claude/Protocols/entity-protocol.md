# Entity Protocol

Governs creation and updating of all entities in the vault.
Read `Protocols/linking-protocol.md` before writing any file.

All file paths are relative to `vault_path` stored in config.md.
Use the **Write** tool to create files, **Read** to load them,
**Edit** to update frontmatter properties, and append new content
by reading the file and writing back the full updated content.

---

## Core Rules

- Always confirm before creating a new entity (except tasks)
- Never delete existing content — always append
- Always check if entity already exists before creating
- Every entity gets YAML frontmatter and at least one `[[link]]`
- One concept per file — atomize

---

## Entity Existence Check

Before creating any entity, check whether it already exists:

```
MMVP: Check if the file already exists at its expected path
      (e.g. People/jason.md, Work/Projects/second-brain.md)

Phase 2: Search Context-Docs/index.md Node Registry for a match
```

If a match is found → load the existing file → append, do not create.
If no match → confirm with user → create new file.

Confirmation phrasing (keep it light, one line):

> "I don't have a file for [name/topic] yet — want me to create one?"

If user confirms → create.
If user says no → capture inline in daily log only.

---

## Entities

### Project

**Folder:** `Work/Projects/[project-name].md`
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

→ **Create:** Write the filled template to `{vault_path}/Work/Projects/<project-name>.md`

**When updating:**
- Read the file
- Append a new `### [TODAY]` section under `## Progress Notes`
- Update `last_modified` in frontmatter (Edit tool or full rewrite)
- Add the log entry path to the `connected:` array in frontmatter
- Write the updated file back

**Idle check:** If `last_modified` is older than
`project_idle_threshold_days` in config.md, flag in
next check-in synthesis.

---

### Idea

**Folder:** `Work/Ideas/[idea-name].md`
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

→ **Create:** Write the filled template to `{vault_path}/Work/Ideas/<idea-name>.md`

**When updating:**
- Read the file
- Append a new `### [TODAY]` section under `## Notes Log`
- Update `last_modified` in frontmatter
- Write the updated file back

**Maturity values:** `seed` → `developing` → `ready` → `converted`

Update maturity in frontmatter as the idea grows (use Edit tool).

When converting to project:
1. Update `status: converted`, `maturity: converted`, add `converted_to: Work/Projects/<project-name>.md` in frontmatter
2. Create new project file with `[[link]]` back to this idea
3. Do not move or delete idea file

---

### Person

**Folder:** `People/[firstname-lastname].md`
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

→ **Create:** Write the filled template to `{vault_path}/People/<firstname-lastname>.md`

**When updating — append to Interaction Log only:**
- Read the file
- Append a new `### [TODAY]` section under `## Interaction Log`
- Update `last_modified` in frontmatter
- Add the log entry path to the `connected:` array
- Write the updated file back

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

→ **Add task:** Read `{vault_path}/Tasks/tasks-inbox.md`, append the new task under `## Active Tasks`, write back.

**Completing a task:**
- Read tasks-inbox.md
- Change `- [ ]` to `- [x]` on the matching line
- Add `completed: [TODAY]` beneath it
- Write the file back

**Blocked task:**
- Read tasks-inbox.md
- Add `status: blocked` and `blocked_reason: [why]` beneath the task line
- Write back
- Flag in hot-memory if blocking an active project

> **Phase 2:** Completed tasks older than `task_archive_after_days`
> in config.md are moved to `Archive/Tasks/` by the daily sync
> protocol. For MMVP, completed tasks stay in tasks-inbox.md.

---

### Learning

**Folder:** `Notes/Learnings/[learning-topic].md`
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

→ **Create:** Write the filled template to `{vault_path}/Notes/Learnings/<learning-topic>.md`

**When updating:**
- Read the file
- Append a new `### [TODAY]` section under `## Notes Log`
- Update `last_modified` in frontmatter
- Write the updated file back

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

→ **Create:** Write the filled template to `{vault_path}/Log/Daily/[TODAY].md`

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

**When updating:**
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
| Ambiguous entity type                        | Default to Idea — easier to promote than demote                 |
| User mentions someone with only a first name | Create file as `People/[firstname].md` — note full name unknown |
| Project mentioned with no clear goal         | Create with `deadline: TBD` — flag in synthesis to clarify      |
| Duplicate topic detected                     | Load existing file — append, do not create second file          |
| User declines confirmation                   | Capture inline in daily log only — no standalone file           |
