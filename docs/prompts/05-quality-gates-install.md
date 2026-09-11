# Prompt 05. Quality gates install (measure only)

**PT (wrapper).** Copia templates ESLint do kit, adapta paths, roda lint e **só lista** violações. Não refatora. `MAX_LINES` default 350.

Fonte. `templates/quality-gates/` neste repo.

**When to use.** Repo JS/TS sem gate de tamanho/arquivo ou lint de arquitetura.

---

## Paste this to the agent (English)

```text
Install cursor-kit quality gates into this repo and MEASURE only. Do not fix violations.

Kit path (resolve one):
- ~/cursor-kit/templates/quality-gates/
- or the plugin/repo root that contains templates/quality-gates/

Steps:
1. Confirm this is a JS/TS project (package.json). If not, stop and say N/A.
2. Copy eslint/rules into the project (e.g. eslint-rules/ or .eslint-rules/). Copy eslint.config.mjs.example as a starting config ONLY if the repo has no ESLint flat config; otherwise merge the max-file-lines rule into the existing config.
3. Set MAX_LINES from the user or default 350. Keep the rule severity at "warn" unless the human asked for error.
4. Install eslint + @eslint/js if missing (do not upgrade the world casually).
5. Run measure (prefer the verify.mjs.example pattern or `MAX_LINES=… npx eslint .`). Capture the list of files over the limit and counts.
6. Do NOT refactor, delete, or "quick fix" anything.
7. Report:
   ## Config changes
   ## Command run
   ## Violations (path + count)
   ## Next step
   Tell the human to run docs/prompts/06-file-size-refactor.md only if they want fixes.
```
