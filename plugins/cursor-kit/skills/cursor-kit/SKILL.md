---
name: cursor-kit
description: Apply Enzo Bossmann's Cursor Kit workflow in Codex for project setup, token-efficient exploration, memory continuity, verification, simplification, and safe shipping. Use when the user asks to use, load, configure, or apply cursor-kit, token-engine, ai-memory, or the Bossmann agent stack.
---

# Cursor Kit for Codex

Use the compatible part of this repository as the default operating layer for Codex projects.

## Stack

- `token-engine` MCP: compress large tool output and context; preserve errors, paths, commands, and exact values.
- `codebase-memory` MCP: explore code structure with graph/search tools before broad reads.
- `ai-memory` MCP: long-horizon wiki and handoff context only; `AGENTS.md`, `PROJECT.md`, and `.cursor/state` remain authoritative.
- Kit skills: `setup-project`, `setup-ai-memory`, `setup-pucpr`, `verification-planning`, `simplify`, and `blindspot-pass`.

## Working rules

1. Use the smallest working change. Check whether the work is needed, reuse existing code, prefer the standard library and native features, then add the minimum code required.
2. For non-trivial work, establish an evidence path before editing: target files, validation command, and expected result.
3. After behavior is proven, run a simplify pass; before shipping, run a blind-spot pass for edge cases, silent failures, security, and accessibility.
4. When exploring a codebase, prefer `codebase-memory` search/graph/snippet/trace tools. Read a whole file only when it is the task-focus file, small, or needed after targeted exploration.
5. Compress tool output over roughly 500 tokens with `token-engine` before retaining it in context. Never drop negation, errors, paths, commands, or numbers.
6. Keep session continuity in this order: `AGENTS.md`, `PROJECT.md` decisions, `.cursor/state/checkpoint.json`, `.cursor/state/failures.jsonl`, then ai-memory handoff context.
7. Never write secrets to memory, project docs, checkpoints, skill output, commits, or ai-memory.
8. Explain non-trivial choices using a named principle or evidence from a run, test, log, or screenshot. Do not claim success without verification.
9. In Portuguese conversations, answer in Portuguese; keep code and identifiers in English unless the target project is Portuguese-first.

## Cursor-only components

Cursor `.mdc` rules and `~/.cursor/hooks.json` remain active in Cursor. Codex does not execute those files as native hooks, so apply the equivalent rules above in this skill and the global `AGENTS.md` compatibility section.

## References

- `docs/00-overview.md`
- `docs/01-installation.md`
- `docs/02-playbook-onboarding.md`
- `docs/ARCHITECTURE.md`
- `docs/MEMORY.md`
