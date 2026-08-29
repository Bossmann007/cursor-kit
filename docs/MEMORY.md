# Memory

## Files

| File | Layer | Maintainer |
|------|-------|------------|
| `AGENTS.md` | Global/project prefs | Continual Learning plugin + agent |
| `PROJECT.md` | Project brain | Agent on arch changes |
| `.cursor/state/checkpoint.json` | Task state | Agent + stop hook |
| `.cursor/state/failures.jsonl` | Failure lessons | tool-failure hook + agent |
| `.cursor/state/observability.jsonl` | Minimal metrics | stop hook only |

## Intelligence rules

**Store when:**
- User states durable preference ("use pnpm")
- Architecture decision approved
- Repeated correction across sessions (Continual Learning bar)

**Do not store:**
- Secrets, one-off tasks, branch names, transient errors

## Retrieval (before task)

1. AGENTS.md
2. PROJECT.md
3. checkpoint.json
4. failures.jsonl (last 5)
5. Token-engine compress if bloated

## Continual Learning

Plugin mines `~/.cursor/projects/*/agent-transcripts/` → updates AGENTS.md incrementally.

Runs on `stop` hook after min turns/minutes (plugin config).
