# External components — inventory + update

Third-party skills, plugins, and companions used with cursor-kit. None auto-update;
re-check occasionally. Prefer **form** from peers; keep stack advantages
(token-engine, hooks + `.cursor/state`, `/setup-project`, ponytail/caveman/cbm,
continual-learning, pstack/team-kit).

| Component | Source | Where it lives | Update procedure |
|-----------|--------|----------------|------------------|
| token-engine | [Bossmann007/token-engine](https://github.com/Bossmann007/token-engine) | `~/token-engine` + MCP in `~/.cursor/mcp.json` | pull repo; keep venv; reload MCP |
| ai-memory | [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) | Companion binary (default `~/Applications/ai-memory`) + LaunchAgent + MCP/hooks via `/setup-ai-memory` | re-run `scripts/install-ai-memory.sh` or upgrade release tarball; reload MCP; see `docs/tools/10-ai-memory.md` |
| codebase-memory | MCP (see `mcp.json.template`) | `~/.cursor/mcp.json` | update MCP entry / package per upstream |
| continual-learning | Cursor plugin | UI plugins | update in Cursor plugin UI |
| cursor-team-kit | Cursor plugin | UI plugins (`deslop`, CI/PR skills) | update in Cursor plugin UI |
| pstack | Cursor plugin | UI plugins + `/setup-pstack` → `~/.cursor/rules/pstack-models.mdc` | update plugin; re-run `/setup-pstack` if models drift |
| poteto-mode | pstack (or bundled skill path) | plugin skills | update with pstack |
| humanizer | [blader/humanizer](https://github.com/blader/humanizer) | Cursor plugin cache / local install | update plugin; do not vendor into cursor-kit |
| Matt Pocock skills | [mattpocock/skills](https://github.com/mattpocock/skills) | `~/.cursor/skills/` via `install-skills.ps1` allowlist | re-run install script; see `SKILLS-CURATED.md` |
| book rules | [mattpocock/agent-rules-books](https://github.com/mattpocock/agent-rules-books) | `~/.cursor/rules/books/` | re-run install script allowlist |
| superpowers | Cursor plugin (public) | plugin cache | optional; verification-before-completion pairs with kit `verification-planning` |
| context7 | MCP / plugin | global MCP | update via Cursor |
| find-skills | vercel-labs/skills | `~/.cursor/skills/find-skills` | `npx skills add …` or install script |

## Kit-native skills (not third-party copies)

| Skill | Role | Desktop location |
|-------|------|------------------|
| `setup-project` / `setup-pucpr` / `setup-ai-memory` | Orchestrators (repo / PUCPR / ai-memory companion) | **Plugin** `skills/` |
| `verification-planning` | Evidence path before non-trivial work | **Plugin** `skills/` |
| `simplify` | Behavior-preserving complexity reduction | **Plugin** `skills/` |
| `blindspot-pass` | Second-pass edges / silent failures before ship | **Plugin** `skills/` |

Removed from the kit (covered by rules/hooks/`/setup-project`): `context-engine`, `dev-workflow`, `project-brain`, `update-checkpoint`.

On desktop with the plugin installed, do **not** keep a second copy under
`~/.cursor/skills/` for plugin-shipped names.

## Install / sync

```bash
# Desktop (preferred): sync repo → local plugin, then Reload Window
rsync -a --delete --exclude '.git/' --exclude '__pycache__/' \
  ~/cursor-kit/ ~/.cursor/plugins/local/cursor-kit/

# Cloud / Projects VM only (no plugin): copy skills → ~/.cursor/skills inside the VM
./scripts/install-cloud-skills.sh
# Script no-ops on desktop when the local plugin is already present.
```

Windows curated Matt + env skills (`install-skills.ps1`) also skips copying
plugin-shipped skills when the local plugin exists.

Last reviewed: 2026-09-18 (ai-memory companion + merge-safe sync-hooks).
