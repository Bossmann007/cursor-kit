# PROJECT.md

Project brain — cursor-kit (Enzo Bossmann working configuration).

## Stack

- Language: Markdown + Python (hooks) + shell/PowerShell installers
- Runtime: Cursor IDE (plugins, hooks, MCP, skills)
- Package manager: n/a (pair with token-engine Python venv)
- Branch: `enzo` is the working base for Enzo's personal/kit setup

## Commands

```bash
# install plugin (Cursor rejects outside symlinks — sync or clone in-place)
rsync -a --delete --exclude '.git/' --exclude '__pycache__/' \
  "$(pwd)/" ~/.cursor/plugins/local/cursor-kit/

# global hooks + hooks.json
./sync-hooks.sh          # Windows: .\sync-hooks.ps1

# global rules (optional if plugin rules already apply)
./sync-rules.sh          # Windows: .\sync-rules.ps1

# per-repo scaffold
./install.sh /ABS/PATH/TO/repo

# tests
python -m unittest discover -s tests
```

## Architecture

Cursor-native kit. Plugin ships skills (`/setup-project`, `/setup-pucpr`,
`/setup-ai-memory`, `/verification-planning`, `/simplify`, `/blindspot-pass`), always-on rules (ponytail, caveman,
token-engine, cbm-first, session-continuity, memory-security), and hooks for
checkpoint + compress hints. Compression lives in [token-engine](https://github.com/Bossmann007/token-engine). Optional long-horizon wiki/handoff: [ai-memory](https://github.com/akitaonrails/ai-memory) companion. Models for subagents come from pstack (`/setup-pstack` → `~/.cursor/rules/pstack-models.mdc`). Durable prefs/facts live in `AGENTS.md` via continual-learning.

## Conventions

- Composition over monolith skills
- No absolute machine paths in committed templates (use placeholders / sync scripts)
- Human docs may be PT; pasteable prompts stay English
- Prefer `/poteto-mode` for non-trivial kit packaging work
- Quality gates for JS/TS are measure-only first (`templates/quality-gates/`)

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-29 | superpowers default; ralph-loop optional; skip OMH | DECISIONS.md Phase 7 |
| 2026-08-29 | Global MCP: token-engine, codebase-memory, context7, notion | Fail-closed compress + CBM |
| 2026-08-29 | Checkpoints in `.cursor/state/checkpoint.json` | Episodic memory without Obsidian |
| 2026-09-12 | Ship rules + hooks.json in plugin on `enzo` | Make kit usable as Enzo working config without machine-only copies |
| 2026-09-17 | Add native `verification-planning` + `simplify`; wire into setup-* | Digest peer skill *form* (Akita/Osmani); not vendored third-party copies |
| 2026-09-17 | Drop unused env skills; ship `blindspot-pass` in plugin only | User never used context-engine/dev-workflow/project-brain/update-checkpoint |
| 2026-09-18 | ai-memory as opt-in companion; kit layers stay episodic SoT; merge-safe sync-hooks | Steal form (wiki/handoff/MCP); keep AGENTS/PROJECT/checkpoint + token-engine |

## Known issues

- Public packaging still young
- Parallel dispatch relies on prompt discipline, not file-lock runtime
- Quality-gates v1 = ESLint JS/TS only

## Current work

See `.cursor/state/checkpoint.json` for live task state.
