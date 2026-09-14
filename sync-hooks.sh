#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="${ROOT}/hooks"
DST="${HOME}/.cursor/hooks"
mkdir -p "$DST"
cp "$SRC"/*.py "$DST"/
chmod +x "$DST"/*.py

# Install global hooks.json from template with resolved hooks dir (no machine paths in git)
TEMPLATE="${ROOT}/hooks.json.template"
HOOKS_JSON="${HOME}/.cursor/hooks.json"
if [[ -f "$TEMPLATE" ]]; then
  # shellcheck disable=SC2016
  sed "s|__CURSOR_HOOKS_DIR__|${DST}|g" "$TEMPLATE" > "$HOOKS_JSON"
  echo "Wrote $HOOKS_JSON"
fi

echo "Synced hooks to $DST"
