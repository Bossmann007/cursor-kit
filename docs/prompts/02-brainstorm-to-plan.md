# Prompt 02. Brainstorm to plan

**PT (wrapper).** Transforma pedido aberto em plano revisável. Perguntas antes de código. Cole o bloco EN no agente (ou use `/poteto-mode` / superpowers se já cobrir).

**When to use.** Feature ou mudança não trivial sem spec clara.

---

## Paste this to the agent (English)

```text
Turn the user's request into an implementation plan. Do NOT write production code yet.

Process:
1. Restate the goal in one sentence.
2. Ask clarifying questions only where a wrong assumption would waste real work. Cap at 5 questions. If the user already answered in-thread, do not re-ask.
3. List constraints you inferred (stack, files, non-goals).
4. Produce a numbered plan. Each step must include:
   - Intent
   - Files likely touched
   - How we will verify (command or observable behavior)
5. Call out risks and open decisions for the human.
6. Stop and wait for approval before implementing.

If /poteto-mode or superpowers skills are available, follow them instead of inventing a parallel process. Still produce the written plan artifact above.
```
