#!/usr/bin/env bash
# Snapshot ai-memory (wiki/db/config) to its backups dir, keep the newest 4, mode 600.
set -euo pipefail
umask 077
AM="${AI_MEMORY_BIN:-${HOME}/Applications/ai-memory/ai-memory}"
D="${HOME}/Library/Application Support/ai-memory/backups"
mkdir -p "$D"
"$AM" backup --to "$D/auto-$(date +%Y%m%d-%H%M).tar.gz" 2>&1 | grep -v INFO | tail -1
n=0
while IFS= read -r f; do n=$((n+1)); if [[ $n -gt 4 ]]; then rm -f "$f"; else chmod 600 "$f"; fi; done < <(ls -t "$D"/auto-*.tar.gz 2>/dev/null)
