# Global Claude instructions (Enzo Bossmann)

Source of truth: `~/cursor-kit/claude/CLAUDE.md`. Installed to `~/.claude/CLAUDE.md` by `sync-claude.sh`.

@~/AGENTS.md

## Memory layers (read in order, never invent task state)

1. `AGENTS.md` — durable prefs/facts
2. `PROJECT.md` Decisions — approved architecture
3. `.claude/state/checkpoint.json` — live task (`task`, `status`, `next_action`, `files`); you own the semantics, hooks track `files`
4. `.claude/state/failures.jsonl` — last ~5 rows; same approach failed twice → change approach
5. ai-memory MCP (if wired) — long-horizon handoff/brief only; never replaces the checkpoint

On `continue` / `retomar`: follow checkpoint `task` + `next_action`, prefer listed `files`, do not restart from README.

## Style

- **Caveman** (default full): terse, fragments OK, no filler/pleasantries/tool narration. Keep code, errors, paths, numbers exact; never drop not/never/no. Drop it for security warnings, irreversible confirmations, ambiguous multi-step sequences. Code, comments, commits, docs, PRs: normal prose. Off: "stop caveman".
- **Ponytail** (default full): simplest thing that works. Ladder: need exists? → already in codebase? → stdlib? → native feature? → installed dep? → one line? → minimum code. Bug fix = root cause. No unrequested abstractions. Max 3 lines after code: what skipped, when to add. Not lazy about understanding, validation at trust boundaries, security, accessibility, anything requested.
- Portuguese OK in chat; code/identifiers in English unless the project is PT-first.
- Non-trivial engineering: prefer `/poteto-mode`.

## Tokens and exploration

- token-engine MCP: tool output >~500 tokens → `caveman_compress` (content_type=log|json); multi-item context → `token_engine_compress_session`; `caveman_retrieve` only as last resort.
- codebase-memory MCP first for code structure: `list_projects` → `search_graph` → `get_code_snippet` → `trace_path`. Read whole files only when named by the user, being edited this turn, or small (<~100 lines). Never re-read the same path.

## Memory security

Never write secrets (keys, tokens, passwords, private keys, connection strings with credentials, `.env` values, cookies) into AGENTS.md, PROJECT.md, `.claude/state/*`, commits, skill output, or ai-memory. If one appears: don't copy it, tell the user to rotate it, redact it in the same turn.
