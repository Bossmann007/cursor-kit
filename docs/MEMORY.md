# Memory

## Files / services

| File / service | Layer | Maintainer |
|----------------|-------|------------|
| `AGENTS.md` | Global/project prefs | Continual Learning plugin + agent |
| `PROJECT.md` | Project brain | Agent on arch changes |
| `.cursor/state/checkpoint.json` | Task state | Agent + stop hook |
| `.cursor/state/failures.jsonl` | Failure lessons | tool-failure hook + agent |
| `.cursor/state/observability.jsonl` | Minimal metrics | stop hook only |
| ai-memory wiki + index (opt-in) | Long-horizon project knowledge | [ai-memory](https://github.com/akitaonrails/ai-memory) companion |

## Intelligence rules

**Store when:**
- User states durable preference ("use pnpm") → `AGENTS.md`
- Architecture decision approved → `PROJECT.md` Decisions
- Live task progress → `checkpoint.json`
- Repeated correction across sessions (Continual Learning bar) → `AGENTS.md`
- Cross-session narrative / handoff / searchable history → ai-memory (when enabled)

**Do not store:**
- Secrets, one-off tasks, branch names, transient errors
- Dual-write every AGENTS bullet into the wiki (no sync daemon)

## Retrieval (before task)

1. AGENTS.md
2. PROJECT.md
3. checkpoint.json
4. failures.jsonl (last 5)
5. If ai-memory MCP is up: pending handoff / brief (wiki is not a second checkpoint)
6. Token-engine compress if bloated

## Continual Learning

Plugin mines `~/.cursor/projects/*/agent-transcripts/` → updates AGENTS.md incrementally.

Runs on `stop` hook after min turns/minutes (plugin config).

## Companion

See [tools/10-ai-memory.md](tools/10-ai-memory.md) and [prompt 07](prompts/07-ai-memory-wire.md).
