#!/usr/bin/env bash
# Install cursor-kit into Claude Code: hooks, global CLAUDE.md, MCP servers. Idempotent, merge-safe.
# Env: SKIP_MCP=1 skip `claude mcp add`; SKIP_AI_MEMORY=1 skip ai-memory MCP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CL="${HOME}/.claude"
DST="${CL}/hooks"
mkdir -p "$DST"

# 1. hooks scripts
cp "$ROOT"/hooks/*.py "$DST"/
chmod +x "$DST"/*.py

# 2. settings.json merge (backup first)
SETTINGS="${CL}/settings.json"
[[ -f "$SETTINGS" ]] && cp "$SETTINGS" "${SETTINGS}.bak.$(date +%Y%m%d%H%M%S)"
KIT_RESOLVED="$(mktemp)"; MERGED="$(mktemp)"
sed "s|__CLAUDE_HOOKS_DIR__|${DST}|g" "$ROOT/claude-hooks.json.template" > "$KIT_RESOLVED"
python3 "$ROOT/scripts/merge-claude-settings.py" --kit "$KIT_RESOLVED" --existing "$SETTINGS" --out "$MERGED"
mv "$MERGED" "$SETTINGS"; rm -f "$KIT_RESOLVED"
echo "merged kit hooks into $SETTINGS"

# 3. global CLAUDE.md (backup if different)
if [[ -f "${CL}/CLAUDE.md" ]] && ! cmp -s "${CL}/CLAUDE.md" "$ROOT/claude/CLAUDE.md"; then
  cp "${CL}/CLAUDE.md" "${CL}/CLAUDE.md.bak.$(date +%Y%m%d%H%M%S)"
fi
cp "$ROOT/claude/CLAUDE.md" "${CL}/CLAUDE.md"
echo "installed ${CL}/CLAUDE.md"

# 4. skills: link kit skills into ~/.claude/skills (plugin install is the alternative)
mkdir -p "${CL}/skills"
for d in "$ROOT"/skills/*/; do
  n="$(basename "$d")"
  [[ -e "${CL}/skills/${n}" ]] || ln -s "${d%/}" "${CL}/skills/${n}"
done
echo "linked skills into ${CL}/skills"

# 5. MCP servers (user scope). Secrets are never written here; add TiDB yourself via env.
if [[ "${SKIP_MCP:-}" != "1" ]] && command -v claude >/dev/null; then
  # add NAME [claude mcp add args before name...] -- usage: add NAME "flags..." then rest handled below
  add() { local name="$1"; shift; if claude mcp get "$name" >/dev/null 2>&1; then echo "mcp $name: exists"; else claude mcp add --scope user "$name" "$@" "${ADD_TAIL[@]}"; fi; }
  TE="${HOME}/.cursor/repos/token-engine"
  ADD_TAIL=(-- "${TE}/.venv/bin/python" -m token_engine.mcp.server)
  add token-engine -e "PYTHONPATH=${TE}/src"
  ADD_TAIL=(-- "${HOME}/.local/bin/codebase-memory-mcp")
  add codebase-memory
  ADD_TAIL=(https://mcp.context7.com/mcp);  add context7 --transport http
  ADD_TAIL=(https://mcp.notion.com/mcp);    add notion --transport http
  ADD_TAIL=(http://127.0.0.1:49374/mcp)
  [[ "${SKIP_AI_MEMORY:-}" == "1" ]] || add ai-memory --transport http
else
  echo "skipped MCP registration (claude CLI missing or SKIP_MCP=1)"
fi
echo "done. Restart Claude Code; run /hooks and /mcp to verify."
