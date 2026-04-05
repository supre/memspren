# MemSpren — OpenClaw Skill

An [OpenClaw](https://openclaw.ai/) skill that turns your AI assistant into a thinking partner for managing a Zettelkasten-based second brain in Obsidian.

## What it does

You talk. MemSpren extracts entities, builds connections, and syncs everything to your Obsidian vault as linked atomic notes — automatically.

- **Brain dump → knowledge graph.** One messy paragraph becomes linked notes for people, projects, ideas, tasks, and learnings.
- **Three-layer memory.** Active memory stays in context. A write-only buffer captures everything during conversation. Batch sync pushes rich entities to Obsidian.
- **Smart merge.** Description-based deduplication prevents duplicate files. Git safety checkpoints before every modification.
- **Zero maintenance.** No manual linking, no tagging, no folder management. The skill handles all of it.

## Prerequisites

- [Obsidian](https://obsidian.md) installed with a vault created
- [Git](https://git-scm.com/) installed
- [OpenClaw](https://openclaw.ai/) installed and running
- [uv](https://docs.astral.sh/uv/) — Python package manager (`brew install uv`)
- [Lobster](https://www.npmjs.com/package/@clawdbot/lobster) — workflow runner (`npm install -g @clawdbot/lobster`)
- Python 3.9+

## Installation

### 1. Install OpenClaw plugins

The sync pipeline requires the `lobster` and `llm-task` plugins. Install and enable them:

```bash
openclaw plugins install lobster
openclaw plugins install llm-task
openclaw plugins enable lobster
openclaw plugins enable llm-task
openclaw gateway restart
```

### 2. Install memcli

`memcli` is the Python CLI that drives every sync pipeline step. Install it as a global uv tool from the **repo root** (where `pyproject.toml` lives):

```bash
# From the repo root — pyproject.toml is here, not inside openclaw/
uv tool install --editable .

# Verify — should print all available commands
memcli --help
```

> **Note:** `uv tool install` places `memcli` in `~/.local/bin/` so Lobster can call it from any directory. If you update `pyproject.toml` dependencies, reinstall with `uv tool install --reinstall --editable .`

### 3. Configure your OpenClaw agent

The sync pipeline routes all LLM calls to an agent named `main`. Create or confirm this agent in OpenClaw:

1. Open OpenClaw → Agents
2. Ensure an agent with id `main` exists and has the `llm-task` and `lobster` tools enabled
3. Set the model — any capable model works; `moonshotai/kimi-k2.5` via OpenRouter is the tested default

The model is configured in `~/.openclaw/openclaw.json` under `agents.list`. The vault's `.second-brain/config.md` also has an `agents:` section that maps `heavy`, `light`, and `default` to agent names — all three default to `main`.

### 4. Set up your vault

Run the setup command once to scaffold the vault structure and create the config file:

```bash
memcli setup \
  --vault-path /path/to/your/vault \
  --vault-name "Your Vault Name"
```

This creates all folders, seed files, and `.second-brain/config.md` idempotently — safe to re-run.

### 5. Verify the pipeline

Run the tests to confirm everything is wired correctly:

```bash
# From the repo root
uv run pytest
```

All tests create throwaway vaults under `/tmp` — nothing touches your real vault.

## Running a sync

Invoke the full pipeline via Lobster:

```bash
lobster run \
  --file workflows/sync.lobster \
  --args-json '{
    "vault_path": "/path/to/your/vault",
    "vault_name": "Your Vault Name",
    "config_path": "/path/to/your/vault/.second-brain/config.md"
  }'
```

Or trigger sync by saying "sync now" in an OpenClaw conversation — the skill invokes Lobster automatically.

## Pipeline stages

The sync runs as a deterministic Lobster workflow (`workflows/sync.lobster`):

| Stage | Step | What it does |
|-------|------|--------------|
| 0 | `lock` | Acquires `buffers/sync.lock` — prevents concurrent syncs |
| 0 | `check_cli` | Verifies Obsidian CLI availability and resolves write mode |
| 0 | `vault_diff` | Scans vault for files manually edited since last sync |
| 0 | `task_inbox` | Parses `tasks-inbox.md` for open/completed tasks |
| 0 | `rotate_buffer` | Seals the active sync buffer if it has content |
| 0 | `sync_gate` | **Halts pipeline cleanly if nothing to sync (exit 0)** |
| 1 | `extraction` | LLM extracts insights, goals, tasks, patterns from buffer |
| 2 | `parallel_refinement` | 4 parallel LLM jobs refine insights/goals/tasks/hot-memory |
| 3 | `merge_layer1` | Writes all 4 memory files to vault |
| 4a | `read_frontmatter` | Batch-reads YAML frontmatter for merge detection |
| 4b | `entity_plan` | LLM plans vault writes — creates brief notes per entity |
| 4c | `entity_writes` | LLM expands notes → full content, writes to vault |
| 4d | `entity_links` | Determines wikilinks, creates stubs for missing targets |
| 5 | `metrics` | Writes `metrics.json`, updates `system-state.md` |
| 5 | `archive_run` | Moves all `run/` artifacts to `run/archive/` with timestamp |
| 5 | `release_lock` | Releases lock, prunes stale tokens |

## Logs

All `memcli` pipeline logs are written to `/tmp/memcli/`:

```
/tmp/memcli/memcli-YYYY-MM-DD.log
```

If a sync fails, check this file first. Each step logs at DEBUG level with structured JSON fields. For OpenClaw gateway errors, check `/tmp/openclaw/openclaw-YYYY-MM-DD.log`.

## Troubleshooting

**`memcli: command not found`**  
Run `uv tool install --editable .` from the `openclaw/` directory. If installed but not found, ensure `~/.local/bin/` is in your `PATH`.

**Gateway HTTP 500 errors**  
The LLM call failed. Check `/tmp/openclaw/openclaw-YYYY-MM-DD.log` for the root cause — common causes are model rate limits, timeouts, or the OpenClaw gateway process needing a restart.

**`sync.lock` blocking a run**  
The lock file exists from a previous run. Remove it manually:  
```bash
rm /path/to/vault/.second-brain/buffers/sync.lock
```

**Pipeline exits at `sync_gate`**  
No content in the active buffer — there is nothing to sync. This is normal and intentional.

## Entity types

| Entity | Vault path | Description |
|--------|-----------|-------------|
| Project | `Work/Projects/[name].md` | Deadline-driven work with goals and progress notes |
| Idea | `Work/Ideas/[name].md` | Atomic thoughts, seeds for future projects |
| Person | `People/[name].md` | Interaction logs, connections to projects |
| Task | `Tasks/tasks-inbox.md` | Unified inbox, appended not created |
| Learning | `Notes/Learnings/[topic].md` | Things learned, connected to active work |
| Pattern | `Notes/Patterns/[name].md` | Recurring behavioral observations |
| Daily log | `Log/Daily/YYYY-MM-DD.md` | One note per day, hub of all entities |
| Vision | `Vision/[name].md` | Values, long-term aspirations |
| Strategy | `Strategy/[name].md` | Quarterly goals and strategic plans |

## File structure

```
memspren/                                 # Repo root
├── pyproject.toml                        # memcli package definition + deps (install from here)
└── openclaw/
    ├── SKILL.md                          # Skill definition (loaded by OpenClaw)
    ├── README.md                         # This file
    ├── workflows/
    │   └── sync.lobster                  # Lobster workflow — full sync pipeline
    ├── Protocols/
    │   ├── check-in-protocol.md
    │   ├── setup-protocol.md
    │   └── sync-protocol.md
    └── scripts/
        └── memcli/                       # Python CLI package
            ├── cli.py                    # Click command dispatcher
            ├── gateway.py                # OpenClaw gateway HTTP client
            ├── paths.py                  # VaultPaths — shared path constants
            ├── prompts/                  # LLM prompts for each pipeline step
            ├── schemas/                  # JSON schemas for LLM output validation
            ├── preflight/                # Stage 0: lock, check-cli, sync-gate
            ├── buffer/                   # Stage 0: rotate-buffer
            ├── scanning/                 # Stage 0/4a: vault-diff, task-inbox, frontmatter
            ├── extraction/               # Stage 1: run-extraction
            ├── memory/                   # Stage 2-3: parallel-memory, merge
            ├── entities/                 # Stage 4b-d: entity-plan, write, link
            ├── finalize/                 # Stage 5: metrics, archive-run
            ├── vault/                    # Git commit + connected: helpers
            └── tests/                    # Integration + unit tests
```

## Vault structure (created by setup)

```
[vault]/
├── .second-brain/                        # Skill state (not vault content)
│   ├── config.md                         # Settings, sync config, custom protocols
│   ├── memory/
│   │   ├── insights.md                   # User patterns, energy, mindset
│   │   ├── goals.md                      # Priorities, weekly/quarterly goals
│   │   ├── hot-memory.md                 # Active project/task state
│   │   ├── tasks.md                      # Task tracking
│   │   └── system-state.md              # Config flags, last sync timestamp
│   ├── buffers/
│   │   ├── sync-buffer-NNN.md            # Active/sealed sync buffers
│   │   └── sync.lock                     # Pipeline concurrency lock
│   └── run/
│       ├── archive/                      # Run artifacts with timestamps
│       └── (step outputs during sync)
├── Work/Projects/
├── Work/Ideas/
├── People/
├── Log/Daily/
├── Notes/Learnings/
├── Notes/Patterns/
├── Vision/
├── Strategy/
├── Tasks/
├── Inbox/
└── Archive/
```

## Key design decisions

- **Single agent.** All LLM calls go through the `main` agent. No heavy/light split — model selection is the user's choice in OpenClaw config.
- **Brief entity-plan, rich entity-write.** The entity-plan step produces compact bullet notes per entity (small LLM output). Entity-write expands these into full vault content via a separate LLM call — this keeps entity-plan reliable even with slow models.
- **Token efficiency.** Active memory stays under 2000 tokens total. Buffer is never read during conversation.
- **Filesystem writes.** All vault writes go directly to the filesystem. Obsidian CLI mode is available but filesystem is the default and tested path.
- **Git safety.** Every file modification is preceded by a git commit. Users can always `git diff` or `git revert`.
- **Description-based merge.** Every entity has a `description` frontmatter field used to detect duplicates before creating new files.
- **Nothing gets deleted.** Completed projects, old ideas, past tasks — everything is archived, never removed.
- **Run artifacts archived.** Every sync moves its intermediate files (`extraction-output.json`, `entity-plan.json`, etc.) to `run/archive/` with a timestamp suffix — full auditability with zero clutter.
