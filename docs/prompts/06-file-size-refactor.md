# Prompt 06. File size refactor (fix after measure)

**PT (wrapper).** Segundo tempo do 05. Quebra arquivos acima do teto por **responsabilidade**, não por contagem cega. Um arquivo por vez, com verificação entre cada um.

**When to use.** Depois do prompt 05, com lista de violações em mãos.

---

## Paste this to the agent (English)

```text
Refactor oversized files reported by cursor-kit quality gates. Fix ONE file per iteration.

Rules:
1. Start from the measured violation list. Do not expand scope to unrelated lint noise.
2. Split by responsibility (UI vs domain vs data access), never by arbitrary line slicing.
3. If there is no natural seam, stop and report "no natural seam" instead of inventing abstractions.
4. After each file: run the project typecheck/tests you can find, and re-run eslint for that path.
5. Prefer small commits (or clear commit messages) per file when the human wants git history.
6. Do not raise MAX_LINES to "make it pass" unless the human explicitly asks.
7. Keep public APIs stable unless the plan approved a break.

Output per file:
## Target
## Split plan
## Files created/changed
## Verify commands + results
## Remaining violations
```
