# Workflows

## Default dev (non-trivial)

Prefer `/poteto-mode`. Fallback loop when staying light:

```text
PLAN → IMPLEMENT → TEST → REVIEW → MEMORIZE
```

Use `/verification-planning` before IMPLEMENT on non-trivial work; `/simplify`
and `/blindspot-pass` after behavior is proven.

## Continue interrupted work

1. User: `continue` / `retomar`
2. Agent reads checkpoint.json + failures.jsonl
3. Resumes next_action

## Iterative loops

| Tool | Use |
|------|-----|
| superpowers | Default plans/TDD/debug |
| ralph-loop | Long autonomous iteration (optional) |

Skip OMH/Hermes pipeline.

## Compression workflow

1. Agent runs tool
2. If output large → caveman_compress MCP
3. postToolUse hook adds ratio notice

## Memory workflow

1. Continual Learning updates AGENTS.md (background)
2. Agent updates checkpoint at task boundaries
3. Failures append on tool errors

## Writing a skill

`scripts/skill-lint.py` checks every `skills/<name>/SKILL.md`. `scripts/verify` runs it: it reports all skills, and
fails only when a skill whose `SKILL.md` was added or changed against `origin/master` fails a check (no git base:
report only, printed as `gate SKIPPED`). Run `python3 scripts/skill-lint.py` before a skill PR.

| Check | Passes when | Source |
|---|---|---|
| Frontmatter | `name` and `description` are set; a description over 600 characters (~100-150 tokens) only warns | [Anthropic skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (both required, description max 1,024 chars); the 600 warn: Uber* |
| Length | the body after the frontmatter is under 500 lines; scripts and references go in files the steps load | Anthropic best practices: "Keep the SKILL.md body under 500 lines" |
| Steps | there are numbered steps (`1.` items or `### 1.` headings), each with a `command` in backticks or a code block, and a check word (`Check`, `Done when`, `verify`, `confirm`, `expect`, `exit 0`, `until`, `passes`, ...) | Uber*; Anthropic best practices: sequential steps and "Run validator → fix errors → repeat" |
| Recovery | a heading starting with Error(s), Failure(s), Recovery, Troubleshooting or "If/When ... fails" has a table (failure, fix) or list (`failure → fix`, `failure: fix`) with at least one fix that is not only "try again"/"retry" | Uber* |

\* Uber Engineering, [Skills at Enterprise Scale](https://x.com/UberEng/status/2125008806249930999), as summarized
in the brief for this lint; the post itself was not read (X returned HTTP 402).

The checks are structural on purpose: they look for the shape, not the intent, so a passing skill can still be weak.
