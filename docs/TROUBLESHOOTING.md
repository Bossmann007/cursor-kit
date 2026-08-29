# Troubleshooting

## MCP token-engine not loading

- Verify: `C:\Users\enzo.bossmann\token-engine\.venv\Scripts\python.exe` exists
- Run: `pip install -e "C:\Users\enzo.bossmann\token-engine[cursor,dev]"`
- Reload Cursor window

## Hooks not firing

- Check Cursor Settings → Hooks tab
- Paths in `~/.cursor/hooks.json` must be absolute on Windows
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
- Check `.cursor/hooks/state/continual-learning.json`

## Compression not helping

- Run `caveman_stats` MCP
- Benchmark: `token-engine benchmark --check-baseline`

## Secrets in memory

- Rotate key immediately
- Remove from AGENTS.md/checkpoint
- memory-security rule prevents re-storage
