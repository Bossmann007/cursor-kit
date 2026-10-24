#!/usr/bin/env bash
# Install Claude Code plugins:
#  - pstack: OFFICIAL Claude Code build from marketplace cursor/plugins (generated tree with Cursor->Claude name adapter).
#  - superpowers (opt-in, WITH_SUPERPOWERS=1): pinned copy from the Cursor plugin cache via a local marketplace (hooks stripped).
#  - official helper: frontend-design. commit-commands and claude-md-management were dropped (unused; /doctor 2026-10-24).
# Idempotent. Network only for GitHub (cursor/plugins) and the Anthropic plugin directory.
set -euo pipefail
umask 022
command -v claude >/dev/null || { echo "claude CLI missing"; exit 0; }
M="${HOME}/.claude/local-marketplace"
CACHE="${HOME}/.cursor/plugins/cache/cursor-public"
has_plugin() { claude plugin list 2>/dev/null | grep -q "❯ $1"; }

# pstack (official)
claude plugin marketplace list 2>/dev/null | grep -q cursor-plugins || claude plugin marketplace add cursor/plugins 2>&1 | tail -1
has_plugin pstack@cursor-plugins && claude plugin update pstack@cursor-plugins 2>&1 | tail -1 || claude plugin install pstack@cursor-plugins 2>&1 | tail -1
# retire the old local pstack copy if present
has_plugin pstack@bossmann-local && claude plugin uninstall pstack@bossmann-local >/dev/null 2>&1 || true
rm -rf "$M/plugins/pstack" "$HOME/.claude/plugins/cache/bossmann-local/pstack"

# superpowers (local copy, no SessionStart hook)
if [[ "${WITH_SUPERPOWERS:-}" == "1" && -d "$CACHE/superpowers" ]]; then
  mkdir -p "$M/.claude-plugin" "$M/plugins"
  latest="$(ls -dt "$CACHE"/superpowers/*/ | head -1)"
  rsync -a --delete --exclude .git --exclude .cache-complete "$latest" "$M/plugins/superpowers/"
  rm -rf "$M/plugins/superpowers/hooks"
  python3 - "$M" <<'PY'
import json,sys
M=sys.argv[1]
sp=json.load(open(f'{M}/plugins/superpowers/.claude-plugin/plugin.json'))
json.dump({"name":"bossmann-local","owner":{"name":"Enzo Bossmann"},"plugins":[
 {"name":"superpowers","source":"./plugins/superpowers","description":"superpowers (no hooks)","version":sp['version']}]},
 open(f'{M}/.claude-plugin/marketplace.json','w'),indent=2)
PY
  claude plugin marketplace list 2>/dev/null | grep -q bossmann-local || claude plugin marketplace add "$M"
  claude plugin marketplace update bossmann-local >/dev/null
  claude plugin uninstall superpowers@bossmann-local >/dev/null 2>&1 || true
  rm -rf "$HOME/.claude/plugins/cache/bossmann-local/superpowers"
  claude plugin install superpowers@bossmann-local 2>&1 | tail -1
else
  echo "install-claude-plugins: superpowers skipped (set WITH_SUPERPOWERS=1; needs the Cursor plugin cache)"
fi

for p in frontend-design; do
  has_plugin "$p@anthropic-plugin-directory" && echo "plugin $p: installed" || claude plugin install "$p@anthropic-plugin-directory" 2>&1 | tail -1
done
echo "install-claude-plugins: done (restart Claude Code; pstack commands are /pstack:<name>)"
