#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="${ROOT}/hooks"
DST="${HOME}/.cursor/hooks"
mkdir -p "$DST"
cp "$SRC"/*.py "$DST"/
chmod +x "$DST"/*.py

# Install global hooks.json from template with resolved hooks dir (no machine paths in git).
# MERGE-SAFE: preserves non-kit companion commands (ai-memory, rtk, …).
TEMPLATE="${ROOT}/hooks.json.template"
HOOKS_JSON="${HOME}/.cursor/hooks.json"
MERGE_PY="${ROOT}/scripts/merge-hooks-json.py"
if [[ -f "$TEMPLATE" ]]; then
  # shellcheck disable=SC2016
  KIT_RESOLVED="$(mktemp)"
  sed "s|__CURSOR_HOOKS_DIR__|${DST}|g" "$TEMPLATE" > "$KIT_RESOLVED"
  if [[ -f "$MERGE_PY" ]]; then
    MERGED="$(mktemp)"
    python3 "$MERGE_PY" --kit "$KIT_RESOLVED" --existing "$HOOKS_JSON" --out "$MERGED"
    mv "$MERGED" "$HOOKS_JSON"
    rm -f "$KIT_RESOLVED"
    echo "Merged kit hooks into $HOOKS_JSON (companions preserved)"
  else
    mv "$KIT_RESOLVED" "$HOOKS_JSON"
    echo "Wrote $HOOKS_JSON (merge helper missing — full replace)"
  fi
fi

echo "Synced hooks to $DST"
