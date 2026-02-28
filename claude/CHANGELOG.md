# Changelog

All notable changes to the Managing Second Brain skill are documented here.

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
