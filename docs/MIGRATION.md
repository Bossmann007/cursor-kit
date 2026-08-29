# Migration notes

## From Hermes / Claude / dotagents

| Old | New | Action |
|-----|-----|--------|
| Hermes MEMORY.md | AGENTS.md + Continual Learning | Do not copy secrets |
| Hermes skills bulk | Curated ~/.cursor/skills | Only pucpr-canvas migrated |
| Claude ponytail | ~/.cursor/rules/ponytail.mdc | Done |
| Claude rtk | token-engine postToolUse | Done |
| dotagents | cursor-kit | This repo |
| Mafioso harness | ARCHIVED | Not migrated |
| MedOS | REMOVED | Never migrate |

## Windows setup checklist

1. Global `~/.cursor/mcp.json` (4 servers)
2. Global `~/.cursor/hooks.json`
3. token-engine venv at fixed path
4. Reload Cursor
5. `install.ps1` per project

## Deprecation

- `docs/HARNESS_PROMPT.md` in token-engine — deleted
- `~/.agents/skills/` — deprecated, use ~/.cursor/skills
