#!/usr/bin/env bash
# One-shot install of cursor-kit + token-engine + ai-memory across Claude Code, Cursor, Codex, Gemini CLI.
# Idempotent, add-only merges, backups chmod 600, no secrets read/printed/written.
# Env: TOOLS="claude cursor codex gemini" (subset), SKIP_AI_MEMORY=1.
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLS="${TOOLS:-claude cursor codex gemini}"
TE="${HOME}/.cursor/repos/token-engine"
has() { [[ " $TOOLS " == *" $1 "* ]]; }
say() { echo "sync-all: $*"; }

# 1. token-engine: venv + editable install + import check
[[ -d "$TE" ]] || { say "token-engine missing at $TE"; exit 1; }
if [[ ! -x "$TE/.venv/bin/python" ]]; then python3 -m venv "$TE/.venv"; fi
"$TE/.venv/bin/python" -m pip install -q -e "$TE"
"$TE/.venv/bin/python" -c "import token_engine.mcp.server" && say "token-engine ok"
chmod -R go-rwx "$TE/.venv" 2>/dev/null || true

# 2. ai-memory binary + LaunchAgent (loopback only) + per-agent wiring
if [[ "${SKIP_AI_MEMORY:-}" != "1" ]]; then
  [[ "${AI_MEMORY_BIND:-127.0.0.1:49374}" == 127.0.0.1:* ]] || { say "ai-memory bind must be loopback"; exit 1; }
  agents="" 
  has claude && agents+=" claude-code"; has cursor && agents+=" cursor"
  has codex && agents+=" codex"; has gemini && agents+=" gemini-cli"
  AI_MEMORY_AGENTS="${agents# }" "$ROOT/scripts/install-ai-memory.sh"
fi

# 3. per-tool kit wiring
has claude && SKIP_AI_MEMORY=1 "$ROOT/sync-claude.sh"
if has cursor; then "$ROOT/sync-hooks.sh"; python3 "$ROOT/scripts/merge-mcp.py" --client cursor --file ~/.cursor/mcp.json; fi
if has codex; then
  mkdir -p ~/.codex
  [[ -e ~/.codex/AGENTS.md ]] || ln -s ~/AGENTS.md ~/.codex/AGENTS.md
  for n in token-engine codebase-memory context7 ai-memory; do
    codex mcp get "$n" >/dev/null 2>&1 || say "codex mcp $n missing (add via 'codex mcp add')"
  done
fi
if has gemini; then
  mkdir -p ~/.gemini
  [[ -e ~/.gemini/GEMINI.md ]] || printf '@%s/AGENTS.md\n' "$HOME" > ~/.gemini/GEMINI.md
  python3 "$ROOT/scripts/merge-mcp.py" --client gemini --file ~/.gemini/settings.json
fi

# 4. permissions hardening on config files (no content read)
for f in ~/.cursor/mcp.json ~/.cursor/hooks.json ~/.claude.json ~/.claude/settings.json ~/.codex/config.toml ~/.codex/auth.json ~/.gemini/settings.json; do
  [[ -f "$f" ]] && chmod 600 "$f"
done
chmod 600 ~/.cursor/mcp.json.bak.* ~/.claude/settings.json.bak.* ~/.claude.json.backup* 2>/dev/null || true
# 5. backup retention: keep newest 3 per config family, all 600
prune() { local f n=0; for f in $(ls -t "$1"* 2>/dev/null); do [[ "$f" == "$1" ]] && continue; n=$((n+1)); [[ $n -gt 3 ]] && rm -f "$f" || chmod 600 "$f"; done; }
for b in ~/.claude/settings.json.bak ~/.claude/CLAUDE.md.bak ~/.cursor/mcp.json.bak ~/.cursor/hooks.json.bak ~/.codex/config.toml.bak ~/.codex/hooks.json.bak ~/.gemini/settings.json.bak; do prune "$b"; done
say "done. Restart each tool. TiDB MCP: register with env vars only; rotate the old password."
