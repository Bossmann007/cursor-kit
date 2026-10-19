# Global Claude instructions (Enzo Bossmann)

Source: `~/cursor-kit/claude/CLAUDE.md`, installed by `sync-claude.sh`.

@~/AGENTS.md

## Replies (IMPORTANT)

Short and direct: no preamble, no recap, no option menus, about 6 lines unless asked for more. Portuguese in chat, English in code and identifiers. State only what you verified; say "não verifiquei" for the rest. Never invent commands, flags, files or features: check first.

## Work

- Done means evidence: run the project's check (tests, build, lint) and show the output.
- Non-trivial task: `/emode`. Heavy or multi-file: `/pstack:poteto-mode`. Plan only if the change spans more than one file.
- Before building a new tool, skill or integration: `/prior-art-check`.
- No commit or push unless asked; ship by PR. Never merge unless asked.
- Smallest change that works; fix the root cause.
- Delegating with `/goal`: the project needs an executable `scripts/verify` (exit 0 = done). Run `~/cursor-kit/scripts/goal-run.sh <dir> <usd> [turns]` for a budget, turn cap and worktree. The `/goal` evaluator only reads the transcript, so the condition must make Claude run `scripts/verify` and show its exit code.
- On `continue` / `retomar`: follow `.claude/state/checkpoint.json` (`task`, `next_action`).

## Context

- Big Bash output is filtered by hooks (RTK, `te-filter-output`); do not compress by hand. Full text stays in `~/.claude/te-cache`; read it there when the filtered text hides detail.
- Code structure: codebase-memory first (`search_graph`, `get_code_snippet`); do not re-read files.
- History and decisions: ai-memory MCP.

## Security

Never write secrets (keys, tokens, passwords, connection strings, `.env` values, cookies) into any file, commit, memory or ai-memory. If one appears: do not copy it, tell the user to rotate it.
