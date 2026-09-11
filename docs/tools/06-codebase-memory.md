# codebase-memory (CBM)

MCP de grafo estrutural. Símbolos, callers/callees, snippets. Regra `cbm-first`. preferir grafo a varrer arquivo inteiro.

## Uso típico

`list_projects` → `index_repository` se preciso → `search_graph` / `trace_path` / `get_code_snippet`.

## Limite

Não gera HTML visual de comunidades (diferente de Graphify). Cobertura é best-effort. Confirme `check_index_coverage` antes de afirmações fortes.

## Ver também

- [Overview §6](../00-overview.md)
- [CONTEXT](../CONTEXT.md)
