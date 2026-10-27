---
name: emode
description: >
  Enzo's default workflow for real engineering work (feature, bug, refactor, plan,
  review, PR, new tool/MCP/skill): size the task, verify with evidence, ship by PR.
  Use at the start of non-trivial work, on "emode", "fluxo", or when a task spans
  several files or steps. Skip for chat and one-line edits.
disable-model-invocation: false
---

# emode

Short replies. "Done" needs evidence: the project's check output (tests, build, lint).

## 1. Size it

- **Small** (diff fits one sentence): do it, run the check.
- **Medium** (bug, 1-2 files): reproduce, find the root cause (`diagnosing-bugs`), write a failing test, fix, run the check.
- **Large** (multi-file, new feature, a phase): step 2.
- **Decision** (a recommendation, or a change to security, money, the clinic, global config or many folders):
  1. Open the primary source now (README, LICENSE, docs, the code) and cite it (URL or `file:line`); no source, say "não verifiquei" and do not recommend.
  2. Name the one fact that would make it wrong and prove it by running real code (pstack `blast-radius` idea), not by writing it up.
  3. Say how to undo it. Apply to one canary (one bot, one folder) and check it before the rest.
  4. If it gets reverted, add a row to `~/orquestrador/notes/reverts.tsv` (date, what, cause, check added) and turn the cause into a check, script or hook (pstack `correct`), not a new prompt rule.

## 2. Large task

1. Goal: pstack `in-your-own-words` if the ask is vague. New tool or integration: `/prior-art-check`.
2. Spec: interview with `AskUserQuestion`, write `SPEC.md` (files, out of scope, one end-to-end check). Then implement from a fresh context: a new session whose brief is `SPEC.md` (CLI: `/clear`).
3. Implement in pstack `poteto-mode` style, one task at a time, commit per task only if asked.
4. Unattended: `/goal <the check passes>` (tests, build and lint exit 0).

## 3. Verify

- Run the check and show the output.
- Large change: fresh-context review with `/code-review`. Tell the reviewer to flag only correctness or requirement gaps, not style.
- UI: screenshot and compare in the browser.

## 4. Ship

PR with evidence (`pr` skill: what changed, how it was verified). Never merge unless asked.

## 5. Context

Fresh context between unrelated tasks (new session; CLI: `/clear`). After two failed corrections: fresh context and rewrite the prompt. Use subagents for investigation.

## pstack skills

pstack skills (`poteto-mode`, `in-your-own-words`, ...) set `disable-model-invocation: true`, so the `Skill` tool refuses them. The user can type `/pstack:<name>`; the agent instead reads `docs/harness/claude-code.md` once, then `skills/<name>/SKILL.md`, from the folder in `installPath` of `pstack@cursor-plugins` in `~/.claude/plugins/installed_plugins.json` (the active version; older cache folders may remain), and follows it.
