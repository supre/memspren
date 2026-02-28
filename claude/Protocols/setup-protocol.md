# Setup Protocol

Runs ONCE on first launch when `setup_complete: false` in config.md.
Never runs again unless manually reset.

> **MMVP note:** Steps 5 and 6 (journaling, lifestyle tracking) are Phase 2
> features. Skip them for a minimal first working version — the system works
> without them. Include them when building toward the full MVP.

---

## Checklist

Copy and track progress before starting:

```
- [ ] Step 1: Greet user
- [ ] Step 2: Vault location
- [ ] Step 3: Check-in time
- [ ] Step 4: Vision and goals
- [ ] Step 5: Journaling (Phase 2 — skip for MMVP)
- [ ] Step 6: Lifestyle tracking (Phase 2 — skip for MMVP)
- [ ] Step 7: Create files and structure
- [ ] Step 8: Guided tour
- [ ] Step 9: Mark setup complete
```

---

## Step 1: Greet user

Say:
> "Hey! I'm going to set up your second brain. Takes about 2 minutes.
> I'll ask a few questions then create everything. You can change
> any of this later — nothing is permanent."

---

## Step 2: Vault location

Ask:
> "What's the full path to your Obsidian vault on your computer?
> (e.g. `/Users/yourname/Documents/My Second Brain`)"

| Answer | Action |
|---|---|
| Provides path | Store as `vault_path` in config.md |
| Doesn't know | Ask: *"Is this folder your vault?"* — check for a `.obsidian/` subfolder to confirm. Use the current folder if confirmed. |
| No vault yet | Tell them: *"No problem — I'll create the vault structure in the folder you've selected."* Use the current mounted folder as vault_path. |

---

## Step 3: Check-in time

Ask:
> "What time works for your daily check-in? (e.g. 9pm, after work)"

Convert natural language to 24h format. Store as `check_in_time` in config.md.
Default if skipped: `21:00`

---

## Step 4: Vision and goals

Ask:
> "Do you have a long-term vision or goals you want me to know
> about from the start? Even rough notes are fine — or skip
> and add later."

| Answer | Action |
|---|---|
| Provides content | Write to `Vision/long-term-vision.md` with YAML frontmatter + `[[link]]` to `Vision/core-values.md` |
| Skips | Create empty `Vision/long-term-vision.md` with placeholder |

---

## Step 5: Journaling *(Phase 2 — skip for MMVP)*

Ask:
> "Do you want a daily journaling prompt during check-ins?"

| Answer | Action |
|---|---|
| No | Skip — do not create journaling protocol |
| Yes (default) | Create `Protocols/journaling-context.md` with default questions |
| Yes (custom) | Ask: *"What would you like to reflect on each day?"* → capture response → create `Protocols/journaling-context.md` from their input |

Default journaling questions:
- What were today's wins?
- What didn't work and why?
- What would you do differently?
- What are you grateful for?
- What's your intention for tomorrow?

---

## Step 6: Lifestyle tracking *(Phase 2 — skip for MMVP)*

Ask:
> "Do you want to track anything daily — health, habits,
> energy, sleep, anything like that?"

| Answer | Action |
|---|---|
| No | Skip — do not create any lifestyle protocol |
| Yes | Ask follow-up questions one at a time (see below) |

For each area they mention, ask ONE AT A TIME:
> "For [area] — what would you like to check in on?
> Specific metrics, or just a general feel?"

Create `Protocols/lifestyle-[area].md` per area using their answers.
Continue until user says they're done.

---

## Step 7: Create files and structure

**Two locations are used:**
- **Skill folder** → `.second-brain/` in the mounted folder root (always fixed)
- **Vault content** → `vault_path` (set in Step 2)

Create the `.second-brain/` directory first if it doesn't exist.

### Vault folders

Create at `vault_path`:

```
Vision/
Strategy/
Work/Projects/
Work/Ideas/
People/
Life/Lifestyle/
Tasks/
Inbox/
Log/Daily/
Log/Weekly/
Log/Analysis/
Notes/Learnings/
Notes/Resources/
Notes/Reference/
Archive/Vision/
Archive/Strategy/
Archive/Projects/
Archive/Ideas/
Archive/People/
Archive/Lifestyle/
Archive/Tasks/
Archive/Inbox/
Archive/Log/
Archive/Notes/
```

### Seed files

Create with YAML frontmatter and placeholder content:

```
Vision/core-values.md
Vision/long-term-vision.md
Vision/guiding-principles.md
Vision/life-philosophy.md
Strategy/quarterly-goals.md
Tasks/tasks-inbox.md
```

`Tasks/tasks-inbox.md` format:

```markdown
---
node_type: tasks-inbox
created: [TODAY]
status: active
---
# Tasks Inbox

## Active Tasks

## Completed (last 2 weeks)
```

### .second-brain/config.md

Write to `.second-brain/config.md` in the mounted folder:

```yaml
vault_path: "[from Step 2]"
check_in_time: "[from Step 3]"
project_idle_threshold_days: 7
task_archive_after_days: 14
log_retention_days: 90
moc_suggestion_link_threshold: 8
auto_archive_enabled: true
setup_complete: false
```

### .second-brain/Memory/hot-memory.md

```markdown
---
node_type: hot-memory
last_updated: [TODAY]
---
# Hot Memory

## Active Projects

## Immediate Tasks

## Patterns Flagged

## Active Protocols
[list protocols created in Steps 5–6]
```

### .second-brain/Memory/system-state.md

```markdown
---
node_type: system-state
setup_complete: false
last_updated: [TODAY]
---
# System State

## Setup
vault_path: [vault_path]
check_in_time: [check_in_time]

## Active Protocols
[only protocols created during setup]

## Behavioral Flags
journaling: [true/false]
lifestyle_tracking: [true/false]
auto_archive: true
moc_suggestions: true
```

### Context-Docs/index.md *(Phase 2 — create as stub for MMVP)*

```markdown
---
node_type: index
last_updated: [TODAY]
---
# Vault Index

## Node Registry

## Link Frequency
```

---

## Step 8: Guided tour

Say:
> "Your second brain is ready. Here's what I built:"

Walk through each area naturally:

| Folder | What it's for |
|---|---|
| `Vision/` | Your why — values, vision, principles |
| `Strategy/` | Quarterly goals and active strategies |
| `Work/Projects/` | Deadline-driven work with tasks |
| `Work/Ideas/` | Lightweight captures, no pressure |
| `People/` | Everyone you interact with, linked to your work |
| `Tasks/` | One unified inbox for all tasks |
| `Log/` | Daily notes, weekly reviews, analysis |
| `Notes/` | Learnings, resources, reference material |
| `Inbox/` | Catch-all for anything unsorted |
| `Archive/` | Nothing ever deleted — everything lives here |

If journaling enabled:
> "I'll ask your journaling questions during check-ins.
> Find them in `Protocols/journaling-context.md` — evolve them anytime."

If lifestyle tracking enabled:
> "I'll check in on [areas] during daily sessions.
> Each area has its own protocol file you can update whenever."

Close with:
> "To start, just say 'check in' or 'let's do my daily check-in'
> whenever you're ready."

---

## Step 9: Mark setup complete

Update `.second-brain/config.md`:

```yaml
setup_complete: true
```

Update `.second-brain/Memory/system-state.md` frontmatter:

```yaml
setup_complete: true
```

Log to `{vault_path}/Logs/system-log.md`:

```
[TIMESTAMP] SETUP COMPLETE
  vault_path: [path]
  check_in_time: [time]
  protocols_created: [list]
  folders_created: [count]
  seed_files_created: [count]
```

---

## Error handling

| Problem | Action |
|---|---|
| Vault path can't be created | Tell user, ask for different path — do not proceed |
| User skips all optional steps | Fine — create structure only, no protocol files |
| User wants to restart setup | Set `setup_complete: false` in `.second-brain/config.md` and `.second-brain/Memory/system-state.md`, then reload |
