# My Ultimate Cursor Environment

**Repo:** [github.com/Bossmann007/cursor-kit](https://github.com/Bossmann007/cursor-kit) · pairs with [token-engine](https://github.com/Bossmann007/token-engine)

Cursor-only dev stack. Phases 1–29 implemented at infrastructure level.

## Quick reference

| Doc | Topic |
|-----|-------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, hooks, memory types |
| [docs/MEMORY.md](docs/MEMORY.md) | AGENTS.md, checkpoint, failures |
| [docs/PROJECT-BRAIN.md](docs/PROJECT-BRAIN.md) | PROJECT.md |
| [docs/CONTEXT.md](docs/CONTEXT.md) | Context pipeline |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | PLAN→MEMORIZE, continue |
| [docs/MIGRATION.md](docs/MIGRATION.md) | From Hermes/Claude/dotagents |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Fixes |
| [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | token-engine benchmarks |
| [DECISIONS.md](DECISIONS.md) | Locked user decisions |

## Install new project

```powershell
~\cursor-kit\install.ps1
~\cursor-kit\install-skills.ps1   # mattpocock skills + book rules + find-skills
```

Then in Cursor (once per repo): run skill **`setup-matt-pocock-skills`**.

## Global config

Already in `~/.cursor/` — rules, hooks, MCP, skills.

## Tests

```powershell
python -m unittest discover -s "$env:USERPROFILE\cursor-kit\tests"
```

## Manual validation (Test A/B/C)

**A — Continue:** set checkpoint task → close Cursor → `continue` → agent reads checkpoint.

**B — Decision:** add row to PROJECT.md Decisions → return later → agent cites it.

**C — Failure:** fail tool twice → check failures.jsonl → retry uses different approach.
