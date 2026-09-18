# Memória em camadas

| Camada | Arquivo / serviço | Quem mantém |
|--------|-------------------|-------------|
| Preferências / fatos | `AGENTS.md` | continual-learning + edições manuais |
| Stack / decisions | `PROJECT.md` | humanos + `/setup-project` / agent refresh |
| Tarefa | `.cursor/state/checkpoint.json` | hooks + agent (`task` / `next_action`) |
| Falhas de tool | `.cursor/state/failures.jsonl` | hook postToolUseFailure |
| Long-horizon (opt-in) | ai-memory wiki + índice | companion [ai-memory](https://github.com/akitaonrails/ai-memory) |

## Ordem de leitura

1. `AGENTS.md`
2. `PROJECT.md` Decisions
3. `checkpoint.json` (autoridade do “agora”)
4. `failures.jsonl` (últimas ~5)
5. Se companion ativo: handoff / brief via MCP ai-memory (não substitui o checkpoint)

## Bootstrap

[Prompt 04](../prompts/04-memory-bootstrap.md) (camadas kit) · [Prompt 07](../prompts/07-ai-memory-wire.md) (companion) · fase memória do [playbook](../02-playbook-onboarding.md).

## Limite

Sem Obsidian default. ai-memory é **companion**, não segundo checkpoint. Índice continual-learning só com plugin ativo. Não grave segredos (kit memory-security + sanitize upstream).

## Ver também

- [MEMORY](../MEMORY.md)
- [10 ai-memory](10-ai-memory.md)
- [Overview §7](../00-overview.md)
