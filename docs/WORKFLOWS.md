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
