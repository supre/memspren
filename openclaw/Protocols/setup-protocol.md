# Setup Protocol

Runs ONCE on first launch when `setup_complete: false` in config.md.
Never runs again unless manually reset.

All vault operations use obsidian-cli. Skill files (config, Memory) are written directly.

> **MMVP note:** Steps 5 and 6 (journaling, lifestyle tracking) are Phase 2
> features. Skip them for a minimal first working version — the system works
> without them. Include them when building toward the full MVP.

---

## Checklist

Copy and track progress before starting:

```
- [ ] Step 1: Check prerequisites (git, obsidian-cli)
- [ ] Step 2: Greet user
- [ ] Step 3: Vault location
- [ ] Step 4: Check-in time
- [ ] Step 5: Vision and goals
- [ ] Step 6: Sync schedule
- [ ] Step 7: Journaling (Phase 2 — skip for MMVP)
- [ ] Step 8: Lifestyle tracking (Phase 2 — skip for MMVP)
- [ ] Step 9: Create files and structure (includes git init)
- [ ] Step 10: Guided tour
- [ ] Step 11: Mark setup complete
```

---

## Step 1: Check prerequisites

### Git
Verify git is installed:
```bash
git --version
```

If git not found:
> "MemSpren requires git for version control of your vault. Every time I modify a file,
> I commit the previous version first so nothing is ever lost. Please install git:
> - macOS: `brew install git` or `xcode-select --install`
> - Linux: `sudo apt install git`
> - Windows: https://git-scm.com/download/win"

Do NOT proceed with setup until git is available.

### Obsidian CLI
(Already covered in Prerequisites section of SKILL.md)

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
| Provides path | Verify it exists and contains `.obsidian/`. Store as `vault_path` in config.md |
| Doesn't know | Ask: *"Is this folder your vault?"* — check for a `.obsidian/` subfolder to confirm. Use the current folder if confirmed. |
| No vault yet | Tell them: *"No problem — I'll create the vault structure in the folder you've selected."* Use the current mounted folder as vault_path. |

**Verify obsidian-cli access:**
```bash
obsidian version  # Check CLI is reachable
python scripts/check_cli.py --vault "[vault_name]"  # Full verification
```

If Obsidian is not running, tell user: "Please open Obsidian and try again."

---

## Step 4: Check-in time

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
| Provides content | **Create** `Vision/long-term-vision.md` using obsidian-cli with YAML frontmatter + `[[link]]` to `Vision/core-values.md` |
| Skips | **Create** empty `Vision/long-term-vision.md` with placeholder |

**Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path=Vision/long-term-vision.md \
  content="---\nnode_type: vision\ncreated: [TODAY]\nstatus: active\nconnected:\n  - Vision/core-values.md\ntags: []\nlast_modified: [TODAY]\n---\n\n# Long-term Vision\n\n[user content or placeholder]"
```

---

## Step 6: Sync schedule

Explain to the user how vault synchronization works, then set up cron jobs.

Say:
> "Your brain dumps are captured in real-time but synced to Obsidian in batches
> — this keeps things fast and token-efficient. I can set up automatic syncs
> throughout the day. How many times per day would you like your vault synced?
> (e.g. '3 times — noon, 5pm, 9pm' or 'just once at night')"

| Answer | Action |
|---|---|
| Provides specific times | Create a cron job for each time using the `cron` tool |
| Says "default" or skips | Create one default cron job at 21:00 (9 PM) |
| Doesn't want auto-sync | Skip — user will trigger manually with "sync now" |

**Creating cron jobs:**

For each sync time, create a cron job with:
- **Schedule:** `cron` kind with appropriate expression (e.g. `0 12 * * *` for noon)
- **Timezone:** User's timezone (from system or ask)
- **Session target:** `isolated`
- **Delivery:** `announce` (so user sees sync results)
- **Payload:** `agentTurn` with message:
  ```
  Trigger a MemSpren sync now. Read the sync-buffer at {vault_path}/.second-brain/Memory/sync-buffer.md
  — if pending_sync is true, execute the full sync protocol: read Protocols/sync-protocol.md from
  the memspren skill, follow all 11 steps (validate obsidian-cli, load state, process buffer, batch
  create/update Obsidian entities, recalculate insights.md + goals.md + hot-memory.md, archive buffer,
  clear buffer, log results). If pending_sync is false or buffer is empty, reply 'Nothing to sync.'
  Vault: {vault_name}. Remember to export PATH to include /Applications/Obsidian.app/Contents/MacOS
  before any obsidian-cli commands.
  ```

**Store sync schedule in config.md:**

Add to config.md during Step 8 (file creation):
```yaml
sync_mode: batch
sync_interval_cron: [list of times, e.g. "12:00, 17:00, 21:00"]
sync_cron_job_ids: [list of cron job IDs returned from creation]
auto_sync_on_checkin_close: true
buffer_max_tokens: 3000
```

**Default (if user skips):**

Create one cron job at 21:00 in user's timezone. Store in config.md.

Say:
> "I've set up automatic sync at [times]. Your vault will be updated with
> everything captured during the day. You can also say 'sync now' anytime
> to trigger it manually."

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
- **Vault content** → `vault_path` (set in Step 2)

### Create .second-brain/ directory

Create at workspace root (Write tool handles this).

### Create vault folders using obsidian-cli

For each folder below, use obsidian-cli to verify/create structure:

```bash
obsidian vault="[vault_name]" files path=Vision
obsidian vault="[vault_name]" files path=Strategy
obsidian vault="[vault_name]" files path=Work/Projects
obsidian vault="[vault_name]" files path=Work/Ideas
obsidian vault="[vault_name]" files path=People
obsidian vault="[vault_name]" files path=Life/Lifestyle
obsidian vault="[vault_name]" files path=Tasks
obsidian vault="[vault_name]" files path=Inbox
obsidian vault="[vault_name]" files path=Log/Daily
obsidian vault="[vault_name]" files path=Log/Weekly
obsidian vault="[vault_name]" files path=Log/Analysis
obsidian vault="[vault_name]" files path=Notes/Learnings
obsidian vault="[vault_name]" files path=Notes/Resources
obsidian vault="[vault_name]" files path=Notes/Reference
obsidian vault="[vault_name]" files path=Archive/Vision
obsidian vault="[vault_name]" files path=Archive/Strategy
obsidian vault="[vault_name]" files path=Archive/Projects
obsidian vault="[vault_name]" files path=Archive/Ideas
obsidian vault="[vault_name]" files path=Archive/People
obsidian vault="[vault_name]" files path=Archive/Lifestyle
obsidian vault="[vault_name]" files path=Archive/Tasks
obsidian vault="[vault_name]" files path=Archive/Inbox
obsidian vault="[vault_name]" files path=Archive/Log
obsidian vault="[vault_name]" files path=Archive/Notes
obsidian vault="[vault_name]" files path=Logs
```

(Obsidian will create missing folders automatically when files are written.)

### Create seed files using obsidian-cli

```bash
# Core values
obsidian vault="[vault_name]" create \
  path=Vision/core-values.md \
  content="---\nnode_type: vision\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# Core Values\n\n[Placeholder — add your values]"

# Guiding principles
obsidian vault="[vault_name]" create \
  path=Vision/guiding-principles.md \
  content="---\nnode_type: vision\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# Guiding Principles\n\n[Placeholder — add your principles]"

# Life philosophy
obsidian vault="[vault_name]" create \
  path=Vision/life-philosophy.md \
  content="---\nnode_type: vision\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# Life Philosophy\n\n[Placeholder — add your philosophy]"

# Quarterly goals
obsidian vault="[vault_name]" create \
  path=Strategy/quarterly-goals.md \
  content="---\nnode_type: strategy\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\nlast_modified: [TODAY]\n---\n\n# Quarterly Goals\n\n## This Quarter\n\n[Placeholder — add your goals]"

# Tasks inbox
obsidian vault="[vault_name]" create \
  path=Tasks/tasks-inbox.md \
  content="---\nnode_type: tasks-inbox\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\n---\n\n# Tasks Inbox\n\n## Active Tasks\n\n## Completed (last 2 weeks)"
```

### Create .second-brain/config.md

Write to `.second-brain/config.md` using the Write tool:

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

### Create .second-brain/Memory/hot-memory.md

Write using the Write tool:

```
LAST_UPDATED: [TODAY]

ACTIVE_PROJECTS [max 3]

OPEN_THREADS

EVIDENCE_TRAIL

KEY_INSIGHTS

IDEAS_PARKED
```

### Create .second-brain/Memory/insights.md

Write using the Write tool:

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

### Create .second-brain/Memory/goals.md

Write using the Write tool:

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

### Create .second-brain/Memory/sync-buffer.md

Write using the Write tool:

```
---
node_type: sync-buffer
last_updated: [TODAY]
pending_sync: false
entry_count: 0
---
```

### Create .second-brain/Memory/sync-archive/ directory

Create the directory for archived sync buffers.

### Initialize git in the vault

```bash
python3 scripts/git_commit.py --vault-path "[vault_path]" --init
```

Tell user:
> "I've initialized git in your vault for version control. Every time I modify
> a file, I'll commit the previous version first so nothing is ever lost."

### Create .second-brain/Memory/system-state.md

Write using the Write tool:

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

## Step 11: Mark setup complete

**Update .second-brain/config.md:**

Change `setup_complete: false` → `setup_complete: true` and write back using Write tool.

**Update .second-brain/Memory/system-state.md:**

Change `setup_complete: false` → `setup_complete: true` in frontmatter and write back.

**Log to system-log.md using obsidian-cli:**

```bash
obsidian vault="[vault_name]" create \
  path=Logs/system-log.md \
  content="---\nnode_type: log-entry\ncreated: [TODAY]\nstatus: active\nconnected: []\ntags: []\n---\n\n# System Log\n\n[TIMESTAMP] SETUP COMPLETE\n  vault_path: [path]\n  check_in_time: [time]\n  protocols_created: [list]\n  folders_created: [count]\n  seed_files_created: [count]"
```

(Use `create` instead of `append` for the initial system log.)

---

## Error handling

| Problem | Action |
|---|---|
| obsidian-cli not responding | Check if Obsidian is running. Tell user: "Please open Obsidian and ensure the CLI is enabled in Settings → General." |
| Vault path can't be accessed | Tell user, ask for different path — do not proceed |
| User skips all optional steps | Fine — create structure only, no protocol files |
| User wants to restart setup | Set `setup_complete: false` in both `.second-brain/config.md` and `.second-brain/Memory/system-state.md`, then reload |
