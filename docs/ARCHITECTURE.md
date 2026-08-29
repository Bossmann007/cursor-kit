# Architecture — My Ultimate Cursor Environment

```text
                         CURSOR (IDE + Agent)
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
      CURSOR NATIVE      PERSONAL LAYER      TOKEN ENGINE
      rules/skills       AGENTS.md              MCP + API
      hooks/MCP          PROJECT.md             compress only
      subagents          checkpoint.json
      indexing           failures.jsonl
           │                  │                  │
           └──────────────────┼──────────────────┘
                              ▼
                    CONTEXT PIPELINE (skill)
              task → brain → memory → CBM → compress → agent
```

## Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Global config | `~/.cursor/` | rules, hooks, MCP, skills |
| Per-project | repo root | AGENTS.md, PROJECT.md |
| Ephemeral | `.cursor/state/` | checkpoint, session, failures, obs |
| Compression | token-engine | external infra, not duplicated |

## Hooks (global)

| Event | Script | Effect |
|-------|--------|--------|
| sessionStart | token-engine-session.py | inject checkpoint + compression hint |
| postToolUse | compress-tool-output.py | note large compressions |
| postToolUseFailure | tool-failure.py | failures.jsonl |
| afterFileEdit | hook.py + track-edits.py | format + track files |
| stop | checkpoint-stop.py | merge session → checkpoint |

## Memory types

| Type | Store | Decay |
|------|-------|-------|
| Semantic | AGENTS.md facts | Continual Learning dedup |
| Episodic | checkpoint.json | overwritten per task |
| Procedural | skills + rules | manual |
| Decision | PROJECT.md table | manual update |
| Failure | failures.jsonl | append-only, read last N |

## Not in scope

- Hermes daemon, Claude Code runtime, MedOS, Linux harness
