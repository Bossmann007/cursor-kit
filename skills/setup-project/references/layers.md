# Layers — global vs per-repo

Use this when deciding what to write. Prefer repair over duplicate.

## Global (`~/.cursor/`) — shared across projects

| Asset | Expected path | Role |
|-------|---------------|------|
| Rules | `~/.cursor/rules/*.mdc` | ponytail, caveman, token-engine, cbm-first, session-continuity, pstack-models, … |
| MCP | `~/.cursor/mcp.json` | token-engine, codebase-memory, context7, notion (and others) |
| Hooks | `~/.cursor/hooks.json` + `~/.cursor/hooks/` | sessionStart, compress, failures, track-edits, checkpoint-stop |
| User skills | `~/.cursor/skills/` | Matt Pocock + project-brain, context-engine, … |
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

## External sources (do not fork into the skill body)

- Templates: `$CURSOR_KIT` → `~/cursor-kit` or this plugin repo root
- Compression: [token-engine](https://github.com/Bossmann007/token-engine)
- Models: `/setup-pstack` → `~/.cursor/rules/pstack-models.mdc`
- Issue/domain: `/setup-matt-pocock-skills`
- CI/PR workflows: plugin `cursor-team-kit`
- AGENTS.md mining: plugin `continual-learning`
