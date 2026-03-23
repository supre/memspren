# Changelog

All notable changes to the MemSpren skill are documented here.

---

## [0.5.0] — 2026-03-23

### Added
- **Three-layer Memory + Buffer + Sync architecture** — Active memory (insights, goals, hot-memory, system-state ~2000 tokens), rotating write-only sync buffers, and batch Obsidian vault sync. Conversations never touch the vault; syncs process bounded buffer data.
- **`Protocols/sync-protocol.md`** — NEW: 11-step batch sync protocol. Smart merge with description-based deduplication, optional git safety checkpoints, insights/goals recalculation, buffer archival. Fully adapted for native Read/Write/Edit tools.
- **Rotating sync buffer system** — `sync-buffer-001.md`, `sync-buffer-002.md`, etc. with `sync-buffer-active.txt` pointer. Buffers seal at 1500 words; each sync processes one sealed buffer (bounded context). Prevents context window overflow on heavy days.
- **`insights.md`** — Layer 1 memory file (700 tokens): user patterns, energy, mindset, strategies, vision alignment. Recalculated during sync.
- **`goals.md`** — Layer 1 memory file (500 tokens): lead domino, top 3 priorities, failure modes, health/emotional check, weekly/quarterly goals. Recalculated during sync.
- **Pattern entity type** — `Notes/Patterns/[name].md`: recurring behavioral themes with date-stamped evidence, triggers, and connected entities.
- **`description` field** — REQUIRED in all entity frontmatter. One-line summary used for smart merge detection and retrieval.
- **Custom protocols support** — User-created protocols in `.second-brain/Protocols/`, triggered via config.md intent mapping.
- **`.memspren-config`** — Workspace-root config file with vault_path and setup_complete flag.
- **Cron-based auto-sync** — Uses CronCreate for scheduled sync jobs. Session-scoped (re-created from config.md each session start).
- **Sync schedule step in setup** — Step 6: configure automatic sync times during first-run setup.
- **Prerequisites check in setup** — Step 1: checks git availability (non-blocking).

### Changed
- **`SKILL.md`**: Complete rewrite. Name changed to `memspren`. Three-layer architecture, session start flow (8 steps including cron re-creation), conversation flow section, sync triggers table, native operations table, expanded intent detection, custom protocols, updated critical rules (token limits, description field, buffer rules).
- **`Protocols/check-in-protocol.md`**: Major rewrite. Reads insights.md + goals.md + hot-memory.md (not just hot-memory). Step 6 completely replaced: writes to rotating sync buffer instead of directly to vault. Step 9 adds sync prompt (Part 4). Step 10 simplified to system-state update only.
- **`Protocols/entity-protocol.md`**: Added sync mode awareness section, `description` field to all entity templates, Pattern entity type, Glob-based existence check alternative.
- **`Protocols/linking-protocol.md`**: Added `description` field to base frontmatter spec, `tasks-inbox` and `pattern` to valid node_types, step-by-step connected array update procedure.
- **`Protocols/setup-protocol.md`**: Expanded from 9 to 11 steps. Added prerequisites check (Step 1), sync schedule (Step 6), .memspren-config creation, insights.md/goals.md/sync-buffer creation, git init, Logs/ and Notes/Patterns/ folders.
- **`README.md`**: Rewritten with "What it does" section, three-layer memory explanation, "During conversation" and "During sync" subsections, expanded entity types and vault structure, key design decisions section, sync troubleshooting.
- **hot-memory.md token limit** reduced from 800 to 500 (patterns/mindset moved to insights.md).
- **hot-memory.md structure** updated: ACTIVE_PROJECTS, OPEN_THREADS, EVIDENCE_TRAIL, KEY_INSIGHTS, IDEAS_PARKED.

---

## [0.4.0] — 2026-02-28

### Changed
- **Removed Obsidian CLI dependency** — Claude's sandboxed environment cannot access OS-level CLI tools. All vault reads and writes now use Claude's native Read/Write/Edit tools directly on the filesystem.
- **Introduced `.second-brain/` skill folder** — Operational files (`config.md`, `Memory/`) are now stored in a `.second-brain/` directory at the mounted folder root, separate from vault content. This solves the chicken-and-egg problem: Claude always knows where to find `config.md` (at `.second-brain/config.md`) regardless of vault path.
- **`Protocols/setup-protocol.md`**: Removed Step 0 (CLI verification). Step 7 now creates `.second-brain/` and writes `config.md` + `Memory/` there instead of at vault root. Step 9 updates `.second-brain/config.md`.
- **`Protocols/check-in-protocol.md`**: All `Memory/` references updated to `.second-brain/Memory/`. Removed CLI note and all bash command blocks. File operations now described as Read/Write/Edit tool calls.
- **`Protocols/entity-protocol.md`**: Removed all CLI command blocks. Replaced with direct Write/Read/Edit tool instructions. `→ Write to {vault_path}/...` notation used throughout.
- **`Protocols/linking-protocol.md`**: Removed CLI command blocks. Updated Existing Links section now describes read-modify-write pattern using native tools.
- **`SKILL.md`**: Updated session start to load `.second-brain/config.md` first. Added File locations table distinguishing skill folder from vault. Updated Memory loading rules and vault/skill structure diagrams. Removed CLI-specific critical rules.
- **`README.md`**: Removed all CLI prerequisites and setup instructions. Added "How it works — two locations" section explaining the `.second-brain/` separation. Updated vault structure diagram. Rewrote troubleshooting section.

### Removed
- `scripts/check_cli.py`, `scripts/update_connected.py` — no longer needed
- `Reference-Files/obsidian-cli-reference.md` — no longer relevant
- `scripts/scripts.md` — no longer needed

---

## [0.3.0] — 2026-02-28

### Added
- Obsidian CLI integration across all protocols *(superseded by v0.4.0)*
- `scripts/check_cli.py` — CLI + Obsidian availability check
- `scripts/update_connected.py` — YAML `connected:` array updater via CLI
- `Reference-Files/obsidian-cli-reference.md` — CLI cheat sheet
- `README.md`, `CHANGELOG.md`

### Changed
- All protocol files updated with CLI command blocks
- `SKILL.md` updated with CLI rules

---

## [0.2.0] — 2026-02-27

### Added
- **`Protocols/entity-protocol.md`** — governs creation and updating of all six entity types (Project, Idea, Person, Task, Learning, Daily Log); entity existence check; full YAML templates; idea maturity lifecycle; MOC creation (Phase 2)
- **`Protocols/check-in-protocol.md`** — 10-step daily check-in flow with trackable checklist; silent inference pass; targeted follow-up; journaling and lifestyle steps gated on system-state flags (Phase 2)
- **`Protocols/linking-protocol.md`** — dual-link system (YAML `connected:` + body `[[links]]`); full frontmatter spec per node type; minimum links table per entity; orphan note prevention; index update (Phase 2)

### Changed
- **`SKILL.md`**: Expanded reference files table; slimmed entity quick-reference to point to entity-protocol.md; intent detection table updated to reference check-in-protocol.md directly

---

## [0.1.0] — 2026-02-26

### Added
- **`SKILL.md`** — master orchestrator; session start flowchart; intent detection; entity quick-reference; memory loading rules; vault structure; critical rules; what never happens
- **`Protocols/setup-protocol.md`** — 9-step first-run setup flow; vault location capture; check-in time; vision and goals; journaling and lifestyle tracking (Phase 2); full vault folder structure creation; seed files; config.md and Memory file initialization; guided tour; setup_complete flag
