#!/usr/bin/env bash
# Fail if staged/tracked content looks like a credential. Usage: secret-scan.sh [--all]
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [[ "${1:-}" == "--all" ]]; then files="$(git ls-files)"; else files="$(git diff --cached --name-only --diff-filter=AM)"; fi
PAT='(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(password|passwd|secret|api[_-]?key|token)["'"'"']? *[:=] *["'"'"'][^"'"'"' $<{(]{8,}["'"'"'])'
bad=0
while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  if git show ":$f" 2>/dev/null | grep -Eiq -- "$PAT"; then echo "secret-scan: possible secret in $f"; bad=1; fi
done <<<"$files"
case "$files" in *.env*|*mcp.json*|*auth.json*) [[ "$files" == *template* ]] || { echo "secret-scan: sensitive filename staged"; bad=1; } ;; esac
exit $bad
