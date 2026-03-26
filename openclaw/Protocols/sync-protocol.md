# Sync Protocol

Governs batch synchronization from brain dump log to Obsidian vault.

**Triggered by:** user explicit ("sync now"), cron interval, end of check-in, or buffer overflow.

**Key Behavior (Updated 2026-03-26):**
- Sync processes ALL available entries (sealed buffers + active buffer with entries)
- If active buffer has entries, it's sealed first, then synced
- Daily logs are created even if buffer didn't hit 1500-word rotation cap
- This ensures nightly sync always creates daily logs (no more missed days)

Read `Protocols/entity-protocol.md` and `Protocols/linking-protocol.md` before creating/updating vault files.

---

## Checklist

Copy and track:
```
- [ ] Step 1: Pre-sync validation
- [ ] Step 2: Load current state
- [ ] Step 3: Read and process sync buffer
- [ ] Step 4: Batch create/update Obsidian entities
- [ ] Step 5: Recalculate insights.md
- [ ] Step 6: Recalculate goals.md
- [ ] Step 7: Update hot-memory.md
- [ ] Step 8: Update system-state.md
- [ ] Step 9: Archive and clear buffer
- [ ] Step 10: Log sync results
- [ ] Step 11: Confirm to user
```

---

## Step 1: Pre-sync validation

Verify obsidian-cli is available and vault is accessible:
```bash
python scripts/check_cli.py --vault "<vault_name>"
```

If obsidian-cli not available or Obsidian not running:
- Tell user: "Obsidian needs to be open for me to sync your vault. Please open Obsidian and try again."
- Do NOT proceed with sync.
- Buffer data is safe — it persists until next successful sync.

---

## Step 2: Load current state

Read these files (all are `.second-brain/` files — use Read tool directly, not obsidian-cli):

1. **Check for active buffer:**
   - Read `.second-brain/Memory/sync-buffer-active.txt` to get current buffer ID
   - Read `.second-brain/Memory/sync-buffer-{ID}.md` (the active buffer)
   
2. **Check for sealed buffers:**
   - List all `sync-buffer-*.md` files with `state: sealed` in frontmatter
   
3. **Load context files:**
   - `.second-brain/Memory/insights.md` — previous user understanding
   - `.second-brain/Memory/goals.md` — previous goals (check: were they met?)
   - `.second-brain/Memory/hot-memory.md` — current project state
   - `.second-brain/Memory/system-state.md` — config flags, last sync timestamp

---

## Step 3: Seal active buffer if needed, then process all buffers

**NEW PROTOCOL (Updated 2026-03-26):**

The sync should process **all available entries**, whether they're in sealed buffers or still in the active buffer.

### 3a: Seal active buffer if it has entries

1. Read the active buffer (from Step 2)
2. Check `entry_count` in frontmatter OR count `## Entry` sections
3. **If active buffer has ANY entries (entry_count > 0):**
   - Update frontmatter: `state: sealed`, `sealed_at: [timestamp]`, `word_count: [actual count]`
   - Create new active buffer with next ID
   - Update `sync-buffer-active.txt` to point to new buffer
4. **If active buffer is empty:** leave it as-is (nothing to seal)

### 3b: Collect all sealed buffers for processing

After sealing active buffer (if needed), gather all sealed buffers:
- List all `sync-buffer-*.md` files with `state: sealed`
- Sort by `sealed_at` timestamp (oldest first)
- Read each buffer in order

### 3c: Parse buffer entries

For each sealed buffer, parse each entry:

1. **Identify all extracted entities** (DAILY_LOG, PROJECT_UPDATE, PERSON_UPDATE, PATTERN_UPDATE, TASK_NEW, TASK_COMPLETE, IDEA, LEARNING)
2. **Identify all proposed links** between entities
3. **Group by entity type** for batch processing
4. **Merge entries for same entity** (e.g., multiple PROJECT_UPDATEs for the same project → combine into one update)

**If NO sealed buffers exist and active buffer is empty:** skip sync, notify user "Nothing to sync."

---

## Step 4: Batch create/update Obsidian entities

Read `Protocols/entity-protocol.md` now.
Read `Protocols/linking-protocol.md` now.

**Before writing ANY entity**, follow the Smart Merge flow:

1. **Scan:** Run `scripts/scan_descriptions.py --vault-path [vault_path] --folder [relevant_folder]`
   to get existing files with descriptions in that folder.

2. **Decide:** Read the descriptions. Does an existing file match what you're about to create?
   - If YES → read the full file via obsidian-cli, then:
     - If new content COMPLEMENTS existing → git commit snapshot, then append
     - If new content CONFLICTS with existing → git commit snapshot, update file,
       notify user: "Updated [file]. Previous said [X], new says [Y]. Git commit [hash] for rollback."
   - If NO match → create new file with `description` in frontmatter

3. **Git safety:** Before modifying ANY existing file, run:
   `scripts/git_commit.py --vault-path [vault_path] --file [file_path] --message "pre-sync snapshot"`

4. **Description field:** Every new file MUST include `description` in frontmatter —
   a one-line summary of what the file is about. This is the search key for future merges.

**Scope rules for scanning:**

| node_type | Scan folder | Merge aggressiveness |
|---|---|---|
| vision | `Vision/` | Aggressive — few files, merge readily |
| strategy | `Strategy/` | Aggressive — few files |
| idea | `Work/Ideas/` | Moderate — similar ideas should consolidate |
| learning | `Notes/Learnings/` | Moderate — same topic = same file |
| pattern | `Notes/Patterns/` | Conservative — patterns are distinct |
| project | `Work/Projects/` | No scan — always distinct |
| person | `People/` | No scan — always distinct |
| log-entry | `Log/Daily/` | Date-based — same date = append |
| kt | `Work/KT/` | Moderate — same system/component = same file |

Process entities in this order:

### 4a — Daily log note

**CRITICAL: Check if today's daily log already exists before creating.**

```bash
obsidian vault="[vault_name]" read path=Log/Daily/YYYY-MM-DD.md
```

- **If it exists:** APPEND new content to the existing log. Do NOT create a new file or overwrite.
  Use `obsidian vault="[vault_name]" append` to add new sections for the time period covered
  by the current buffer entries. Add a timestamp header (e.g., `## Afternoon Update (3:00 PM)`)
  to separate from earlier content.

- **If it does NOT exist:** Create `Log/Daily/YYYY-MM-DD.md` with FULL DETAILED content from
  all buffer entries for that date.

In both cases: include everything the user said, full emotional context, decisions made, specific
names/numbers/quotes. This is the richest document — do not condense. Use the full context from
buffer entries.

Follow the daily log template from entity-protocol.md.
Link to all entities created/updated during this sync.
Update the `connected:` array using the helper script (append, don't replace).

### 4b — Project updates

For each project mentioned in buffer:
- Read existing project file from Obsidian
- Append detailed progress note with `### [DATE]` section
- Update `last_modified` frontmatter
- Add today's log to `connected:` array via `scripts/update_connected.py`
- Write back with full wiki links to related entities

### 4c — Ideas

For each new idea in buffer:
- Create atomic idea file with full context from buffer
- Link to daily log and related projects/people
- Include user's exact words and reasoning, not just summary

### 4d — People

For each person mentioned in buffer:
- If exists: append interaction note under `## Interaction Log`
- If new: create person file with full context
- Link to daily log and connected projects

### 4e — Tasks

For each task in buffer:
- New tasks: append to `Tasks/tasks-inbox.md`
- Completed tasks: mark `- [x]` with completion date
- Blocked tasks: update status, flag in hot-memory

### 4f — Patterns

For each pattern in buffer:
- If pattern note exists: append new evidence with date
- If new pattern: create pattern note in `Notes/Patterns/`
- Link to daily log and related entities

### 4g — Learnings

For each learning in buffer:
- Create or update learning note with full context
- Link to source (daily log) and related projects/ideas

### 4h — Cross-linking pass

After all entities are created/updated:
- Run through ALL proposed links from buffer
- Update `connected:` arrays for BOTH sides of each link (using `scripts/update_connected.py`)
- Add `[[wiki links]]` in body text where contextually relevant
- Verify no orphan notes (every new file has at least one incoming link)

---

## Step 5: Recalculate insights.md

**Data sources (in priority order, latest-weighted):**

1. **sync-buffer.md** (HIGHEST — what just happened)
2. **Previous insights.md** (HIGH — accumulated inference)
3. **hot-memory.md** (MEDIUM — project context)
4. **goals.md** (LOW — were previous goals met or missed?)

**Recalculation rules:**
- New data OVERRIDES old data where conflicting
- Patterns ACCUMULATE (add new evidence, don't discard old patterns)
- Energy/mindset = LATEST snapshot (most recent state matters most)
- Strategies: update working/not-working based on new evidence
- What matters: recalculate based on what user ACTUALLY talked about (not what they stated aspirationally)

**Compression rules (must stay under 700 tokens):**
- Drop details older than ~7 days unless they're foundational patterns
- Keep pattern names + latest evidence dates (not full history)
- Specific > vague (dates, numbers, quotes > "user seemed stressed")
- If over 700 tokens after recalculation, prioritize: WHAT_MATTERS_NOW > ENERGY_STATE > MINDSET_STATE > PATTERNS > STRATEGIES > VISION_ALIGNMENT

**Write using Write tool** (this is a `.second-brain/` file, NOT vault content).

**insights.md structure:**
```
LAST_UPDATED: [timestamp]

WHAT_MATTERS_NOW
[Top 2-3 things genuinely occupying user's mental/emotional space. Inferred from recent brain dumps.]

RECENT_CHALLENGES
[Active struggles with specific dates and details. Emotional, practical, professional.]

PATTERNS_OBSERVED
[Behavioral patterns with evidence dates. What triggers what. Both productive and destructive.]

STRATEGIES_WORKING
[What has demonstrably produced results. Cite specific evidence with dates.]

STRATEGIES_NOT_WORKING
[What's been attempted but isn't landing. Include WHY if inferable.]

ENERGY_STATE
[Composite: sleep quality/duration (last 3 days avg), physical activity, nutrition, hydration, mood trajectory. Include raw data points.]

MINDSET_STATE
[Where user's head is at. Inner critic? Confident? Spiraling? Growth-oriented? Recent emotional events. User's own frameworks.]

VISION_ALIGNMENT
[How recent actions connect or don't to stated future vision. Brief honest assessment.]
```

---

## Step 6: Recalculate goals.md

Derive from updated insights.md + hot-memory.md + weekly/quarterly plans (if available in vault).

**If weekly plan exists:** Read it from vault during sync to populate WEEKLY_MICRO_GOALS.
**If quarterly plan exists:** Read it from vault to populate QUARTERLY_GOALS.

**Write using Write tool.**

**goals.md structure:**
```
LAST_UPDATED: [timestamp]

LEAD_DOMINO
[The ONE thing that moves everything else forward. Adjusted for current energy/emotional state.]

TOP_3
[Max 3 priorities. Realistic given energy, schedule, emotional state. Achievable, not aspirational.]

WHAT_TO_AVOID
[Most likely failure mode today based on patterns. What NOT to do.]

HEALTH_PRIORITY
[The ONE health thing with biggest impact today based on what's failing in ENERGY_STATE.]

EMOTIONAL_CHECK
[What user needs emotionally today. More structure? Freedom? Gentle push? Hard truth? Space?]

WEEKLY_MICRO_GOALS [from weekly plan if available]
[Week label] ([date range]):
- KR1: [goal] | [STATUS]
- KR2: [goal] | [STATUS]
- KR3: [goal] | [STATUS]

QUARTERLY_GOALS [from quarterly plan if available]
[Quarter label] ([date range]):
- [metric]: [current/target] | [STATUS]
```

---

## Step 7: Update hot-memory.md

Update project/task state ONLY based on buffer data. No patterns, no lifestyle, no mindset (those are in insights.md now).

**Must stay under 500 tokens.**

**Write using Write tool.**

**hot-memory.md structure:**
```
LAST_UPDATED: [timestamp]

ACTIVE_PROJECTS [max 3, one line each with current status]

OPEN_THREADS [bounded list of what's pending this week]

EVIDENCE_TRAIL [cumulative date-stamped shipped artifacts]

KEY_INSIGHTS [cumulative distilled learnings]

IDEAS_PARKED [not building now]
```

---

## Step 8: Update system-state.md

Update using Write tool:
```yaml
last_sync: [ISO timestamp]
last_sync_summary: [one line summary of what was synced]
```

---

## Step 9: Archive and clear buffers

**For each sealed buffer that was synced:**

1. **Archive:** Copy buffer content to `.second-brain/Memory/sync-archive/YYYY-MM-DD-HHMMSS-{buffer_id}.md`
   - Create `sync-archive/` directory if it doesn't exist
   - Use Write tool (not obsidian-cli — this is a `.second-brain/` file)
   - Include buffer ID in archive filename (e.g., `2026-03-26-053000-001.md`)

2. **Delete sealed buffer:** Remove the sealed buffer file after archiving

**Active buffer:**
- Should already be fresh/empty (created in Step 3a when old active was sealed)
- If sync happened without sealing active buffer (because it was empty), active buffer stays as-is

---

## Step 10: Log sync results

Append to vault's `Logs/system-log.md` using obsidian-cli:
```bash
obsidian vault="[vault_name]" append \
  path=Logs/system-log.md \
  content="\n[TIMESTAMP] SYNC COMPLETE\n  entries_processed: [count]\n  entities_created: [count and types]\n  entities_updated: [count and types]\n  insights_updated: [yes/no]\n  goals_updated: [yes/no]\n  buffer_archived: [archive filename]"
```

---

## Step 11: Confirm to user

Brief, natural confirmation:
> "Synced: [summary]. Created [X], updated [Y]. Your vault is up to date."

Example:
> "Synced 3 brain dumps. Created today's daily log, updated Ship Consistently project, added Juliana interaction note, updated Inner Critic pattern. Insights and goals recalculated."

---

## Error handling

| Problem | Action |
| --- | --- |
| Obsidian not running | Notify user. Buffer is safe — retry on next sync trigger. |
| obsidian-cli error on specific file | Log error, skip that file, continue with remaining entities. Report skipped files in confirmation. |
| Buffer is empty | "Nothing to sync." — no action needed. |
| Entity already exists (duplicate detection) | Append to existing, do not create duplicate. |
| insights.md exceeds 700 tokens after recalc | Compress: drop oldest details first, keep pattern names + dates, prioritize sections per Step 5. |
| Sync interrupted mid-process | Buffer NOT cleared until Step 9. Safe to retry — buffer still has all data. |
