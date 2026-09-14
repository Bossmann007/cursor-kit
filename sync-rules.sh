#!/usr/bin/env bash
# Copy kit plugin rules into ~/.cursor/rules (global always-on). Idempotent overwrite of kit-owned names only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="${ROOT}/rules"
DST="${HOME}/.cursor/rules"
mkdir -p "$DST"
if [[ ! -d "$SRC" ]]; then
  echo "No rules/ in kit root" >&2
  exit 1
fi
cp "$SRC"/*.mdc "$DST"/
echo "Synced rules to $DST"

PSTACK_EXAMPLE="${ROOT}/templates/pstack/pstack-models.mdc.example"
PSTACK_DST="${DST}/pstack-models.mdc"
if [[ -f "$PSTACK_EXAMPLE" && ! -f "$PSTACK_DST" ]]; then
  cp "$PSTACK_EXAMPLE" "$PSTACK_DST"
  echo "Seeded $PSTACK_DST from example (run /setup-pstack to pin real models)"
fi
