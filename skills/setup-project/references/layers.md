# Layers — global vs per-repo

Use this when deciding what to write. Prefer repair over duplicate.

## Global (`~/.cursor/`) — shared across projects

| Asset | Expected path | Role |
|-------|---------------|------|
| Rules | plugin `rules/` and/or `~/.cursor/rules/*.mdc` | ponytail, caveman, token-engine, cbm-first, session-continuity, memory-security, pstack-models |
| MCP | `~/.cursor/mcp.json` | token-engine, codebase-memory, context7, notion; **ai-memory** companion (repair in `/setup-project` pré-check / §6c) |
| Hooks | plugin `hooks/hooks.json` and/or `~/.cursor/hooks.json` + `~/.cursor/hooks/` | sessionStart, compress, failures, track-edits, checkpoint-stop; companions (ai-memory, rtk) preserved by merge-safe `sync-hooks` |
| User skills | `~/.cursor/skills/` | Matt Pocock + `find-skills` — **not** plugin-shipped kit skills when plugin is installed |
| Kit plugin skills | `~/.cursor/plugins/local/cursor-kit/skills/` | `setup-project`, `setup-pucpr`, `setup-ai-memory`, `verification-planning`, `simplify`, `blindspot-pass` (source of truth on desktop) |
| Plugins | Cursor plugin UI | pstack, cursor-team-kit, continual-learning, this cursor-kit plugin |

Global repair (phase 0) only when something above is missing or broken. Do not copy global rules into the target repo.

## Per-repo — created/updated by this skill

| Asset | Path | Role |
|-------|------|------|
| Durable memory | `AGENTS.md` | Continual Learning contract (`## Learned User Preferences`, `## Learned Workspace Facts`) |
| Project brain | `PROJECT.md` | Stack, commands, architecture, decisions table |
| Ephemeral state | `.cursor/state/` | checkpoint.json, session.json, failures.jsonl |
| Ignore noise | `.gitignore` | Ignore state files (kit snippet) |
| Eng. skills config | `docs/agents/*` | issue-tracker, domain, optional triage-labels |
| Domain docs | `CONTEXT.md` + `docs/adr/` | Created lazily by domain-modeling unless interview depth 2 asks to scaffold empty dirs |

Long-horizon wiki (opt-in) lives in the **ai-memory** data dir / server — not under the repo `.cursor/state/`. See `/setup-ai-memory`.

## External sources (do not fork into the skill body)

- Templates: `$CURSOR_KIT` → `~/cursor-kit` or this plugin repo root
- Compression: [token-engine](https://github.com/Bossmann007/token-engine)
- Long-horizon memory: [ai-memory](https://github.com/akitaonrails/ai-memory) via `/setup-ai-memory`
- Models: `/setup-pstack` → `~/.cursor/rules/pstack-models.mdc`
- Issue/domain: `/setup-matt-pocock-skills`
- CI/PR workflows: plugin `cursor-team-kit`
- AGENTS.md mining: plugin `continual-learning`
