# AGENTS.md — cursor-kit

## Learned User Preferences

- Cursor-only dev environment (macOS primary; Windows scripts still shipped)
- Prefer minimal tokens: caveman_stats on demand only
- Prefer `/setup-project` for new or existing repos on this stack

## Learned Workspace Facts

- Kit lives at `~/cursor-kit` → `~/.cursor/repos/cursor-kit`
- Pairs with [token-engine](https://github.com/Bossmann007/token-engine) at `~/token-engine`
- Hooks source of truth: `cursor-kit/hooks/` synced to `~/.cursor/hooks` via `sync-hooks.sh` / `sync-hooks.ps1`
- Plugin entry: `.cursor-plugin/plugin.json` + skill `setup-project`
