# Troubleshooting

## MCP token-engine not loading

- Clone/install [token-engine](https://github.com/Bossmann007/token-engine) and create a venv:
  - macOS/Linux: `~/token-engine/.venv/bin/python`
  - Windows: `~\token-engine\.venv\Scripts\python.exe`
- Run: `pip install -e "~/token-engine[cursor,dev]"` (adjust path)
- Point `~/.cursor/mcp.json` `token-engine.command` at that Python; set `PYTHONPATH` to `…/token-engine/src`
- Reload Cursor window

## Hooks not firing

- Check Cursor Settings → Hooks tab
- Prefer global hooks from this kit (`sync-hooks.sh` / `sync-hooks.ps1`)
- On Windows, paths in `~/.cursor/hooks.json` may need to be absolute
- Restart Cursor after editing hooks.json

## Checkpoint empty on continue

- Agent must set `task` and `next_action` in checkpoint.json
- Hooks only auto-track `files`
- Run skill `update-checkpoint` manually once

## Notion MCP OAuth

- First connect prompts browser login
- Ensure Notion integration has workspace access

## Continual Learning not updating AGENTS.md

- Plugin must be enabled
- Needs min turns/minutes before stop hook triggers
- Check `.cursor/hooks/state/continual-learning-index.json` (or legacy `continual-learning.json`)

## Local plugin cursor-kit not loading / skills missing

- Check Cursor Plugins log for:
  `loadUserLocalPlugin cursor-kit rejected: symlink target … is outside …/plugins/local`
- Fix: real directory under `~/.cursor/plugins/local/cursor-kit` (rsync or clone in-place). See [01-installation](01-installation.md) §4.
- Fallback (desktop only): `~/.cursor/skills/setup-project` + `setup-pucpr` symlinks still work without the plugin.
- Reload Window after fixing. Projects/Cloud: laptop skills do not appear unless environment install copies them.

## Compression not helping

- Run `caveman_stats` MCP
- Benchmark: `token-engine benchmark --check-baseline`

## Secrets in memory

- Rotate key immediately
- Remove from AGENTS.md/checkpoint
- memory-security rule prevents re-storage
