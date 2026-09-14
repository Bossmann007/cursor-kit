# Decisions locked — 2026-08-29

User approved Phase 7 build. Reference for future sessions.

| # | Question | Decision |
|---|----------|----------|
| 1 | Hermes WhatsApp | User already handled |
| 2 | superpowers vs OMH vs ralph-loop | **superpowers default**, ralph-loop optional, **skip OMH** |
| 3 | pucpr-canvas | **Migrated** to `~/.cursor/skills/pucpr-canvas` |
| 4 | ponytail+caveman global | **Yes** — all projects |
| 5 | MCP global | **Yes** — token-engine, codebase-memory, context7, notion |
| 6 | Notion | **Integrate** via MCP OAuth |
| 7 | Observability | **Minimal tokens** — caveman_stats on demand only |
| 8 | Checkpoints | **Yes** — `.cursor/state/checkpoint.json` |
| 9 | cursor-kit | **Yes** — `~/cursor-kit` replaces dotagents |
| 10 | Plugins | User already configured — leave as-is |

## Built in Phase 7

- `~/.cursor/rules/` — ponytail, caveman, token-engine, cbm-first, session-continuity
- `~/.cursor/mcp.json` — 4 MCP servers
- `~/.cursor/hooks.json` — sessionStart, postToolUse, afterFileEdit
- `~/.cursor/hooks/token-engine-session.py`, `compress-tool-output.py`
- `~/.cursor/skills/pucpr-canvas/SKILL.md`
- `~/cursor-kit/` — template repo
- `token-engine/docs/CURSOR-ENV.md` (replaced HARNESS_PROMPT.md)
- `token-engine/AGENTS.md`, `PROJECT.md`, checkpoint scaffold

## Built in Phase 7–29

- Global hooks: sessionStart, postToolUse, postToolUseFailure, afterFileEdit, stop
- `cursor_state.py`: checkpoint, session, failures, minimal observability
- Skills: dev-workflow, update-checkpoint, project-brain, context-engine
- Rules: explainability, memory-security
- cursor-kit docs: ARCHITECTURE, MEMORY, WORKFLOWS, etc.
- Tests: cursor-kit/tests/test_cursor_state.py

## Next (user action)

1. Reload Cursor window
2. Connect Notion MCP (OAuth prompt)
3. `python -m unittest discover -s ~/cursor-kit/tests`

## Built on branch `enzo` (2026-09-12)

- Plugin ships `rules/` + `hooks/hooks.json` (usable without machine-only copies)
- `hooks.json.template` + sync-hooks writes `~/.cursor/hooks.json`
- `sync-rules.sh` / `.ps1` mirrors rules + seeds pstack `inherit-parent` example
- Kit `PROJECT.md` documents Enzo working configuration
