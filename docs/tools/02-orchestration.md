# Orquestração e subagentes

Sessão principal planeja e delega. Subagentes (Task) executam escopo estreito. Commit na sessão pai.

## No Cursor

- Task / subagents nativos.
- **pstack** (`/setup-pstack`, `pstack-models.mdc`) para papéis e modelos.
- **`/poteto-mode`** swarm/arena quando o playbook pedir fan-out.
- Prompt. [parallel-safe dispatch](../prompts/03-parallel-safe-dispatch.md).

## Limite (honesto)

Não há runtime que impeça dois agentes de editarem o mesmo arquivo. A segurança da “onda” é regra de prompt + revisão humana. Toolkits Claude com protocolo mais rígido ainda ganham neste eixo.

## Ver também

- [Overview §1](../00-overview.md)
