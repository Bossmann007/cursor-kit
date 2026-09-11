#!/usr/bin/env bash
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)/hooks"
DST="${HOME}/.cursor/hooks"
mkdir -p "$DST"
cp "$SRC"/*.py "$DST"/
chmod +x "$DST"/*.py
echo "Synced hooks to $DST"
