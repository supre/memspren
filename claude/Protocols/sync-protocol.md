# Sync Protocol

Governs batch synchronization from rotating sync buffers to Obsidian vault.
Triggered by: user explicit ("sync now"), cron interval, end of check-in, or buffer overflow.

---

## Primary path: Lobster workflow

**Always trigger sync via the Lobster workflow first.** The workflow handles every step
deterministically — locking, extraction, entity writing, memory refinement, archiving, and cleanup.

Read `.second-brain/config.md` to get `vault_path`, `vault_name`, and `config_path`, then run:

```bash
lobster run \
  --file ~/.openclaw/skills/memspren/workflows/sync.lobster \
  --args-json '{
    "vault_path": "[vault_path]",
    "vault_name": "[vault_name]",
    "config_path": "[vault_path]/.second-brain/config.md"
  }'
```

Wait for the workflow to complete. On success it will output a metrics summary.
Confirm to the user: "Synced. [summary from metrics output]."

**If the workflow completes successfully, stop here — do not execute the manual steps below.**

---

## Fallback: manual execution

Only proceed with the steps below if Lobster is unavailable or the workflow fails.
Each step maps directly to a `memcli` command. Execute them in order.

Read `Protocols/entity-protocol.md` and `Protocols/linking-protocol.md` before Step 4.

All vault operations use the Read/Write/Edit tools. Vault content paths are prefixed with `vault_path` from `.second-brain/config.md`. Skill operational files (memory, config) are at `.second-brain/`.

### Checklist

Copy and track:
```
- [ ] Step 1: Pre-sync validation
- [ ] Step 2: Load current state
- [ ] Step 3: Read and process sync buffer
- [ ] Step 4: Batch create/update vault entities
- [ ] Step 5: Recalculate insights.md
- [ ] Step 6: Recalculate goals.md
- [ ] Step 7: Update hot-memory.md
- [ ] Step 8: Update system-state.md
- [ ] Step 9: Archive and clean up buffer
- [ ] Step 10: Log sync results
- [ ] Step 11: Confirm to user
```

---

## Step 1: Pre-sync validation

Verify vault is accessible by reading a known file:
- Read `{vault_path}/Tasks/tasks-inbox.md` (or any seed file created during setup)
- If the file cannot be read, tell user: "I can't access your vault at [vault_path]. Please check the path in `.second-brain/config.md`."
- Do NOT proceed with sync if vault is inaccessible.

**Git availability check (optional):**
- Run `git --version` via Bash
- If git is available, it will be used for safety checkpoints in Step 4
- If git is not available, skip safety checkpoints — buffer data is still safe

---

## Step 2: Load current state

Read these files (all are `.second-brain/` files — use Read tool directly):

1. `.second-brain/memory/insights.md` — previous user understanding
2. `.second-brain/memory/goals.md` — previous goals (check: were they met?)
3. `.second-brain/memory/hot-memory.md` — current project state
4. `.second-brain/memory/system-state.md` — config flags, last sync timestamp

**Identify sealed buffers:**
5. Read `.second-brain/memory/sync-buffer-active.txt` — get active buffer ID
6. Use Glob to find all `.second-brain/memory/sync-buffer-*.md` files
7. Read frontmatter of each buffer file — find those with `state: sealed`
8. Sort sealed buffers by buffer ID (process oldest first)

---

## Step 3: Read and process sync buffer

**If sealed buffers exist:** Read the **oldest sealed buffer** (lowest buffer ID with `state: sealed`). This is the primary data source for this sync.

**If no sealed buffers exist:** Check the active buffer:
- If active buffer has entries (`entry_count > 0`), seal it first via Bash:
  ```bash
  memcli rotate-buffer --vault-path "[vault_path]" --rotate
  ```
  This seals the current active buffer and creates the next one. Then read the now-sealed buffer.

**If no buffers have entries:** Skip sync, notify user "Nothing to sync."

For the selected sealed buffer, parse each entry:

1. **Identify all extracted entities** (DAILY_LOG, PROJECT_UPDATE, PERSON_UPDATE, PATTERN_UPDATE, TASK_NEW, TASK_COMPLETE, IDEA, LEARNING)
2. **Identify all proposed links** between entities
3. **Group by entity type** for batch processing
4. **Merge entries for same entity** (e.g., multiple PROJECT_UPDATEs for the same project → combine into one update)

---

## Step 4: Batch create/update vault entities

Read `Protocols/entity-protocol.md` now.
Read `Protocols/linking-protocol.md` now.

**Before writing ANY entity**, follow the Smart Merge flow:

1. **Scan:** Use Glob to list all `.md` files in the target folder within `vault_path`. Read the first ~20 lines of each file to extract the `description` field from frontmatter.

2. **Decide:** Compare descriptions. Does an existing file match what you're about to create?
   - If YES → read the full file, then:
     - If new content COMPLEMENTS existing → git safety checkpoint, then append
     - If new content CONFLICTS with existing → git safety checkpoint, update file,
       notify user: "Updated [file]. Previous said [X], new says [Y]."
   - If NO match → create new file with `description` in frontmatter

3. **Git safety (if git available):** Before modifying ANY existing vault file, run via Bash:
   ```
   cd [vault_path] && git add "[file_path]" && git commit -m "pre-sync snapshot: [file]"
   ```
   If git is not available, skip this step.

4. **Description field:** Every new file MUST include `description` in frontmatter —
   a one-line summary of what the file is about. This is the search key for future merges.

**Scope rules for scanning:**

| node_type | Scan folder        | Merge aggressiveness                        |
| --------- | ------------------ | ------------------------------------------- |
| vision    | `Vision/`          | Aggressive — few files, merge readily       |
| strategy  | `Strategy/`        | Aggressive — few files                      |
| idea      | `Work/Ideas/`      | Moderate — similar ideas should consolidate |
| learning  | `Notes/Learnings/` | Moderate — same topic = same file           |
| pattern   | `Notes/Patterns/`  | Conservative — patterns are distinct        |
| project   | `Work/Projects/`   | No scan — always distinct                   |
| person    | `People/`          | No scan — always distinct                   |
| log-entry | `Log/Daily/`       | Date-based — same date = append             |

Process entities in this order:

### 4a — Daily log note

**CRITICAL: Check if today's daily log already exists before creating.**

Read `{vault_path}/Log/Daily/YYYY-MM-DD.md`.

- **If it exists:** APPEND new content to the existing log. Do NOT create a new file or overwrite.
  Add a timestamp header (e.g., `## Afternoon Update (3:00 PM)`)
  to separate from earlier content.

- **If it does NOT exist:** Create `Log/Daily/YYYY-MM-DD.md` with FULL DETAILED content from
  all buffer entries for that date.

In both cases: include everything the user said, full emotional context, decisions made, specific
names/numbers/quotes. This is the richest document — do not condense. Use the full context from
buffer entries.

Follow the daily log template from entity-protocol.md.
Link to all entities created/updated during this sync.
Update the `connected:` array (read, parse, append, deduplicate, write back).

### 4b — Project updates

For each project mentioned in buffer:
- Read existing project file from `{vault_path}/Work/Projects/`
- Append detailed progress note with `### [DATE]` section
- Update `last_modified` frontmatter
- Add today's log to `connected:` array (read, parse, append, write)
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
- New tasks: read `{vault_path}/Tasks/tasks-inbox.md`, append the task, write back
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
- Update `connected:` arrays for BOTH sides of each link (read, parse, append, write)
- Add `[[wiki links]]` in body text where contextually relevant
- Verify no orphan notes (every new file has at least one incoming link)

---

## Step 5: Recalculate insights.md

**Data sources (in priority order, latest-weighted):**

1. **sync buffer just processed** (HIGHEST — what just happened)
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

Update using Edit tool:
```yaml
last_sync: [ISO timestamp]
last_sync_summary: [one line summary of what was synced]
```

---

## Step 9: Archive and clean up buffer

Run via Bash:
```bash
memcli rotate-buffer \
  --vault-path "[vault_path]" \
  --cleanup \
  --buffer-id "[processed_buffer_id]" \
  --archive
```

This archives the sealed buffer to `.second-brain/buffers/sync-archive/`, deletes the
original, and resets the active buffer ID back to `001` if no sealed buffers remain
(so the counter doesn't keep incrementing across sync cycles).

**Check for remaining sealed buffers** after cleanup:
```bash
memcli rotate-buffer --vault-path "[vault_path]" --list-sealed
```
- If sealed buffers remain: notify user "Synced buffer [ID]. [X] more sealed buffers to process — say 'sync now' to continue."
- If none remain: buffer ID has been reset to `001` automatically.

---

## Step 10: Log sync results

Read `{vault_path}/Logs/system-log.md`, append sync log entry, write back:

```
[TIMESTAMP] SYNC COMPLETE
  buffer_processed: [buffer_id]
  entries_processed: [count]
  entities_created: [count and types]
  entities_updated: [count and types]
  insights_updated: [yes/no]
  goals_updated: [yes/no]
  buffer_archived: [archive filename]
  sealed_remaining: [count]
```

If `Logs/system-log.md` does not exist, create it with a header first.

---

## Step 11: Confirm to user

Brief, natural confirmation:
> "Synced: [summary]. Created [X], updated [Y]. Your vault is up to date."

Example:
> "Synced 3 brain dumps. Created today's daily log, updated Ship Consistently project, added Juliana interaction note, updated Inner Critic pattern. Insights and goals recalculated."

If sealed buffers remain:
> "Synced buffer [ID]. [X] more to go — say 'sync now' to continue, or I'll pick them up on the next scheduled sync."

---

## Error handling

| Problem                                     | Action                                                                                             |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Vault path not accessible                   | Notify user. Buffer is safe — retry on next sync trigger.                                          |
| File read/write error on specific file      | Log error, skip that file, continue with remaining entities. Report skipped files in confirmation. |
| Buffer is empty                             | "Nothing to sync." — no action needed.                                                             |
| Entity already exists (duplicate detection) | Append to existing, do not create duplicate.                                                       |
| insights.md exceeds 700 tokens after recalc | Compress: drop oldest details first, keep pattern names + dates, prioritize sections per Step 5.   |
| Sync interrupted mid-process                | Buffer NOT archived/deleted until Step 9. Safe to retry — buffer still has all data.               |
| Git not available                           | Skip safety checkpoints. Proceed with sync normally.                                               |
