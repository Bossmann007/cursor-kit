# Prompt 03. Parallel-safe dispatch

**PT (wrapper).** Divide tarefas em ondas paralelas sem dois agentes no mesmo arquivo. No Cursor a garantia é **disciplinar** (prompt), não um runtime que bloqueia overlap. Seja honesto se não der para paralelizar.

**When to use.** Várias tarefas independentes após um plano aprovado.

---

## Paste this to the agent (English)

```text
Split the approved task list into parallel-safe waves for Cursor subagents.

Hard rules:
1. Two tasks in the SAME wave must not touch overlapping file paths (including renames).
2. No subagent commits. Only the parent session commits, in order, after the wave finishes.
3. Each task card must list: goal, allowed files, forbidden files, model tier hint (cheap vs strong), verify command.
4. If two pieces cannot be separated cleanly, keep them serial in later waves. Say so explicitly.
5. Prefer fewer correct waves over aggressive parallelism.

Output:
## Wave 1
### Task …
## Wave 2
…
## Serial leftovers
## Commit plan (parent only)
```
