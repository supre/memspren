# Setup Protocol

Runs ONCE on first launch when `setup_complete: false` in config.md.
Never runs again unless manually reset.

All vault operations use obsidian-cli. Skill files (config, memory) are written directly.

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

### Git (required)
Verify git is installed:
```bash
git --version
```

If git not found, do NOT proceed:
> "MemSpren requires git for version-safe sync. Every vault write gets a safety
> snapshot so nothing is ever lost. Please install git and try again:
> - macOS: `brew install git` or `xcode-select --install`
> - Windows/Linux: https://git-scm.com/downloads"

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

| Answer        | Action                                                                                                                                   |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Provides path | Verify it exists and contains `.obsidian/`. Store as `vault_path` in config.md                                                           |
| Doesn't know  | Ask: *"Is this folder your vault?"* — check for a `.obsidian/` subfolder to confirm. Use the current folder if confirmed.                |
| No vault yet  | Tell them: *"No problem — I'll create the vault structure in the folder you've selected."* Use the current mounted folder as vault_path. |

**Verify vault path is accessible** — check that `.second-brain/config.md` exists (or the vault folder exists). If not:
> "I can't access your vault at that path. Please double-check it and try again."

Do NOT write to `.memspren-config` until the path is confirmed.

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

| Answer           | Action                                                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Provides content | **Create** `Vision/long-term-vision.md` using obsidian-cli with YAML frontmatter + `[[link]]` to `Vision/core-values.md` |
| Skips            | **Create** empty `Vision/long-term-vision.md` with placeholder                                                           |

**Create using obsidian-cli:**
```bash
obsidian vault="[vault_name]" create \
  path=Vision/long-term-vision.md \
  content="---\nnode_type: vision\ncreated: [TODAY]\nstatus: active\nconnected:\n  - Vision/core-values.md\ntags: []\nlast_modified: [TODAY]\n---\n\n# Long-term Vision\n\n[user content or placeholder]"
```

---

## Step 6: Sync schedule

Explain sync, then set the schedule.

Say:
> "Brain dumps are captured in real-time but synced to Obsidian in batches — fast and
> token-efficient. I recommend syncing 3 times a day (morning, afternoon, evening) by
> default. Want to keep that, or pick your own times?"

| Answer                  | Action                                                     |
| ----------------------- | ---------------------------------------------------------- |
| "Default" or skips      | Create 3 cron jobs: 08:00, 13:00, 21:00 in user's timezone |
| Provides specific times | Create a cron job for each time                            |
| "Manual only"           | Skip — user triggers sync with "sync now"                  |

**Creating cron jobs:**

For each sync time, create a cron job with:
- **Schedule:** cron expression (e.g. `0 8 * * *` for 08:00)
- **Timezone:** user's timezone (ask if unknown)
- **Session target:** `isolated`
- **Delivery:** `announce`
- **Payload:** `agentTurn` with message:
  ```
  Trigger a MemSpren sync now. Run the Lobster pipeline:
  lobster run workflows/sync.lobster --args-json '{"vault_path":"{vault_path}","vault_name":"{vault_name}","config_path":"{vault_path}/.second-brain/config.md"}'
  Follow Protocols/sync-protocol.md for approval gate handling. If the pipeline reports nothing to sync, reply 'Nothing to sync.'
  ```

**Store sync schedule in config.md:**

```yaml
sync_mode: batch
sync_interval_cron: "08:00, 13:00, 21:00"
sync_cron_job_ids: [list of cron job IDs]
auto_sync_on_checkin_close: true
buffer_max_tokens: 3000
```

Say:
> "Syncs scheduled for [times]. You can also say 'sync now' anytime to trigger manually."

---

## Step 7: Journaling *(Phase 2 — skip for MMVP)*

Ask:
> "Do you want a daily journaling prompt during check-ins?"

| Answer        | Action                                                                                                                              |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| No            | Skip — do not create journaling protocol                                                                                            |
| Yes (default) | Create `Protocols/journaling-context.md` with default questions                                                                     |
| Yes (custom)  | Ask: *"What would you like to reflect on each day?"* → capture response → create `Protocols/journaling-context.md` from their input |

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

| Answer | Action                                            |
| ------ | ------------------------------------------------- |
| No     | Skip — do not create any lifestyle protocol       |
| Yes    | Ask follow-up questions one at a time (see below) |

For each area they mention, ask ONE AT A TIME:
> "For [area] — what would you like to check in on?
> Specific metrics, or just a general feel?"

Create `Protocols/lifestyle-[area].md` per area using their answers.
Continue until user says they're done.

---

## Step 9: Create files and structure

Run the idempotent scaffold command. This creates all missing folders, seed files,
`.second-brain/` structure, memory stubs, `.gitignore`, and initializes git.
It never overwrites anything that already exists.

```bash
uv run scripts/memcli.py setup \
  --vault-path "[vault_path]" \
  --vault-name "[vault_name]"
```

The command returns JSON confirming what was created. Tell the user:
> "I've set up your vault structure and initialized git for version control.
> Every file I modify gets a safety snapshot so nothing is ever lost."

**Then write `.second-brain/config.md`** (create-only if it doesn't exist):

```yaml
vault_path: "[from Step 3]"
vault_name: "[from Step 3]"
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
agents:
  heavy: memspren-heavy
  light: memspren-light
  default: main
logging:
  verbosity: INFO
  max_log_bytes: 2097152
  keep_lines: 2000
lobster:
  resume_token_ttl_hours: 24
setup_complete: false
```

---

## Step 10: Guided tour

Say:
> "Your second brain is ready. Here's what I built:"

Walk through each area naturally:

| Folder           | What it's for                                   |
| ---------------- | ----------------------------------------------- |
| `Vision/`        | Your why — values, vision, principles           |
| `Strategy/`      | Quarterly goals and active strategies           |
| `Work/Projects/` | Deadline-driven work with tasks                 |
| `Work/Ideas/`    | Lightweight captures, no pressure               |
| `People/`        | Everyone you interact with, linked to your work |
| `Tasks/`         | One unified inbox for all tasks                 |
| `Log/`           | Daily notes, weekly reviews, analysis           |
| `Notes/`         | Learnings, resources, reference material        |
| `Inbox/`         | Catch-all for anything unsorted                 |
| `Archive/`       | Nothing ever deleted — everything lives here    |

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

**Update .second-brain/memory/system-state.md:**

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

| Problem                       | Action                                                                                                                |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| obsidian-cli not responding   | Check if Obsidian is running. Tell user: "Please open Obsidian and ensure the CLI is enabled in Settings → General."  |
| Vault path can't be accessed  | Tell user, ask for different path — do not proceed                                                                    |
| User skips all optional steps | Fine — create structure only, no protocol files                                                                       |
| User wants to restart setup   | Set `setup_complete: false` in both `.second-brain/config.md` and `.second-brain/memory/system-state.md`, then reload |
