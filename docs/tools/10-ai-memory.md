# ai-memory (companion)

Memória de longo prazo **fora** do Cursor-only. Wiki markdown + índice SQLite, handoffs tipados, captura silenciosa. Não substitui AGENTS / PROJECT / checkpoint.

Upstream. [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory)  
Instalação kit. skill `/setup-ai-memory` ou `scripts/install-ai-memory.sh`  
Camadas. [07 memory-layers](07-memory-layers.md) · [MEMORY](../MEMORY.md)

## O que o kit mantém vs o que o companion acrescenta

| Kit (obrigatório no stack) | ai-memory (opt-in) |
|----------------------------|--------------------|
| `AGENTS.md` prefs/fatos | Wiki de sessão consolidada |
| `PROJECT.md` Decisions | Search FTS / entities |
| `.cursor/state/checkpoint.json` | Handoff cross-agent / cross-machine |
| `failures.jsonl` | Capture via hooks → consolidate |
| token-engine + CBM | MCP `ai-memory` (recall / status) |

## Default macOS (kit)

1. Binary nativo (release tarball), não Docker
2. LaunchAgent em login (`~/Library/LaunchAgents/…`)
3. Loopback `127.0.0.1:49374`, zero-LLM ok
4. `ai-memory install-mcp --client cursor --apply`
5. `ai-memory install-hooks --agent cursor --apply`

Detalhe upstream: [docs/macos.md](https://github.com/akitaonrails/ai-memory/blob/main/docs/macos.md).

## Coexistência de hooks

`sync-hooks.sh` / `.ps1` é **merge-safe**: atualiza só comandos do kit; preserva entradas companion (ex. `ai-memory hook …`, `rtk`).

## Verificação rápida

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:49374/mcp   # expect 405
ai-memory status   # or MCP memory_status
```

Reload Cursor MCP depois do install.

## Não fazer

- Fork / vendor do binário Rust no cursor-kit
- Dual-write automático AGENTS → wiki
- Exigir ai-memory em depth 1 do `/setup-project`
