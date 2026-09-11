# Playbook de onboarding

Do zero até um repo real com o stack Cursor rodando. Tempo alvo. cerca de 1–2 horas na primeira vez.

Pré-requisito. [Instalação](01-installation.md) (clones, venv, MCP, hooks, plugin).

## Passo 1. Abrir o Cursor no lugar certo

- **Repo existente.** Abra a pasta do projeto como workspace.
- **Repo novo.** Crie a pasta, `git init`, abra no Cursor (ou deixe `/setup-project` criar e peça `move_agent_to_root`).

## Passo 2. Rodar `/setup-project`

No chat do agente:

```text
/setup-project
```

Responda.

1. Modo. existing vs new (default. existing se já há root).
2. Interview. **1 minimal** ou **2 completo**.

Depth 2 oferece. preencher `PROJECT.md`, index CBM, lembrar poteto/pstack, e **oferecer quality gates** (JS/TS) apontando o playbook/prompts. Não reinventa matt-pocock nem pstack. Delega.

O que deve existir depois (idempotente se já existir conteúdo).

- `AGENTS.md` (seções Learned *)
- `PROJECT.md`
- `.cursor/state/checkpoint.json`
- ignore de state no `.gitignore`
- `docs/agents/*` se a fase Matt rodou

## Passo 3. Conferir MCP e compressão

No chat:

```text
Use caveman_stats or compress a short sample with the token-engine MCP.
```

Se falhar. volte à [instalação §2](01-installation.md) e [TROUBLESHOOTING](TROUBLESHOOTING.md). Sem MCP saudável o pilar de tokens não existe.

## Passo 4. Memória viva

1. Escreva uma linha real em `PROJECT.md` → Decisions (data, decisão, porquê).
2. Peça ao agente. “Cite a última Decision de PROJECT.md.”
3. Rode o skill `update-checkpoint` (ou peça) com `task` + `next_action` preenchidos.

## Passo 5. Quality gates (só se o repo for JS/TS)

Depth 2 ou manual.

1. Cole o [prompt 05. medir](prompts/05-quality-gates-install.md) (instala templates, **não conserta**).
2. Olhe a lista de violações.
3. Só depois, se quiser, [prompt 06. consertar](prompts/06-file-size-refactor.md) arquivo a arquivo.

Outras linguagens. documente o gate no `PROJECT.md`; templates v1 não cobrem.

## Passo 6. Smoke A / B / C

**A. Continue.** Checkpoint com `task` e `next_action` → feche o chat/janela → diga `continue` / `retomar` → o agente deve retomar pelo state.

**B. Decision.** A Decision do passo 4 deve ser citada sem alucinar outra.

**C. Failure.** Force uma falha de tool duas vezes (comando inválido). Confira `.cursor/state/failures.jsonl`. Na próxima tentativa o agente deve mudar de abordagem.

## Passo 7. Primeiro trabalho disciplinado

Pedido não trivial.

```text
/poteto-mode
```

(ou superpowers se for o default da casa). Plano antes de código. Compressão em outputs grandes. CBM antes de varrer a árvore inteira.

## Checklist “estranho em 2h”

- [ ] MCP token-engine enabled
- [ ] Hooks sincronizados
- [ ] `/setup-project` rodou sem clobber de AGENTS/PROJECT preenchidos
- [ ] Sabe achar [overview](00-overview.md) e um [prompt](prompts/)
- [ ] JS/TS. quality gates medidos (ou N/A documentado)
- [ ] Smoke A ou B ok
- [ ] Entende. tokens = token-engine, não “fale curto”

## Depois

- Cards. [docs/tools/](tools/)
- Referência. [ARCHITECTURE](ARCHITECTURE.md), [MEMORY](MEMORY.md), [CONTEXT](CONTEXT.md)
- CI/PR. plugin cursor-team-kit
