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

**Preferred (orchestrator):** in Cursor, run **`/setup-project`** (skill in this repo / plugin). It scaffolds kit files, repairs global gaps (MCP/hooks/pstack), runs Matt Pocock setup, and checks team-kit + continual-learning.

Manual fallback:

```bash
# macOS / Linux
~/cursor-kit/install.sh

# Windows
~\cursor-kit\install.ps1
~\cursor-kit\install-skills.ps1   # mattpocock skills + book rules + find-skills
```

Then (if not using `/setup-project`): run **`setup-matt-pocock-skills`** once per repo.

### Use as Cursor plugin

This repo ships `.cursor-plugin/plugin.json` + `skills/setup-project/`. Install from GitHub or symlink:

```bash
ln -sfn ~/cursor-kit ~/.cursor/plugins/local/cursor-kit
```

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
