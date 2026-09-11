# token-engine

Compressão fail-closed de outputs de ferramenta e contexto. MCP `caveman_compress`, `caveman_retrieve`, `caveman_stats`, analyze/sandbox.

## Onde vive

Repo. [Bossmann007/token-engine](https://github.com/Bossmann007/token-engine)  
Docs. `docs/CURSOR.md`, `docs/API.md` no engine.  
MCP global. `~/.cursor/mcp.json` (placeholders em [`mcp.json.template`](../../mcp.json.template)).

## Hooks

`postToolUse` do kit pode notar compressões grandes. A chamada MCP continua sendo do agente.

## Limite

Sem venv/MCP corretos, o pilar some. “Fale como caveman” não substitui compressão de log/JSON.

## Ver também

- [Overview §3](../00-overview.md)
- [BENCHMARKS](../BENCHMARKS.md)
