#!/usr/bin/env bash
# Seed a repo from the ai-memory cross-project profile ("Projeto novo" step). Idempotent.
# Usage: seed-project.sh [repo-dir]   Env: AI_MEMORY_BOOTSTRAP=1 to also LLM-summarise existing git history.
set -euo pipefail
AM="${AI_MEMORY_BIN:-${HOME}/Applications/ai-memory/ai-memory}"
REPO="${1:-$PWD}"
[[ -x "$AM" ]] || { echo "seed-project: ai-memory missing (run sync-all.sh)"; exit 1; }
curl -s -o /dev/null -m 3 "http://127.0.0.1:49374/mcp" || { echo "seed-project: ai-memory server down"; exit 1; }
cd "$REPO"
# 1. usage snippet + managed skills in the repo's rules file (bracketed block, no secrets)
"$AM" install-instructions --compact 2>&1 | tail -2
# 2. profile -> managed block of the rules file (no-op while the profile is empty)
if "$AM" profile list 2>/dev/null | grep -q 'profile/'; then
  "$AM" profile apply 2>&1 | tail -2
else
  echo "seed-project: profile empty (fills after >=2 projects share a habit); nothing to apply"
fi
# 3. existing history -> wiki seed pages (opt-in: sends repo text to the configured LLM)
if [[ "${AI_MEMORY_BOOTSTRAP:-}" == "1" ]] && git rev-parse --git-dir >/dev/null 2>&1; then
  "$AM" bootstrap 2>&1 | tail -2
fi
echo "seed-project: done ($REPO)"
