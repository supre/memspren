# Knowledge Transfer Protocol

Triggered when user mentions a knowledge transfer session, KT, onboarding session,
handoff, or any work-related knowledge sharing session they participated in.

Purpose: Capture KT sessions so knowledge is retrievable months later when production
issues, questions, or context is needed. Prevents knowledge decay.

Follows the sync protocol — KT documents are buffered, not created immediately.

---

## Step 1: Ask for the transcript and details

When user mentions a KT session, ask:

> "Got it — let's capture that KT properly so you can reference it later.
> Can you share:
> 1. The transcript (paste it or share a file)
> 2. Who was involved?
> 3. What system/component/feature was discussed?
> 4. Anything that was unclear or needs follow-up?"

If user provides a transcript, proceed to Step 2.
If user doesn't have a transcript but can describe it, capture their description as the "transcript" equivalent and note it's from memory, not a verbatim transcript.

---

## Step 2: Extract and structure

From the transcript and user's input, extract:

1. **Date** of the KT session
2. **Participants** (who was involved, their roles)
3. **System/Component/Feature** discussed
4. **Key Technical Details** (architecture, data flow, configs, APIs, databases, services)
5. **Context and Decisions** (why things are the way they are, historical decisions)
6. **Action Items** (who needs to do what, deadlines)
7. **Gotchas and Edge Cases** (things that could break, known issues, workarounds)
8. **Unclear Areas** (questions to follow up on, things that weren't fully explained)
9. **Related References** (Jira tickets, PRs, docs, Confluence pages, Slack threads mentioned)

---

## Step 3: Write to sync buffer

Append TWO entries to `sync-buffer.md`:

### Entry A: Structured KT document

```markdown
### Extracted Entities
- KT_STRUCTURED: [Topic Name] | date: [date] | participants: [names] | system: [system/component]
  Full structured content:
  
  ## Overview
  [One paragraph summary of what this KT covered and why it matters]
  
  ## Participants
  - [Name] — [role/context]
  
  ## System/Component
  [What system, service, or feature was discussed]
  
  ## Key Technical Details
  [Architecture, data flow, configs, APIs, databases — the stuff you need to debug production issues]
  
  ## Context and Decisions
  [Why things are built this way. Historical decisions. Business logic.]
  
  ## Gotchas and Edge Cases
  [Things that could break. Known issues. Workarounds. "If you see X, it's because Y."]
  
  ## Action Items
  - [ ] [Action] — [Owner] — [Deadline if mentioned]
  
  ## Unclear Areas / Follow-up
  [What wasn't fully explained. Questions to ask later.]
  
  ## Related References
  [Jira tickets, PRs, docs, Confluence, Slack threads]
```

### Entry B: Raw transcript

```markdown
- KT_TRANSCRIPT: [Topic Name] | date: [date]
  [Full raw transcript as provided by user]
```

### Proposed Links
```
- Work/KT/[Topic Name].md ↔ People/[participant].md | KT participant
- Work/KT/[Topic Name].md ↔ Log/Daily/YYYY-MM-DD.md | When KT happened
```

---

## Step 4: Confirm capture

> "Captured the KT on [topic]. I've got:
> - Structured summary with [X] key technical details, [Y] gotchas, [Z] action items
> - Full transcript preserved
> These will sync to your vault under Work/KT/ on next sync."

---

## During Sync: How KT entities are created in Obsidian

When sync-protocol.md processes KT entries from the buffer:

### Structured document
**Path:** `Work/KT/[Topic Name].md`

```markdown
---
node_type: knowledge-transfer
created: [KT date]
status: active
participants: [list]
system: [system/component]
transcript: Work/KT/Transcripts/[Topic Name].md
connected:
  - [people involved]
  - [daily log]
tags: [kt, work, system-name]
last_modified: [TODAY]
---

# KT: [Topic Name]

[Full structured content from Step 3 Entry A]

## Transcript
See [[Work/KT/Transcripts/[Topic Name].md|Full Transcript]]
```

### Raw transcript
**Path:** `Work/KT/Transcripts/[Topic Name].md`

```markdown
---
node_type: kt-transcript
created: [KT date]
status: active
source_kt: Work/KT/[Topic Name].md
connected:
  - Work/KT/[Topic Name].md
tags: [kt, transcript, work]
---

# Transcript: [Topic Name]

**Date:** [KT date]
**Participants:** [list]
**Source:** [verbatim transcript / from memory]

---

[Full raw transcript]
```

---

## Vault Structure

```
Work/
├── KT/                          ← Structured KT documents (day-job work)
│   ├── [Topic Name].md
│   └── Transcripts/             ← Raw transcripts
│       └── [Topic Name].md
├── Projects/                    ← Personal projects (Ship Consistently, etc.)
└── Ideas/                       ← Ideas
```

`Work/KT/` is for real work (day job). Separate from `Work/Projects/` (personal projects).

---

## Error Handling

| Problem | Action |
|---|---|
| No transcript available | Capture from user's memory. Note: "Reconstructed from memory, not verbatim transcript." |
| Transcript is very long (>5000 words) | Still persist full transcript. Structured doc stays concise. |
| User mentions KT from the past (not today) | Ask for date. Capture same way. Note it's retrospective. |
| Unclear what system was discussed | Ask: "What system or component was this about?" Don't guess. |
| KT overlaps with existing doc | Read existing, append new session as dated section. Don't create duplicate. |
