---
name: setup-ai-memory
description: >
  Install or repair the ai-memory companion for Cursor (native macOS binary,
  LaunchAgent, MCP + lifecycle hooks) while keeping kit layers AGENTS.md,
  PROJECT.md, and .cursor/state authoritative. Also invoked from /setup-project
  (pré-check repair + depth-2 install) and /setup-pucpr when the full Cursor
  stack is in play. Use when the user asks to wire ai-memory, long-horizon wiki
  memory, cross-agent handoffs, or says setup / arrumar ai-memory. Prefer this
  over ad-hoc upstream copy-paste.
disable-model-invocation: false
---

# Setup ai-memory

Opt-in **companion** for long-horizon project memory. Compose upstream
[ai-memory](https://github.com/akitaonrails/ai-memory) with cursor-kit — do not
fork, do not vendor their SKILL.md, do not replace kit episodic state.

Canonical kit root: `~/cursor-kit` (or this plugin repo). Human doc (PT):
`docs/tools/10-ai-memory.md`. Pasteable prompt: `docs/prompts/07-ai-memory-wire.md`.

## Ownership (do not blur)

| Layer | Authority |
|-------|-----------|
| Prefs / facts | `AGENTS.md` (continual-learning) |
| Architecture | `PROJECT.md` Decisions |
| Live task / continue | `.cursor/state/checkpoint.json` |
| Tool failures | `.cursor/state/failures.jsonl` |
| Long-horizon wiki / handoff / FTS | ai-memory (when enabled) |

Retrieval still starts with kit layers; only then ask ai-memory MCP for handoff/brief.

## Process

### 0. Consent

Confirm once: install/repair companion on this machine? (recommended for solo
macOS Cursor + optional Claude/Codex later). If declined, stop and point at the
PT doc.

### 1. Pré-check

| Check | Healthy | Action |
|-------|---------|--------|
| macOS + arch | Darwin arm64/x86_64 | Else: point upstream install docs; do not run kit script |
| Binary | `ai-memory` on PATH or `~/Applications/ai-memory/ai-memory` | Run kit installer |
| Server | `curl` `http://127.0.0.1:49374/mcp` → 405 (or 401 with auth) | Start LaunchAgent / `serve` |
| MCP | `~/.cursor/mcp.json` has ai-memory | `install-mcp --client cursor --apply` |
| Hooks | hooks.json has kit **and** ai-memory commands | `install-hooks --agent cursor --apply`; never wipe kit hooks |

### 2. Install / repair

Prefer kit script (idempotent):

```bash
# from cursor-kit root
./scripts/install-ai-memory.sh
```

Defaults: native release tarball → `~/Applications/ai-memory`, LaunchAgent,
loopback bind, zero-LLM OK, then upstream `install-mcp` / `install-hooks` for
**cursor**.

Overrides: `AI_MEMORY_HOME`, `AI_MEMORY_SKIP_LAUNCHD=1`, `AI_MEMORY_SKIP_WIRE=1`,
`AI_MEMORY_FORCE_DOWNLOAD=1`.

Do **not** download without user consent if they only asked for docs.

### 3. Preserve kit hooks

After wiring, if the user runs `./sync-hooks.sh`, it must be **merge-safe**
(kit scripts only; companions preserved). If an old overwrite wiped ai-memory
entries, re-run `ai-memory install-hooks --agent cursor --apply` via the real
binary path under `~/Applications/ai-memory/ai-memory` (not a broken symlink).

### 4. Verify

1. LaunchAgent running (or foreground `serve`)
2. Loopback `/mcp` returns 405
3. MCP lists ai-memory beside token-engine / codebase-memory
4. `hooks.json` still includes kit `*.py` hooks **and** ai-memory hook commands
5. Remind: Reload Cursor MCP / window
6. Optional: `memory_status` via MCP; do not dump secrets

### 5. Done report

```markdown
## ai-memory setup

- Consent: accepted | declined
- Binary: path | missing
- Server: up (code) | down
- MCP: wired | repaired | skipped
- Hooks: kit+companion | kit-only | needs re-wire
- Next: reload MCP; use checkpoint for continue; wiki for long-horizon recall
```

## Guardrails

- Composition: call upstream CLI; never paste their hook scripts into the plugin
- No second **episodic** store — checkpoint remains continue/retomar authority
- No secrets in wiki or kit memory files (`memory-security`)
- No absolute machine-specific paths in committed docs
- Docker path is secondary on macOS; kit default is native + LaunchAgent
- Depth 1 `/setup-project` does not require this companion

## Out of scope

- Homelab multi-user auth / TLS (point at upstream deploy docs)
- Making `ai-memory run` the Cursor launcher
- Dual-write AGENTS ↔ wiki
- Cloud Projects VM install (companion is desktop/loopback-first)
