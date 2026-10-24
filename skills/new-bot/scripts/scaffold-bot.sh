#!/usr/bin/env bash
# Scaffold one bot folder: <bots-dir>/<slug>/ with CLAUDE.md template and .claude/{skills,agents,references,state}.
# Refuses an existing folder. Writes nothing outside the new folder. No secrets.
# Usage: scaffold-bot.sh <slug> [--bots-dir DIR]   (default DIR: ~/bots)
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
KIT="$(cd "$SKILL/../.." && pwd)"
slug="${1:-}"; shift || true
dir="${HOME}/bots"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bots-dir) dir="${2:?--bots-dir needs a path}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ "$slug" =~ ^[a-z0-9][a-z0-9-]{0,39}$ ]] || { echo "bad slug '$slug' (use [a-z0-9-], max 40)" >&2; exit 2; }
bot="${dir%/}/${slug}"
[[ -e "$bot" ]] && { echo "exists: $bot (not touched)" >&2; exit 1; }

mkdir -p "$bot"/.claude/{skills,agents,references,state}
cp "$SKILL/templates/CLAUDE.md.template" "$bot/CLAUDE.md"
if [[ -f "$KIT/state/checkpoint.json.example" ]]; then
  cp "$KIT/state/checkpoint.json.example" "$bot/.claude/state/checkpoint.json"
else
  printf '{"task": "", "status": "idle", "next_action": ""}\n' > "$bot/.claude/state/checkpoint.json"
fi
echo "created $bot"
