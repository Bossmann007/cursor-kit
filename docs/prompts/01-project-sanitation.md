# Prompt 01. Project sanitation

**PT (wrapper).** Faxina inicial. Medir antes de agir. Separar correção mecânica de decisão humana. Cole o bloco em inglês no agente.

**When to use.** Repo bagunçado, muitos TODOs, arquivos mortos, inconsistência óbvia. Não use para feature nova.

---

## Paste this to the agent (English)

```text
You are sanitizing this repository. Do NOT implement features.

Rules:
1. Measure first. List concrete findings with file paths and severity (blocker / should-fix / defer).
2. Never invent severity. If unsure, mark "needs-human".
3. Split work into:
   - Mechanical fixes (safe, reversible, no behavior change)
   - Decisions that need human approval before touching code
4. Do not start mechanical fixes until the human approves the list.
5. Do not delete files without listing them first.
6. Prefer idempotent steps. Do not clobber filled AGENTS.md or PROJECT.md.
7. If token-engine MCP is available, compress large tool outputs before keeping them in context.

Output format:
## Inventory
## Proposed mechanical fixes
## Needs human decision
## Out of scope
```
