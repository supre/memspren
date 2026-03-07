# Check-in Protocol

Triggered when user says "check in", "let's do my daily check-in",
"end of day", or anything signaling they want to log their day.

Read `.second-brain/Memory/hot-memory.md` and `.second-brain/Memory/system-state.md` before starting.
Read `Protocols/entity-protocol.md` when creating or updating any entity.
Read `Protocols/linking-protocol.md` when writing any file.

All vault file operations use obsidian-cli. Vault content paths are relative to `vault_path` from `.second-brain/config.md`.
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

**Log gap** to `Logs/system-log.md` using obsidian-cli append:
```bash
obsidian vault="[vault_name]" append \
  path=Logs/system-log.md \
  content="\n[TIMESTAMP] CHECK-IN: Gap detected — [count] days since last check-in"
```

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

Create `Log/Daily/YYYY-MM-DD.md` using obsidian-cli create.

The full template is:

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

**Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path=Log/Daily/YYYY-MM-DD.md \
  content="---\nnode_type: log-entry\ncreated: YYYY-MM-DD\nstatus: active\nconnected: []\ntags: []\n---\n\n# YYYY-MM-DD\n\n## What Happened\n[content]\n\n## Energy and Focus\n[content]\n\n## Open Threads\n[content]\n\n## Reflections\n\n## Linked Updates"
```

### 6b — Project updates

For each project mentioned:
- **Read** the existing project file using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" read path=Work/Projects/[project].md
  ```
- Append a new `### [TODAY]` section under `## Progress Notes`
- Update `last_modified` in frontmatter
- Add today's log path to the `connected:` array using the helper script:
  ```bash
  python scripts/update_connected.py \
    --vault "[vault_name]" \
    --file "Work/Projects/[project].md" \
    --add "Log/Daily/YYYY-MM-DD.md"
  ```
- **Write** the updated file back using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" create \
    path=Work/Projects/[project].md \
    content="[full updated content]" \
    overwrite
  ```

If a project is mentioned that doesn't exist yet:
- Ask: *"Is [name] a new project? Want me to set it up properly
  with goals and a deadline?"*
- If yes → follow entity-protocol.md → Project creation
- If no → treat as an idea instead

### 6c — Ideas

For each new idea surfaced:
- **Create** atomic idea file using obsidian-cli (see entity-protocol.md for template):
  ```bash
  obsidian vault="[vault_name]" create \
    path=Work/Ideas/[idea-name].md \
    content="[filled template]"
  ```
- Link to today's daily log and any related projects or people
- If user elaborated significantly → capture full context
- If user mentioned it briefly → create stub, note it's underdeveloped

### 6d — People

For each person mentioned:

- **Read** the existing person file if it exists:
  ```bash
  obsidian vault="[vault_name]" read path=People/[firstname-lastname].md
  ```
- If file exists → append interaction note under `## Interaction Log`
  + add today's log path to `connected:` array using helper script + write back
- If no file → **create** `People/[name].md` using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" create \
    path=People/[firstname-lastname].md \
    content="[filled template]"
  ```
- Link to today's log and any connected projects

### 6e — Tasks

For each task mentioned:
- **Read** `{vault_path}/Tasks/tasks-inbox.md` using obsidian-cli:
  ```bash
  obsidian vault="[vault_name]" read path=Tasks/tasks-inbox.md
  ```
- **New task** → Append the task under `## Active Tasks` using obsidian-cli append:
  ```bash
  obsidian vault="[vault_name]" append \
    path=Tasks/tasks-inbox.md \
    content="\n- [ ] [Task description]\n  priority: high | medium | low\n  due: [date]\n  tags: #project | #idea | #life\n  created: YYYY-MM-DD"
  ```
- **Completed task** → Read tasks-inbox.md, mark `- [x]`, add `completed: [TODAY]`, write back with overwrite
- **Blocked task** → Append status info, flag in hot-memory if it blocks an active project

---

## Step 7: Journaling (if enabled)

**Read** `.second-brain/Memory/system-state.md` → check `journaling: true/false`

If false → skip this step entirely.

If true → check which journaling questions were NOT already
covered naturally in the brain dump (Step 4 inference pass).

Ask only uncovered questions, one at a time, woven naturally:

> "One more thing — [journaling question]?"

Do not ask all questions in sequence. It should feel like
conversation, not a form.

Capture answers and **append** to today's daily log under
the `## Reflections` section using obsidian-cli append:
```bash
obsidian vault="[vault_name]" append \
  path=Log/Daily/YYYY-MM-DD.md \
  content="\n### [Question]\n[Answer]"
```

---

## Step 8: Lifestyle check-in (if enabled)

**Read** `.second-brain/Memory/system-state.md` → check `lifestyle_tracking: true/false`

If false → skip this step entirely.

If true → for each active lifestyle protocol in system-state.md:
- Check if the metric was mentioned naturally in brain dump
- If yes → log it, do not ask again
- If no → ask naturally, one metric at a time

**Create** `Life/Lifestyle/YYYY-MM-DD-[area].md` with logged values using obsidian-cli create.
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

**Read** `Tasks/tasks-inbox.md` and pull from `hot-memory.md` (high priority + due soon)
and active projects. Suggest 2–3 things max:

> "For tomorrow — based on what's open, I'd focus on:
> 1. [most important task or project milestone]
> 2. [second priority]
> 3. [optional third if clearly important]"

Keep it short. Do not overwhelm.

---

## Step 10: Update memory and log

### Update hot-memory.md

**Read** `.second-brain/Memory/hot-memory.md`, rewrite with today's state.
Keep under 800 tokens. Include:

- Active projects with current status (one line each)
- Top 3 tasks by priority
- Any patterns currently flagged
- Any targets being re-evaluated
- Active protocols list

→ **Write** back using the Write tool (not obsidian-cli — this is a skill file, not vault content).

### Update system-state.md

**Read** `.second-brain/Memory/system-state.md`, update:
```yaml
last_checkin_date: [TODAY]
last_checkin_summary: [one line summary]
```
→ **Write** back using the Write tool.

### Update index.md *(Phase 2)*

> **MMVP note:** Skip until `Context-Docs/index.md` exists.

Add any new nodes created today.
Update link frequency for any nodes that gained new connections.

### Log to system-log.md

**Append** to `{vault_path}/Logs/system-log.md` using obsidian-cli:
```bash
obsidian vault="[vault_name]" append \
  path=Logs/system-log.md \
  content="\n[TIMESTAMP] CHECK-IN COMPLETE\n  date: YYYY-MM-DD\n  entities_created: [count and types]\n  entities_updated: [count and types]\n  patterns_flagged: [any or none]\n  missed_days_gap: [count or none]\n  journaling: [completed/skipped]\n  lifestyle_tracked: [areas or none]"
```

---

## Error handling

| Problem                                  | Action                                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------- |
| obsidian-cli returns error               | Check if Obsidian is running. If not, tell user: "Obsidian needs to be open for me to update your vault. Please open Obsidian and try again." |
| User is very brief, gives minimal info   | Ask one open follow-up: *"Anything else on your mind today?"* — don't push further |
| User wants to skip check-in              | Respect it. Log: `CHECK-IN SKIPPED` with date. Note gap tomorrow.                  |
| Entity file missing that should exist    | Create it now with available context. Note it was auto-created in system-log.      |
| User contradicts something in hot-memory | Trust the user. Update hot-memory immediately.                                     |
| User seems stressed or overwhelmed       | Acknowledge it first before any logging. Don't push through the checklist.         |
