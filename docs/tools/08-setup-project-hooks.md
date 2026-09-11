# `/setup-project` e hooks

## `/setup-project`

Orquestrador per-repo neste plugin. Scaffold idempotente, reparo global se MCP/hooks/pstack faltarem, delega Matt Pocock e pstack. Não implementa features do app.

Skill. [`skills/setup-project/SKILL.md`](../../skills/setup-project/SKILL.md)  
Camadas. [`references/layers.md`](../../skills/setup-project/references/layers.md)

Depth 2 deve oferecer quality gates (JS/TS) e apontar o [playbook](../02-playbook-onboarding.md).

## Hooks

Fonte. `cursor-kit/hooks/` → `sync-hooks.sh` / `sync-hooks.ps1` → `~/.cursor/hooks/`.

Eventos típicos. sessionStart, postToolUse, postToolUseFailure, afterFileEdit, stop (checkpoint).

## Limite

Hooks quebrados com path de máquina no repo são bug. Prefira sync global a hooks project-local com absolutos.

## Ver também

- [Instalação](../01-installation.md)
- [ARCHITECTURE](../ARCHITECTURE.md)
