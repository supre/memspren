# Check-in Protocol

Triggered when user says "check in", "let's do my daily check-in",
"end of day", or anything signaling they want to log their day.

Read `.second-brain/Memory/insights.md`, `.second-brain/Memory/goals.md`,
and `.second-brain/Memory/hot-memory.md` before starting.
These are your ONLY context sources during conversation — do NOT read vault files.

Read `Protocols/entity-protocol.md` only during sync (not during conversation).
Read `Protocols/linking-protocol.md` only during sync (not during conversation).

---

## Checklist

Copy and track:
```
- [ ] Step 1: Open the conversation
- [ ] Step 2: Check for missed days
- [ ] Step 3: Brain dump
- [ ] Step 4: Silent inference pass
- [ ] Step 5: Targeted follow-up
- [ ] Step 6: Extract and buffer entities
- [ ] Step 7: Journaling (if enabled)
- [ ] Step 8: Lifestyle check-in (if enabled)
- [ ] Step 9: Synthesis and close
- [ ] Step 10: Update memory
```

---

## Step 1: Open the conversation

Open warmly and casually. Vary the phrasing — don't repeat the same
opener every day.

Examples:
> "Hey, how was your day?"
> "Ready for your check-in?"
> "What's been going on today?"

Do not ask structured questions yet. Let the user set the tone.

---

## Step 2: Check for missed days

**Read** `.second-brain/Memory/system-state.md` to get `last_checkin_date`.

Compare today's date against `last_checkin_date`.

> **Note:** `last_checkin_date` is written to system-state.md at the
> end of every check-in (Step 10). On the very first check-in it won't
> exist — treat that as a 0-day gap and proceed normally.

| Gap      | Action                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 0–1 days | No mention — proceed normally                                                                                                  |
| 2–3 days | Acknowledge briefly: *"Looks like a couple of days have passed — anything worth catching me up on before we dive into today?"* |
| 4+ days  | Acknowledge clearly: *"It's been a while since we last checked in. Want to do a quick catch-up before we cover today?"*        |

If gap is 3+ occurrences in the last 30 days, flag it:

> "I've noticed check-ins have been inconsistent lately —
> we've missed [X] days in the last month. Worth noting as
> a pattern. Want to adjust your check-in time or approach?"

**Note gap in sync-buffer** for later logging to system-log during sync.

---

## Step 3: Brain dump

Let the user talk. Do not interrupt with questions.
Do not ask structured prompts yet.

If the user seems stuck or silent, offer a light prompt:

> "Just talk me through your day — what happened, what you worked
> on, what's on your mind. No structure needed."

Let them go until they naturally stop or trail off.

---

## Step 4: Silent inference pass

After the brain dump, before responding, run through this checklist
internally. Do not show this to the user.
```
Inference checklist:
- [ ] Projects mentioned or updated?
- [ ] Ideas surfaced?
- [ ] People mentioned?
- [ ] Tasks completed, added, or blocked?
- [ ] Patterns emerging (repeated struggles, avoidance, energy)?
- [ ] Journaling questions covered naturally?
- [ ] Lifestyle metrics mentioned naturally?
- [ ] Anything that connects to Vision or Strategy?
- [ ] What is NOT covered that insights.md or goals.md says should be?
- [ ] Energy/mindset shift from previous state in insights.md?
```

Mark what was covered. Only follow up on what was NOT.

---

## Step 5: Targeted follow-up

Ask only about gaps from Step 4. One question at a time.
Never read out the full checklist. Sound natural.

Examples:

| Gap                              | Follow-up                                                         |
| -------------------------------- | ----------------------------------------------------------------- |
| Project not mentioned            | *"You didn't mention [project] — where did that land today?"*     |
| Idea referenced but vague        | *"You mentioned [idea] briefly — want to capture that properly?"* |
| Person mentioned without context | *"Who's [name]? New contact or someone I should already know?"*   |
| Task outcome unclear             | *"Did you end up finishing [task] or is it still open?"*          |
| Lifestyle metric not covered     | *"Did you make it to the gym today?"*                             |
| Journaling question not covered  | *"What would you do differently today if you could?"*             |

Stop follow-up when all gaps are covered or user signals they're done.

---

## Step 6: Extract and buffer entities

This is where the old protocol wrote directly to Obsidian.
**NEW: Write to sync-buffer.md instead.**

For everything the user shared, append a DETAILED entry to
`.second-brain/Memory/sync-buffer.md` using the Write/Edit tool.

**Entry format:**
```markdown
---

## Entry [N] | [YYYY-MM-DD HH:MM TZ] | check-in

### Full Context
[DETAILED capture of everything the user said. NOT condensed, NOT summarized.
Include: emotional state, specific names mentioned, specific numbers, quotes,
reasoning, decisions made, what they're struggling with, what they're excited about.
This is the source of truth for creating Obsidian entities during sync.
More detail is ALWAYS better than less.]

### Extracted Entities
- DAILY_LOG: [date] | [detailed summary of the day]
- PROJECT_UPDATE: [project name] | [what changed, why, specific evidence]
- PERSON_UPDATE: [name] | [interaction details, context, emotional weight]
- PERSON_NEW: [name] | [who they are, relationship, context]
- PATTERN_UPDATE: [pattern name] | [new evidence with dates]
- PATTERN_NEW: [name] | [description, when observed, triggers, evidence]
- TASK_NEW: [description] | [priority] | [due date] | [connected project]
- TASK_COMPLETE: [description] | [completion date]
- IDEA: [name] | [full context, reasoning, connections]
- LEARNING: [topic] | [what was learned, source, why it matters]

### Proposed Links
- [file A] ↔ [file B] | [reason for link]
```

**Rules for buffer entries:**
- Append only — never edit previous entries
- Be DETAILED — full context preserved (this is what Obsidian entities are built from later)
- Include emotional context, not just facts
- Include user's exact words where significant (quotes matter for patterns)
- Update `entry_count` and `last_updated` in buffer frontmatter
- Set `pending_sync: true` in buffer frontmatter

**Also update insights.md and goals.md in-place** if a significant shift was detected:
- Major mindset change (spiral, breakthrough, inner critic episode)
- Energy state change (gym miss, sleep failure, illness)
- Priority shift (user says something is more/less important now)
- New pattern identified

For minor updates, let the sync recalculation handle it.

---

## Step 7: Journaling (if enabled)

**Read** `.second-brain/Memory/system-state.md` → check `journaling: true/false`

If false → skip this step entirely.

If true → check which journaling questions were NOT already
covered naturally in the brain dump (Step 4 inference pass).

Ask only uncovered questions, one at a time, woven naturally.
Capture answers in the sync-buffer entry (append to the current entry's Full Context).

---

## Step 8: Lifestyle check-in (if enabled)

**Read** `.second-brain/Memory/system-state.md` → check `lifestyle_tracking: true/false`

If false → skip this step entirely.

If true → for each active lifestyle metric:
- Check if mentioned naturally in brain dump
- If yes → already captured in buffer, do not ask again
- If no → ask naturally, one metric at a time

Capture responses in the sync-buffer entry.

---

## Step 9: Synthesis and close

After all data is captured in the buffer, close the check-in
with a brief, natural synthesis. Three parts:

### Part 1 — What was captured

Short summary of what was captured. Note it hasn't synced to vault yet:

> "Captured your work on [project], the idea about [idea], and
> [task] for your inbox. These will sync to your vault on next sync."

### Part 2 — Pattern or observation (if anything notable)

Only include if something genuinely stands out. Don't force it.
Reference insights.md patterns if relevant:

> "I've noticed [pattern] showing up again — [brief observation]."

### Part 3 — Tomorrow's priorities

Pull from goals.md (current priorities) and what user shared.
Suggest 2–3 things max:

> "For tomorrow — based on what's open, I'd focus on:
> 1. [most important task or project milestone]
> 2. [second priority]
> 3. [optional third if clearly important]"

### Part 4 — Sync prompt

> "Want me to sync this to your vault now, or let it accumulate?"

If `auto_sync_on_checkin_close: true` in config.md:
> "Auto-syncing to your vault now..."
> Then trigger sync (read `Protocols/sync-protocol.md` and execute).

---

## Step 10: Update memory

**Update system-state.md** (using Write tool):
```yaml
last_checkin_date: [TODAY]
last_checkin_summary: [one line summary]
```

**If sync was triggered in Step 9:** sync-protocol.md handles all memory updates.
**If sync was NOT triggered:** insights.md and goals.md should already be updated in-place from Step 6 (for significant shifts only).

---

## Error handling

| Problem                                  | Action                                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------- |
| User is very brief, gives minimal info   | Ask one open follow-up: *"Anything else on your mind today?"* — don't push further |
| User wants to skip check-in              | Respect it. Note in buffer: `CHECK-IN SKIPPED` with date.                          |
| User contradicts something in insights   | Trust the user. Update insights.md immediately.                                    |
| User seems stressed or overwhelmed       | Acknowledge it first before any capture. Don't push through the checklist.         |
| Buffer write fails                       | Fall back to updating insights.md and goals.md directly. Log the failure.          |
