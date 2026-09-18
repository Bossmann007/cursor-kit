# `/setup-project` e hooks

## `/setup-project`

Orquestrador per-repo neste plugin. Scaffold idempotente, reparo global se MCP/hooks/pstack faltarem, delega Matt Pocock e pstack. Não implementa features do app.

Skill. [`skills/setup-project/SKILL.md`](../../skills/setup-project/SKILL.md)  
Camadas. [`references/layers.md`](../../skills/setup-project/references/layers.md)

Depth 2 deve oferecer quality gates (JS/TS) e apontar o [playbook](../02-playbook-onboarding.md).

## Hooks

Fonte. `cursor-kit/hooks/*.py` + `hooks.json.template` → `sync-hooks.sh` / `sync-hooks.ps1` → `~/.cursor/hooks/` e `~/.cursor/hooks.json`.

Plugin path. `hooks/hooks.json` usa `${CURSOR_PLUGIN_ROOT}` quando o cursor-kit está ligado como plugin local.

Eventos. sessionStart, postToolUse, postToolUseFailure, afterFileEdit, stop (checkpoint).

## Rules

Fonte. `cursor-kit/rules/*.mdc` (plugin) e opcionalmente `sync-rules.sh` → `~/.cursor/rules/`. Inclui ponytail, caveman, token-engine, cbm-first, session-continuity, memory-security. pstack: seed em `templates/pstack/` + `/setup-pstack`.

`sync-hooks.sh` / `.ps1` é **merge-safe**: atualiza só hooks do kit; preserva companions (ai-memory, rtk). Ver [10 ai-memory](10-ai-memory.md).

## Limite

Hooks quebrados com path de máquina no repo são bug. Prefira sync global a hooks project-local com absolutos.

## Ver também

- [Instalação](../01-installation.md)
- [ARCHITECTURE](../ARCHITECTURE.md)
