# Check-in Protocol

Triggered when user says "check in", "let's do my daily check-in",
"end of day", or anything signaling they want to log their day.

Read `.second-brain/Memory/hot-memory.md` and `.second-brain/Memory/system-state.md` before starting.
Read `Protocols/entity-protocol.md` when creating or updating any entity.
Read `Protocols/linking-protocol.md` when writing any file.

All vault files are read and written using the Read/Write/Edit tools.
Vault content paths are prefixed with `vault_path` from `.second-brain/config.md`.
Skill operational files (Memory, config) are at `.second-brain/` — not in the vault.

---

## Checklist

Copy and track:
```
- [ ] Step 1: Open the conversation
- [ ] Step 2: Check for missed days
- [ ] Step 3: Brain dump
- [ ] Step 4: Silent inference pass
- [ ] Step 5: Targeted follow-up
- [ ] Step 6: Create and update entities
- [ ] Step 7: Journaling (if enabled)
- [ ] Step 8: Lifestyle check-in (if enabled)
- [ ] Step 9: Synthesis and close
- [ ] Step 10: Update memory and log
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

Compare today's date against `last_checkin_date` in `.second-brain/Memory/system-state.md`.

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

Log gap to `Logs/system-log.md` every time it occurs.
Log pattern flag separately when threshold is crossed.

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
- [ ] What is NOT covered that hot-memory says should be?
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

## Step 6: Create and update entities

Read `Protocols/entity-protocol.md` now.
Read `Protocols/linking-protocol.md` now.

Create or update one entity at a time, in this order:

### 6a — Daily log note

Create `Log/Daily/YYYY-MM-DD.md` using the canonical template from
entity-protocol.md. The full template is:

```markdown
---
node_type: log-entry
created: [TODAY]
status: active
connected:
  - [project files mentioned]
  - [idea files mentioned]
  - [people files mentioned]
tags: []
---

# [YYYY-MM-DD]

## What Happened
[Prose summary of the day — written naturally, captures what happened,
how the user felt, what was on their mind]

## Energy and Focus
[How the user felt — inferred from tone if not stated directly]

## Open Threads
[Anything unresolved, pending, or uncertain]

## Reflections
[Journaling responses if journaling enabled — leave blank if not]

## Linked Updates
[List of files updated during this check-in with [[links]]]
```

→ Write the filled template to `{vault_path}/Log/Daily/[TODAY].md`

### 6b — Project updates

For each project mentioned:
- Read the existing project file from `{vault_path}/Work/Projects/`
- Append a new `### [TODAY]` section under `## Progress Notes`
- Update `last_modified` in frontmatter
- Add today's log path to the `connected:` array
- Write the updated file back

If a project is mentioned that doesn't exist yet:
- Ask: *"Is [name] a new project? Want me to set it up properly
  with goals and a deadline?"*
- If yes → follow entity-protocol.md → Project creation
- If no → treat as an idea instead

### 6c — Ideas

For each new idea surfaced:
- Create atomic idea file in `{vault_path}/Work/Ideas/`
  using the template from entity-protocol.md
- Link to today's daily log and any related projects or people
- If user elaborated significantly → capture full context
- If user mentioned it briefly → create stub, note it's underdeveloped

### 6d — People

For each person mentioned:

```
MMVP: Try to Read People/[firstname-lastname].md
Phase 2: Search Context-Docs/index.md Node Registry
```

- If file exists → append interaction note under `## Interaction Log`
  + add today's log path to `connected:` array + write back
- If no file → create `People/[name].md` using the template from
  entity-protocol.md + link to today's log + any connected projects

### 6e — Tasks

For each task mentioned:
- **New task** → Read `{vault_path}/Tasks/tasks-inbox.md`, append
  the task under `## Active Tasks`, write back
- **Completed task** → Read tasks-inbox.md, mark `- [x]`, add
  `completed: [TODAY]`, write back
- **Blocked task** → Read tasks-inbox.md, add `status: blocked`
  + `blocked_reason:`, write back. Flag in hot-memory if it
  blocks an active project.

---

## Step 7: Journaling (if enabled)

Check `.second-brain/Memory/system-state.md` → `journaling: true/false`

If false → skip this step entirely.

If true → check which journaling questions were NOT already
covered naturally in the brain dump (Step 4 inference pass).

Ask only uncovered questions, one at a time, woven naturally:

> "One more thing — [journaling question]?"

Do not ask all questions in sequence. It should feel like
conversation, not a form.

Capture answers and append to today's daily log under
the `## Reflections` section.

---

## Step 8: Lifestyle check-in (if enabled)

Check `.second-brain/Memory/system-state.md` → `lifestyle_tracking: true/false`

If false → skip this step entirely.

If true → for each active lifestyle protocol in system-state.md:
- Check if the metric was mentioned naturally in brain dump
- If yes → log it, do not ask again
- If no → ask naturally, one metric at a time:
  > "Did you [metric] today?"

Create `Life/Lifestyle/YYYY-MM-DD-[area].md` with logged values.
Link to today's daily log.

Track completion. If a metric is skipped 3+ times in a week,
note it in the synthesis (Step 9) and flag in system-log.md.

---

## Step 9: Synthesis and close

After all entities are created and updated, close the check-in
with a brief, natural synthesis. Three parts:

### Part 1 — What was logged

Short summary of what got captured today. Not a list readout —
a sentence or two:

> "Okay, I've logged your work on [project], captured the idea
> about [idea], and added [task] to your inbox."

### Part 2 — Pattern or observation (if anything notable)

Only include if something genuinely stands out. Don't force it.

Examples:
> "You've mentioned feeling scattered three days in a row —
> might be worth looking at what's creating that."

> "The [project] hasn't come up in check-ins for a week —
> it might be going idle soon."

> "You've been logging a lot of ideas this week but not
> converting any to projects — just noting it."

### Part 3 — Tomorrow's priorities

Pull from `Tasks/tasks-inbox.md` (high priority + due soon)
and active projects in hot-memory. Suggest 2–3 things max:

> "For tomorrow — based on what's open, I'd focus on:
> 1. [most important task or project milestone]
> 2. [second priority]
> 3. [optional third if clearly important]"

Keep it short. Do not overwhelm.

---

## Step 10: Update memory and log

### Update hot-memory.md

Rewrite `.second-brain/Memory/hot-memory.md` to reflect today's state.
Keep under 800 tokens. Include:

- Active projects with current status (one line each)
- Top 3 tasks by priority
- Any patterns currently flagged
- Any targets being re-evaluated
- Active protocols list

→ Read the current file, rewrite with today's state, Write back.

### Update system-state.md

Read `.second-brain/Memory/system-state.md`, update:
```yaml
last_checkin_date: [TODAY]
last_checkin_summary: [one line summary]
```
Write back.

### Update index.md *(Phase 2)*

> **MMVP note:** Skip until `Context-Docs/index.md` exists.

Add any new nodes created today.
Update link frequency for any nodes that gained new connections.

### Log to system-log.md

Append to `{vault_path}/Logs/system-log.md`:
```
[TIMESTAMP] CHECK-IN COMPLETE
  date: [TODAY]
  entities_created: [count and types]
  entities_updated: [count and types]
  patterns_flagged: [any or none]
  missed_days_gap: [count or none]
  journaling: [completed/skipped]
  lifestyle_tracked: [areas or none]
```

---

## Error handling

| Problem                                  | Action                                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------- |
| User is very brief, gives minimal info   | Ask one open follow-up: *"Anything else on your mind today?"* — don't push further |
| User wants to skip check-in              | Respect it. Log: `CHECK-IN SKIPPED` with date. Note gap tomorrow.                  |
| Entity file missing that should exist    | Create it now with available context. Note it was auto-created in system-log.      |
| User contradicts something in hot-memory | Trust the user. Update hot-memory immediately.                                     |
| User seems stressed or overwhelmed       | Acknowledge it first before any logging. Don't push through the checklist.         |
