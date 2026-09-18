# Context pipeline

Pipeline (rules + MCP — no separate `context-engine` skill):

```text
USER TASK → PROJECT.md → AGENTS.md → checkpoint → failures
         → codebase-memory (graph) → token-engine (compress) → agent
```

## Token budget

- Never load full transcript into reasoning
- Never re-read unchanged files whole
- compress tool output >500 tokens
- MCP compact_tools when 20+ tool defs

## Code exploration

CBM-first rule: `search_graph` → `get_code_snippet` → Read (last resort)
