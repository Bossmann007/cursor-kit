#!/usr/bin/env bash
# Run a /goal unattended with a budget, a turn cap and an isolated worktree.
# usage: goal-run.sh <project-dir> <max-usd> [max-turns=15] ["task description"]
# The project must have an executable scripts/verify (exit 0 = done).
# DRY_RUN=1 prints the command instead of running it.
set -euo pipefail
DIR="${1:?project dir}"; USD="${2:?max usd}"; TURNS="${3:-15}"; TASK="${4:-the task described in PROJECT.md}"
[[ -x "$DIR/scripts/verify" ]] || { echo "missing executable $DIR/scripts/verify" >&2; exit 2; }
COND="scripts/verify exits 0 (run it and show its exit code), no file outside the task scope changed, and the task is done: ${TASK}. Or stop after ${TURNS} turns, or after 2 turns in a row without progress, and report what is left."
CMD=(claude -p "/goal $COND" --max-budget-usd "$USD" --worktree "goal-$(date +%m%d%H%M)" --output-format stream-json --verbose)
if [[ "${DRY_RUN:-0}" == 1 ]]; then printf '%q ' "${CMD[@]}"; echo; exit 0; fi
cd "$DIR"
exec "${CMD[@]}"
