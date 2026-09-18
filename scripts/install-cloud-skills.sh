#!/usr/bin/env bash
# Install cursor-kit skills into ~/.cursor/skills for Cursor Cloud / Projects VMs
# when the cursor-kit **plugin is not** available on that machine.
#
# Desktop with plugin installed: do NOT copy — plugin skills/ is the source of
# truth. Prefer: rsync kit → ~/.cursor/plugins/local/cursor-kit/
#
# Override: FORCE_USER_SKILLS=1 copies even when the plugin is present
# (legacy / debugging only).
#
# Idempotent. Safe to re-run on every Cloud Build.
set -euo pipefail

KIT_REPO="${CURSOR_KIT_REPO:-https://github.com/Bossmann007/cursor-kit.git}"
KIT_REF="${CURSOR_KIT_REF:-master}"
KIT_DIR="${CURSOR_KIT_DIR:-${HOME}/.cursor-kit-src}"
SKILLS_DST="${HOME}/.cursor/skills"
PLUGIN_SKILLS="${HOME}/.cursor/plugins/local/cursor-kit/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/../skills/setup-project/SKILL.md" ]]; then
  KIT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
  echo "install-cloud-skills: using workspace kit at ${KIT_DIR}"
elif [[ -f "$(pwd)/skills/setup-project/SKILL.md" ]]; then
  KIT_DIR="$(pwd)"
  echo "install-cloud-skills: using cwd kit at ${KIT_DIR}"
else
  mkdir -p "${HOME}"
  if [[ -d "${KIT_DIR}/.git" ]]; then
    git -C "${KIT_DIR}" fetch --depth 1 origin "${KIT_REF}"
    git -C "${KIT_DIR}" checkout -q FETCH_HEAD || git -C "${KIT_DIR}" checkout -q "${KIT_REF}"
    git -C "${KIT_DIR}" pull --ff-only origin "${KIT_REF}" 2>/dev/null || true
  else
    rm -rf "${KIT_DIR}"
    git clone --depth 1 --branch "${KIT_REF}" "${KIT_REPO}" "${KIT_DIR}"
  fi
fi

if [[ "${FORCE_USER_SKILLS:-}" != "1" && -f "${PLUGIN_SKILLS}/setup-project/SKILL.md" ]]; then
  echo "install-cloud-skills: cursor-kit plugin found at ${PLUGIN_SKILLS}"
  echo "install-cloud-skills: skipping copy to ${SKILLS_DST} (plugin is source of truth)"
  echo "install-cloud-skills: tip — rsync kit → ~/.cursor/plugins/local/cursor-kit/ then Reload Window"
  echo "install-cloud-skills: override with FORCE_USER_SKILLS=1 if you really need user-skills copies"
  exit 0
fi

mkdir -p "${SKILLS_DST}"

if [[ ! -d "${KIT_DIR}/skills" ]]; then
  echo "install-cloud-skills: no skills/ in ${KIT_DIR}" >&2
  exit 1
fi

shopt -s nullglob
for skill_src in "${KIT_DIR}/skills"/*/; do
  name="$(basename "${skill_src}")"
  if [[ ! -f "${skill_src}/SKILL.md" ]]; then
    echo "install-cloud-skills: skip ${name} (no SKILL.md)"
    continue
  fi
  dst="${SKILLS_DST}/${name}"
  rm -rf "${dst}"
  mkdir -p "${dst}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude '.git' \
      --exclude 'evals' \
      --exclude '*-workspace' \
      --exclude 'DRAFT.md' \
      "${skill_src}" "${dst}/"
  else
    cp -R "${skill_src}/." "${dst}/"
    rm -f "${dst}/DRAFT.md"
  fi
  echo "install-cloud-skills: installed ${name}"
done

echo "install-cloud-skills: done → ${SKILLS_DST}"
ls -1 "${SKILLS_DST}" || true
