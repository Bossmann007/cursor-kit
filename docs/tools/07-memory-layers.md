# Memória em camadas

| Camada | Arquivo | Quem mantém |
|--------|---------|-------------|
| Preferências / fatos | `AGENTS.md` | continual-learning + edições manuais |
| Stack / decisions | `PROJECT.md` | humanos + `project-brain` |
| Tarefa | `.cursor/state/checkpoint.json` | hooks + `update-checkpoint` |
| Falhas de tool | `.cursor/state/failures.jsonl` | hook postToolUseFailure |

## Bootstrap

[Prompt 04](../prompts/04-memory-bootstrap.md) ou fase memória do [playbook](../02-playbook-onboarding.md).

## Limite

Sem Obsidian default. Índice continual-learning só existe com plugin ativo. Não grave segredos.

## Ver também

- [MEMORY](../MEMORY.md)
- [Overview §7](../00-overview.md)
