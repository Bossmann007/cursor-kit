---
name: enzo-mode
description: >
  Enzo's working mode: the default workflow for any non-trivial engineering task
  (feature, bug, refactor, plan, review, PR, new tool/MCP/skill). Routes to the
  right skills, decides when to escalate to poteto-mode, and keeps tokens low.
  Use at the start of real engineering work, on "enzo-mode", "fluxo", "qual o
  workflow", or when a task spans several files or steps. Do NOT use for PUCPR
  coursework (teach step by step instead), casual chat, or one-line edits.
disable-model-invocation: false
---

# Enzo mode

Style: terse, direct, Portuguese in chat, English in code. Smallest change that works. Never claim done without evidence. Do not commit or push unless asked; ship via PR.

## 0. Gate (10 seconds)

- Coursework (PUCPR, PBL, entrega, prova, slides): STOP this skill. Teach step by step, never write the student's deliverable. Use `digest-files` for PDFs.
- One-line / mechanical edit: just do it.
- Otherwise continue. Name the task size: small, medium, large.

## 1. Route by task

| Task | Do |
|---|---|
| Bug / failing test / odd behavior | `systematic-debugging` first (root cause), fix, then prove |
| New tool, MCP, skill, integration | `/prior-art-check` before designing |
| Feature, medium | `brainstorming` -> `writing-plans` -> implement with `test-driven-development` |
| Feature, large or multi-file | same, but run the implementation through `/poteto-mode` (see 2) |
| Plan too big for one session | `wayfinder` |
| Unclear spec or risky design | `brainstorming` (or `/prior-art-check`), record decisions with `domain-modeling` |
| Docs, PR text | `pr` for PR bodies; unslop prose |
| After a long session | `retro` |

## 2. When to escalate to poteto-mode

Use `/poteto-mode` (subagent runs on Sonnet) only if at least one holds: changes span >3 files, architecture or data-model decision, auth/security/trust boundary, or a bug that survived one honest debugging pass. Otherwise stay inline: poteto-agent is expensive. For the hardest tasks, tell the user to run `/model opus` first.

## 3. Prove it

Before "done": `verification-planning` for non-trivial claims, then `verification-before-completion` (run the check, show the output). Large change: `/code-review`, then `blindspot-pass`.

## 4. Ship

Ask for the PR (`commit-commands:commit-push-pr`); CI runs on the PR. Squash nothing the user did not ask for. Resolve merge conflicts with `resolving-merge-conflicts`.

## 5. Token hygiene

- Brief lives in AGENTS.md / PROJECT.md / ai-memory pages, not pasted each time. Ask `memory_query` before asking the user for known context.
- One task per session: suggest `/clear` when the task changes; no endless `/goal` loops; delegate with "reply in <=10 lines".
- Large tool output: summarize, do not paste. Explore code via codebase-memory before reading whole files.

## 6. Memory

Long-term memory is ai-memory. Run `ai-memory-curate` when asked or weekly. Never write secrets anywhere.
