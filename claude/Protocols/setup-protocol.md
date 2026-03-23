# Setup Protocol

Runs ONCE on first launch when `setup_complete: false` in config.md
(or when no `.memspren-config` exists at workspace root).
Never runs again unless manually reset.

> **MMVP note:** Steps 7 and 8 (journaling, lifestyle tracking) are Phase 2
> features. Skip them for a minimal first working version — the system works
> without them. Include them when building toward the full MVP.

---

## Checklist

Copy and track progress before starting:

```
- [ ] Step 1: Check prerequisites
- [ ] Step 2: Greet user
- [ ] Step 3: Vault location
- [ ] Step 4: Check-in time
- [ ] Step 5: Vision and goals
- [ ] Step 6: Sync schedule
- [ ] Step 7: Journaling (Phase 2 — skip for MMVP)
- [ ] Step 8: Lifestyle tracking (Phase 2 — skip for MMVP)
- [ ] Step 9: Create files and structure
- [ ] Step 10: Guided tour
- [ ] Step 11: Mark setup complete
```

---

## Step 1: Check prerequisites

### Git (optional)
Check if git is available:
```bash
git --version
```

If git is found:
> "Git is available — I'll use it to create safety checkpoints before modifying
> vault files. You can always `git diff` or `git revert` to undo any change."

If git is NOT found:
> "Git isn't available on this system. That's fine — everything still works,
> but I won't be able to create safety checkpoints before modifying files.
> If you'd like that safety net later, install git."

**Do NOT block setup on git.** It's a nice-to-have, not a requirement.

---

## Step 2: Greet user

Say:
> "Hey! I'm going to set up your second brain. Takes about 2 minutes.
> I'll ask a few questions then create everything. You can change
> any of this later — nothing is permanent."

---

## Step 3: Vault location

Ask:
> "What's the full path to your Obsidian vault on your computer?
> (e.g. `/Users/yourname/Documents/My Second Brain`)"

| Answer | Action |
|---|---|
| Provides path | Verify it exists and check for `.obsidian/` subfolder. Store as `vault_path`. |
| Doesn't know | Ask: *"Is this folder your vault?"* — check for a `.obsidian/` subfolder to confirm. Use the current folder if confirmed. |
| No vault yet | Tell them: *"No problem — I'll create the vault structure in the folder you've selected."* Use the current mounted folder as vault_path. |

**Create `.memspren-config` at workspace root** using the Write tool:
```yaml
vault_path: "[from user]"
setup_complete: false
```

---

## Step 4: Check-in time

Ask:
> "What time works for your daily check-in? (e.g. 9pm, after work)"

Convert natural language to 24h format. Store as `check_in_time` in config.md.
Default if skipped: `21:00`

---

## Step 5: Vision and goals

Ask:
> "Do you have a long-term vision or goals you want me to know
> about from the start? Even rough notes are fine — or skip
> and add later."

| Answer | Action |
|---|---|
| Provides content | Write to `Vision/long-term-vision.md` with YAML frontmatter + `[[link]]` to `Vision/core-values.md` |
| Skips | Create empty `Vision/long-term-vision.md` with placeholder |

---

## Step 6: Sync schedule

Explain to the user how vault synchronization works, then set up sync schedule.

Say:
> "Your brain dumps are captured in real-time but synced to Obsidian in batches
> — this keeps things fast and token-efficient. I can set up automatic syncs
> throughout the day. How many times per day would you like your vault synced?
> (e.g. '3 times — noon, 5pm, 9pm' or 'just once at night')"

| Answer | Action |
|---|---|
| Provides specific times | Create a cron job for each time using CronCreate |
| Says "default" or skips | Create one default cron job at 21:00 (9 PM) |
| Doesn't want auto-sync | Skip — user will trigger manually with "sync now" |

**Creating cron jobs:**

For each sync time, create a cron job using CronCreate:
- **Cron expression:** e.g., `"3 21 * * *"` for ~9pm (offset from :00 to spread load)
- **Recurring:** `true`
- **Prompt:**
  ```
  Trigger a MemSpren sync now. Read sync-buffer-active.txt at
  {vault_path}/.second-brain/Memory/ — check for sealed buffers.
  If sealed buffers exist or active buffer has entries, read
  Protocols/sync-protocol.md and execute all 11 steps. If no
  entries exist, reply 'Nothing to sync.'
  ```

**Important:** Cron jobs are session-scoped — they only persist for the current
Claude session (max 7 days). The sync schedule is stored in config.md so it can
be re-created automatically on each session start (handled by SKILL.md session
start flow, Step 8).

**Store sync schedule in config.md** (written in Step 9):
```yaml
sync_mode: batch
sync_interval_cron: "[list of times, e.g. 21:00]"
auto_sync_on_checkin_close: true
buffer_max_tokens: 3000
```

Say:
> "I've set up automatic sync at [times]. Your vault will be updated with
> everything captured during the day. You can also say 'sync now' anytime
> to trigger it manually. Note: sync schedules are re-created each session."

---

## Step 7: Journaling *(Phase 2 — skip for MMVP)*

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

## Step 8: Lifestyle tracking *(Phase 2 — skip for MMVP)*

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

## Step 9: Create files and structure

**Two locations are used:**
- **Skill folder** → `.second-brain/` in the mounted folder root (always fixed)
- **Vault content** → `vault_path` (set in Step 3)

### Create vault folders

Create at `vault_path` (write a seed file or use mkdir to ensure folders exist):

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
Notes/Patterns/
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
Logs/
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
description: "Unified task inbox for all tasks"
created: [TODAY]
status: active
---
# Tasks Inbox

## Active Tasks

## Completed (last 2 weeks)
```

### Create .second-brain/ directory and config

#### .second-brain/config.md

Write to `.second-brain/config.md`:

```yaml
vault_path: "[from Step 3]"
check_in_time: "[from Step 4]"
project_idle_threshold_days: 7
task_archive_after_days: 14
log_retention_days: 90
moc_suggestion_link_threshold: 8
auto_archive_enabled: true
sync_mode: batch
sync_interval_cron: "[from Step 6]"
auto_sync_on_checkin_close: true
buffer_max_tokens: 3000
setup_complete: false
```

#### .second-brain/Memory/insights.md

```
LAST_UPDATED: [TODAY]

WHAT_MATTERS_NOW
[To be populated after first check-in]

RECENT_CHALLENGES

PATTERNS_OBSERVED

STRATEGIES_WORKING

STRATEGIES_NOT_WORKING

ENERGY_STATE

MINDSET_STATE

VISION_ALIGNMENT
```

#### .second-brain/Memory/goals.md

```
LAST_UPDATED: [TODAY]

LEAD_DOMINO
[To be populated after first check-in]

TOP_3

WHAT_TO_AVOID

HEALTH_PRIORITY

EMOTIONAL_CHECK

WEEKLY_MICRO_GOALS

QUARTERLY_GOALS
```

#### .second-brain/Memory/hot-memory.md

```
LAST_UPDATED: [TODAY]

ACTIVE_PROJECTS [max 3]

OPEN_THREADS

EVIDENCE_TRAIL

KEY_INSIGHTS

IDEAS_PARKED
```

#### .second-brain/Memory/system-state.md

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

## Behavioral Flags
journaling: false
lifestyle_tracking: false
auto_archive: true
moc_suggestions: true
```

#### .second-brain/Memory/sync-buffer-001.md

```yaml
---
node_type: sync-buffer
buffer_id: "001"
state: active
created: [ISO timestamp]
sealed_at: null
word_count: 0
entry_count: 0
---
```

#### .second-brain/Memory/sync-buffer-active.txt

Write `001` to this file.

#### .second-brain/Memory/sync-archive/

Create this directory (write a `.gitkeep` file if needed to ensure it exists).

### Initialize git in the vault (if available)

If git was found in Step 1:
```bash
cd [vault_path] && git init && git add -A && git commit -m "initial vault snapshot"
```

Create `.gitignore` in vault root:
```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.DS_Store
.trash/
```

Tell user:
> "I've initialized git in your vault for version control. Every time I modify
> a file during sync, I'll commit the previous version first so nothing is ever lost."

If git was NOT found, skip silently.

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

## Step 10: Guided tour

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
| `Notes/` | Learnings, patterns, resources, reference material |
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

## Step 11: Mark setup complete

**Update .second-brain/config.md:**

Change `setup_complete: false` → `setup_complete: true` and write back.

**Update .second-brain/Memory/system-state.md:**

Change `setup_complete: false` → `setup_complete: true` in frontmatter and write back.

**Update .memspren-config at workspace root:**

Change `setup_complete: false` → `setup_complete: true` and write back.

**Log to system-log.md:**

Write `{vault_path}/Logs/system-log.md`:

```
[TIMESTAMP] SETUP COMPLETE
  vault_path: [path]
  check_in_time: [time]
  sync_mode: batch
  sync_schedule: [times or "manual"]
  protocols_created: [list]
  folders_created: [count]
  seed_files_created: [count]
  git_initialized: [yes/no]
```

---

## Error handling

| Problem | Action |
|---|---|
| Vault path can't be created | Tell user, ask for different path — do not proceed |
| Git not available | Note it, continue — git is optional |
| User skips all optional steps | Fine — create structure only, no protocol files |
| User wants to restart setup | Set `setup_complete: false` in `.second-brain/config.md`, `.second-brain/Memory/system-state.md`, and `.memspren-config`, then reload |
| CronCreate not available | Skip cron jobs — user triggers sync manually with "sync now" |
