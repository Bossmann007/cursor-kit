# Visão geral

Isto é um **fluxo Cursor**, não uma lista de plugins. Cada peça cobre uma falha que as outras não cobrem. Sozinhas são conveniências. Juntas formam o loop.

Leia isto antes de instalar. Os cards em [`tools/`](tools/) e o [playbook](02-playbook-onboarding.md) assumem estes sete pilares.

## 1. Orquestração, não implementação solo

A sessão principal planeja e decide. Trabalho pesado vai para subagentes (Task / pstack) com escopo estreito. Quem committa em ordem é a sessão principal.

No Cursor isso é nativo via subagents e skills (`/poteto-mode`, team-kit). O protocolo de “ondas” sem colisão de arquivo ainda é **mais fraco** que toolkits Claude focados nisso. Use o [prompt de dispatch paralelo](prompts/03-parallel-safe-dispatch.md) e não finja garantia estrutural.

Ver [orquestração](tools/02-orchestration.md).

## 2. Plan → ship

Código é a última etapa. Brainstorm → plano → implementação → revisão. Superpowers e `/poteto-mode` impõem a disciplina. `/setup-project` só prepara o terreno.

Ver [plan-ship](tools/01-plan-ship.md) e [WORKFLOWS](WORKFLOWS.md).

## 3. Economia de tokens (token-engine)

Saídas grandes de ferramentas enchem o contexto. O **token-engine** comprime de forma fail-closed (só substitui se menor e com checks). Hooks avisam; o agente chama `caveman_compress` quando o output é grande.

Isto é a vantagem deste stack frente a “fale menos” ou proxies CLI não publicados.

Ver [token-engine](tools/03-token-engine.md).

## 4. Personas compostas

**Ponytail** governa o que se constrói (escada YAGNI). **Caveman** governa como se fala (menos enchimento). Independentes de propósito.

Ver [ponytail + caveman](tools/04-ponytail-caveman.md).

## 5. Quality gates como migração

Lint novo não pula de off para erro bloqueante. Medir → zerar avisos → promover. Neste kit a peça de 1ª classe é **ESLint** (JS/TS) com teto de linhas configurável. Biome e Ruff ficam como nota, não como template v1.

Medir e consertar são prompts **separados**.

Ver [quality gates](tools/05-quality-gates.md).

## 6. Grafo / codebase-memory

Antes de grep cego, consulte o grafo estrutural (CBM). Não é um HTML visual tipo Graphify. É MCP de símbolos e caminhos.

Ver [codebase-memory](tools/06-codebase-memory.md).

## 7. Memória em camadas

| Camada | Onde | Papel |
|--------|------|--------|
| Semântica | `AGENTS.md` | Preferências e fatos estáveis (continual-learning) |
| Decisão / stack | `PROJECT.md` | Semi-estático; tabela Decisions |
| Episódica | `.cursor/state/checkpoint.json` | Tarefa atual |
| Falha | `.cursor/state/failures.jsonl` | Evitar repetir a mesma abordagem |

Sem Obsidian obrigatório. Notion MCP é opcional se já estiver no global.

Ver [memory layers](tools/07-memory-layers.md) e [MEMORY](MEMORY.md).

## Como as peças se encaixam

```text
Instalar kit + token-engine
    → /setup-project (repo)
    → plan (superpowers / poteto)
    → implementar (subagents + CBM + compress)
    → quality gates (medir; depois consertar)
    → ship (team-kit)
    → memória (checkpoint + continual-learning)
```

## Limites

- Empacotamento público ainda jovem (pouca prova social).
- Ondas paralelas dependem de disciplina do prompt, não de runtime que bloqueia overlap de arquivo.
- Quality gates v1 = JS/TS (ESLint). Outras linguagens não vêm templates.
- Continual-learning precisa do plugin habilitado e tempo mínimo de sessão.
- Paths de MCP são placeholders. Máquina absoluta no repo é bug.

## Próximo passo

[Instalação](01-installation.md) → [Playbook](02-playbook-onboarding.md).
