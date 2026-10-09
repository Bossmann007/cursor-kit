#!/usr/bin/env bash
# Batch MarkItDown → Markdown. Idempotent skip if .md exists and is non-empty unless FORCE=1.
# Works on macOS (BSD find) and Linux.
set -euo pipefail

OUT_DIR=""
SOURCES=()
FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out|-o)
      OUT_DIR="${2:?}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      echo "Usage: digest.sh [--out DIR] [--force] <file-or-dir> [more...]"
      exit 0
      ;;
    *)
      SOURCES+=("$1")
      shift
      ;;
  esac
done

if [[ ${#SOURCES[@]} -eq 0 ]]; then
  echo "digest.sh: need at least one file or directory" >&2
  exit 1
fi

resolve_markitdown() {
  if [[ -n "${MARKITDOWN:-}" && -x "${MARKITDOWN}" ]]; then
    echo "${MARKITDOWN}"
    return
  fi
  if command -v markitdown >/dev/null 2>&1; then
    command -v markitdown
    return
  fi
  for candidate in \
    "${HOME}/token-engine/.venv/bin/markitdown" \
    "${HOME}/.cursor/repos/token-engine/.venv/bin/markitdown"
  do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return
    fi
  done
  return 1
}

MARKITDOWN_BIN="$(resolve_markitdown)" || {
  echo "digest.sh: markitdown not found. Install into Python 3.10+: pip install 'markitdown[all]'" >&2
  exit 1
}

digest_one() {
  local src="$1"
  local dest
  local base
  base="$(basename "$src")"
  base="${base%.*}"

  if [[ -n "$OUT_DIR" ]]; then
    mkdir -p "$OUT_DIR"
    dest="${OUT_DIR}/${base}.md"
  else
    dest="$(dirname "$src")/${base}.md"
  fi

  if [[ -s "$dest" && "$FORCE" != "1" ]]; then
    echo "skip (exists): $dest"
    return 0
  fi

  echo "convert: $src → $dest"
  "$MARKITDOWN_BIN" "$src" -o "$dest"
}

is_convertible() {
  local f="$1"
  local lower
  lower="$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    *.pdf|*.docx|*.doc|*.pptx|*.ppt|*.xlsx|*.xls|*.html|*.htm|*.epub|*.csv|*.json|*.xml|*.png|*.jpg|*.jpeg|*.gif|*.webp|*.mp3|*.wav|*.zip)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

for item in "${SOURCES[@]}"; do
  if [[ -d "$item" ]]; then
    while IFS= read -r -d '' f; do
      if is_convertible "$f"; then
        digest_one "$f"
      fi
    done < <(find "$item" -type f -print0)
  elif [[ -f "$item" ]]; then
    digest_one "$item"
  else
    echo "missing: $item" >&2
  fi
done
