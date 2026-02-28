# Linking Protocol

Governs how every file in the vault gets YAML frontmatter and
Obsidian `[[links]]`. Read this before writing or updating any file.

---

## Core Rules

- Every file gets YAML frontmatter — no exceptions
- Every file gets at least one `[[link]]` — no orphan notes
- Links go in BOTH the frontmatter `connected` field AND the file body
- Always use forward slashes in file paths
- Never use absolute paths — always relative from vault root
- Link to what exists — do not create placeholder links to files
  that don't exist yet

---

## Two Types of Links

### 1. Machine-readable — YAML frontmatter

Lives in the `connected` field. Used by Claude to traverse the graph
without loading full files. Format:
```yaml
connected:
  - Work/Projects/second-brain.md
  - People/jason.md
  - Log/Daily/2026-02-28.md
```

No display titles here. Just clean file paths.

### 2. Human-readable — file body

Lives inside the markdown content. Used by Obsidian's graph view
and for manual navigation. Format:
```markdown
[[folder/filename|Display Title]]
```

Examples:
```markdown
[[Work/Projects/second-brain|Second Brain Skill]]
[[People/jason|Jason]]
[[Log/Daily/2026-02-28|February 28]]
[[Work/Ideas/zettelkasten-approach|Zettelkasten Approach]]
```

Both types must exist in every file. They serve different purposes
and neither replaces the other.

---

## YAML Frontmatter — Full Spec

Every file starts with this block. Fields vary by node type.

### Base frontmatter (all node types)
```yaml
---
node_type: [see valid values below]
created: YYYY-MM-DD
status: [see valid values below]
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

### Valid node_type values
```
project       idea          person        task
log-entry     learning      moc           hot-memory
system-state  index         review        analysis
resource      reference
```

### Valid status values
```
active        archived      completed
idle          converted     inbox
```

### Extended frontmatter by node type

**Project:**
```yaml
---
node_type: project
created: YYYY-MM-DD
status: active
deadline: YYYY-MM-DD
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

**Idea:**
```yaml
---
node_type: idea
created: YYYY-MM-DD
status: active
maturity: seed
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

Optional field added on conversion to project:
```yaml
converted_to: Work/Projects/[project-name].md
```

**Person:**
```yaml
---
node_type: person
created: YYYY-MM-DD
status: active
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

**Learning:**
```yaml
---
node_type: learning
created: YYYY-MM-DD
status: active
source: [url, book, person, or context]
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

**Log entry:**
```yaml
---
node_type: log-entry
created: YYYY-MM-DD
status: active
connected: []
tags: []
---
```

Note: log entries do not have `last_modified` — they are immutable
after creation.

**MOC:**
```yaml
---
node_type: moc
created: YYYY-MM-DD
status: active
topic: [topic name]
connected: []
tags: []
last_modified: YYYY-MM-DD
---
```

---

## Linking Rules by Relationship Type

### New entity → daily log

Every new entity created during a check-in links back to
that day's log entry. Always. No exceptions.

In frontmatter:
```yaml
connected:
  - Log/Daily/YYYY-MM-DD.md
```

In body:
```markdown
[[Log/Daily/YYYY-MM-DD|YYYY-MM-DD]]
```

### Daily log → everything touched today

The daily log links forward to everything created or updated
during that check-in.

In frontmatter — list all files touched:
```yaml
connected:
  - Work/Projects/second-brain.md
  - Work/Ideas/new-idea.md
  - People/jason.md
```

In body — under `## Linked Updates`:
```markdown
## Linked Updates
- [[Work/Projects/second-brain|Second Brain Skill]] — progress update
- [[Work/Ideas/new-idea|New Idea Name]] — captured
- [[People/jason|Jason]] — mentioned in project context
```

### Idea → project (conversion)

When an idea becomes a project, both files link to each other.

In idea file frontmatter:
```yaml
status: converted
maturity: converted
converted_to: Work/Projects/[project-name].md
connected:
  - Work/Projects/[project-name].md
```

In idea file body:
```markdown
**Converted to:** [[Work/Projects/[project-name]|Project Name]]
```

In project file frontmatter:
```yaml
connected:
  - Work/Ideas/[idea-name].md
```

In project file body:
```markdown
**Spawned from:** [[Work/Ideas/[idea-name]|Original Idea]]
```

### Project → person

When a person is involved in a project, both files link
to each other.

In project body under `## People`:
```markdown
- [[People/jason|Jason]] — backend development
```

In person file under `## Connected To`:
```markdown
- [[Work/Projects/second-brain|Second Brain Skill]] — backend developer
```

### Project → strategy or vision

When a project serves a quarterly goal or long-term vision:

In project body under `## Vision`:
```markdown
Serves [[Strategy/quarterly-goals|Q1 Goals]] and connects to
[[Vision/long-term-vision|long-term vision]].
```

### Learning → project or idea

When a learning is relevant to active work:

In learning body under `## Connected To`:
```markdown
- [[Work/Projects/second-brain|Second Brain Skill]] — informs architecture
- [[Work/Ideas/zettelkasten|Zettelkasten Approach]] — directly related
```

### MOC → all cluster nodes

MOC files link to every node in their cluster.
Every cluster node links back to the MOC.

In MOC frontmatter — list all cluster nodes:
```yaml
connected:
  - Work/Ideas/idea-1.md
  - Work/Ideas/idea-2.md
  - Log/Daily/2026-02-28.md
```

In each cluster node — add MOC link:
```markdown
Part of [[folder/moc-name|MOC Title]]
```

---

## Link Quality Rules

### Minimum links per node type

| Node Type | Minimum links                                           |
| --------- | ------------------------------------------------------- |
| Project   | 3 (source idea + at least one person + strategy or log) |
| Idea      | 2 (source log + at least one related node)              |
| Person    | 1 (at least one project, idea, or log)                  |
| Learning  | 2 (source log + at least one project or idea)           |
| Daily log | 1 per entity touched that day                           |
| MOC       | All nodes in cluster                                    |
| Task      | 1 (source project, idea, or log)                        |

### No orphan notes

If a new file cannot meet its minimum link requirement,
do not save it yet. Ask:

> "I want to link [file] to something that already exists —
> what does this connect to in your current work?"

If user cannot answer, save with a single link to today's
daily log and flag as weakly connected in the index.

To check if a file has incoming links, search for its path in other vault files using Grep.

### Link display titles

Always use meaningful display titles. Never use the filename as
the display title if it is not human-readable.
```markdown
✓ [[Work/Projects/second-brain|Second Brain Skill]]
✗ [[Work/Projects/second-brain|second-brain]]
✗ [[Work/Projects/second-brain]]
```

### Do not create forward links

Never create a `[[link]]` to a file that does not exist yet.
If the target file doesn't exist, create it first or note the
intended connection in plain text until it exists.

---

## Updating Existing Links

When updating an existing file:

1. Add new connections to the `connected` field in frontmatter
2. Add new `[[links]]` in the body where contextually relevant
3. Update `last_modified` date in frontmatter
4. Never remove existing links — they are graph history
5. Never modify existing `[[links]]` — append new ones only

→ **How:** Read the full file, apply all changes in memory, Write back the complete file.
For `connected:` arrays — parse the existing list, append the new path(s), deduplicate, rewrite the frontmatter block.
For `last_modified` — update the value inline before writing back.
For body links — append new `[[link]]` lines under the relevant section.

Example of what the `connected:` array looks like before and after:
```yaml
# Before
connected:
  - Log/Daily/2026-02-01.md

# After update
connected:
  - Log/Daily/2026-02-01.md
  - Log/Daily/2026-02-28.md     ← appended
  - People/jason.md              ← appended
```

---

## Index Update After Linking *(Phase 2)*

> **MMVP note:** Skip this section until `Context-Docs/index.md`
> exists. For MMVP, link tracking is handled by the `connected`
> field in each file's frontmatter — no central index needed.

After writing any file, update `Context-Docs/index.md`:

1. Add new node to Node Registry if it's a new file
2. Increment link frequency for every node that gained
   a new incoming link today
3. Flag any node whose link count crosses
   `moc_suggestion_link_threshold` from config.md

High link frequency = high centrality = load first when
that topic comes up.

---

## Error Handling

| Problem                                              | Action                                                               |
| ---------------------------------------------------- | -------------------------------------------------------------------- |
| Target file doesn't exist                            | Create target file first, then link                                  |
| Ambiguous link target (two files could match)        | Ask user which one, or create a new distinct file                    |
| User refers to something with no clear existing node | Create the node first, then link                                     |
| File saved without minimum links                     | Flag in system-log.md as weakly connected — revisit next check-in    |
| Broken link detected in existing file                | Note in system-log.md — do not auto-fix without confirming with user |
