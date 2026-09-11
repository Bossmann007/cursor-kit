# Quality gates (ESLint)

Peça de 1ª classe do cursor-kit para repos **JS/TS**. Medir ≠ consertar.

## Ideia

1. Instalar regras + config de exemplo.
2. Rodar lint e **listar** violações (`MAX_LINES` default 350, configurável).
3. Só depois promover ou refatorar (prompt 06), um arquivo por vez.

Não ligue regra nova como erro bloqueante no dia 1 se a base já está suja. Meça, zere, então aperte.

## Layout

```text
templates/quality-gates/
  README.md                 ← você está aqui
  eslint/
    eslint.config.mjs.example
    rules/
      max-lines.cjs
      index.cjs
    verify.mjs.example
```

## Limites (honestos)

- v1 = ESLint flat config. Biome e Ruff não vêm template.
- Não adapta monorepos complexos sozinho. O prompt 05 deve ajustar paths.
- Teto de linhas é heurística de legibilidade, não prova de design.

## Fluxo

1. [docs/prompts/05-quality-gates-install.md](../../docs/prompts/05-quality-gates-install.md) — instalar e medir.
2. [docs/prompts/06-file-size-refactor.md](../../docs/prompts/06-file-size-refactor.md) — quebrar arquivos grandes.
