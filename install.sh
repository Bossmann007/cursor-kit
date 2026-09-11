#!/usr/bin/env bash
# Install cursor-kit scaffold into a project (macOS/Linux)
set -euo pipefail
PROJECT_ROOT="${1:-$(pwd)}"
KIT="${HOME}/cursor-kit"
mkdir -p "${PROJECT_ROOT}/.cursor/state"
[[ -f "${PROJECT_ROOT}/AGENTS.md" ]] || cp "${KIT}/AGENTS.md.template" "${PROJECT_ROOT}/AGENTS.md"
[[ -f "${PROJECT_ROOT}/PROJECT.md" ]] || cp "${KIT}/PROJECT.md.template" "${PROJECT_ROOT}/PROJECT.md"
[[ -f "${PROJECT_ROOT}/.cursor/state/checkpoint.json" ]] || cp "${KIT}/state/checkpoint.json.example" "${PROJECT_ROOT}/.cursor/state/checkpoint.json"
if [[ -f "${PROJECT_ROOT}/.gitignore" ]]; then
  grep -q 'checkpoint.json' "${PROJECT_ROOT}/.gitignore" || cat "${KIT}/gitignore.snippet" >> "${PROJECT_ROOT}/.gitignore"
else
  cp "${KIT}/gitignore.snippet" "${PROJECT_ROOT}/.gitignore"
fi
echo "cursor-kit installed in ${PROJECT_ROOT}"
