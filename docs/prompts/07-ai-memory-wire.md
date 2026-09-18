# Prompt 07. ai-memory companion wire

**PT (wrapper).** Liga o companion [ai-memory](https://github.com/akitaonrails/ai-memory) ao Cursor sem substituir AGENTS / PROJECT / checkpoint. Preferir `/setup-ai-memory` ou o script do kit.

**When to use.** Depth 2 do `/setup-project`, primeira vez no machine, ou repair (MCP/hooks em falta com server saudável).

---

## Paste this to the agent (English)

```text
Wire the ai-memory companion for this Cursor machine. Do not replace kit memory layers.

Keep authoritative:
1. AGENTS.md — durable prefs/facts (continual-learning)
2. PROJECT.md Decisions — approved architecture
3. .cursor/state/checkpoint.json — live task for continue/retomar
4. .cursor/state/failures.jsonl — tool failure memory

Add companion (opt-in long-horizon wiki):
- Prefer kit scripts/install-ai-memory.sh (macOS native binary + LaunchAgent) or /setup-ai-memory
- Default: loopback http://127.0.0.1:49374, zero-LLM OK
- Run: ai-memory install-mcp --client cursor --apply
- Run: ai-memory install-hooks --agent cursor --apply (posix-native)
- Do not overwrite ~/.cursor/hooks.json from scratch — kit sync-hooks must stay merge-safe
- Never store secrets in wiki pages or AGENTS/PROJECT/state
- Do not vendor upstream SKILL.md or Rust sources into cursor-kit

Verify:
1. curl loopback /mcp returns 405 (server up)
2. ~/.cursor/mcp.json lists ai-memory beside token-engine / codebase-memory
3. hooks.json still has kit python hooks AND ai-memory hook commands
4. Report: installed | repaired | declined | blocked (with reason)

Point human docs at docs/tools/10-ai-memory.md (PT).
```
