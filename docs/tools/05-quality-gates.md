# Quality gates

ESLint (JS/TS) com teto de linhas configurável. Medir antes de apertar severidade.

## Artefatos

- Templates. [`templates/quality-gates/`](../../templates/quality-gates/)
- Prompt medir. [05](../prompts/05-quality-gates-install.md)
- Prompt consertar. [06](../prompts/06-file-size-refactor.md)

## Política

1. Entra como `warn`.
2. Violações visíveis e contadas.
3. Só vira `error` com contagem zero (ou acordo explícito).

## Limite

v1 não empacota Biome nem Ruff. Monorepos exigem adaptação manual no prompt 05. `/setup-project` depth 2 **oferece** gates; não força em repos não-JS.

## Ver também

- [Overview §5](../00-overview.md)
