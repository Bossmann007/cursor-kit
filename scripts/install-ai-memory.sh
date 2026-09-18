#!/usr/bin/env bash
# Install / repair ai-memory companion for Cursor (macOS native default).
# Does not vendor upstream sources into cursor-kit. Idempotent where possible.
#
# Env overrides:
#   AI_MEMORY_HOME     install dir (default: ~/Applications/ai-memory)
#   AI_MEMORY_BIND     default 127.0.0.1:49374
#   AI_MEMORY_SKIP_LAUNCHD=1   skip LaunchAgent
#   AI_MEMORY_SKIP_WIRE=1      skip install-mcp / install-hooks
set -euo pipefail

AI_MEMORY_HOME="${AI_MEMORY_HOME:-${HOME}/Applications/ai-memory}"
AI_MEMORY_BIND="${AI_MEMORY_BIND:-127.0.0.1:49374}"
REPO_RELEASES="https://github.com/akitaonrails/ai-memory/releases/latest/download"

arch="$(uname -m)"
case "${arch}" in
  arm64|aarch64) asset="ai-memory-macos-aarch64.tar.gz" ;;
  x86_64) asset="ai-memory-macos-x86_64.tar.gz" ;;
  *)
    echo "install-ai-memory: unsupported arch ${arch} (macOS aarch64/x86_64 only)" >&2
    exit 1
    ;;
esac

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "install-ai-memory: this kit script targets macOS native. See upstream docs/install.md" >&2
  exit 1
fi

mkdir -p "${AI_MEMORY_HOME}"
cd "${AI_MEMORY_HOME}"

need_download=0
if [[ ! -x "${AI_MEMORY_HOME}/ai-memory" ]]; then
  need_download=1
fi

if [[ "${need_download}" -eq 1 || "${AI_MEMORY_FORCE_DOWNLOAD:-}" == "1" ]]; then
  echo "install-ai-memory: downloading ${asset}"
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' EXIT
  curl -fsSL -o "${tmp}/${asset}" "${REPO_RELEASES}/${asset}"
  tar -xzf "${tmp}/${asset}" -C "${AI_MEMORY_HOME}"
  chmod +x "${AI_MEMORY_HOME}/ai-memory"
  rm -rf "${tmp}"
  trap - EXIT
fi

BIN="${AI_MEMORY_HOME}/ai-memory"
if [[ ! -x "${BIN}" ]]; then
  echo "install-ai-memory: binary missing at ${BIN}" >&2
  exit 1
fi

# Prefer PATH via ~/.local/bin (no sudo). Symlink after extract so hooks/ stays beside real binary.
mkdir -p "${HOME}/.local/bin"
ln -sfn "${BIN}" "${HOME}/.local/bin/ai-memory"
echo "install-ai-memory: linked ~/.local/bin/ai-memory → ${BIN}"

"${BIN}" init >/dev/null 2>&1 || "${BIN}" init

if [[ "${AI_MEMORY_SKIP_LAUNCHD:-}" != "1" ]]; then
  mkdir -p "${HOME}/Library/Logs/ai-memory" "${HOME}/Library/LaunchAgents"
  PLIST_SRC=""
  for candidate in \
    "${AI_MEMORY_HOME}/packaging/launchd/com.github.akitaonrails.ai-memory.plist" \
    "${AI_MEMORY_HOME}/com.github.akitaonrails.ai-memory.plist"
  do
    if [[ -f "${candidate}" ]]; then
      PLIST_SRC="${candidate}"
      break
    fi
  done

  PLIST_DST="${HOME}/Library/LaunchAgents/com.github.akitaonrails.ai-memory.plist"
  if [[ -n "${PLIST_SRC}" ]]; then
    sed -e "s|__AI_MEMORY_BIN__|${BIN}|g" -e "s|__HOME__|${HOME}|g" \
      "${PLIST_SRC}" > "${PLIST_DST}"
  else
    # Minimal LaunchAgent if tarball omitted packaging/ (still loopback HTTP serve)
    cat > "${PLIST_DST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.github.akitaonrails.ai-memory</string>
  <key>ProgramArguments</key>
  <array>
    <string>${BIN}</string>
    <string>serve</string>
    <string>--transport</string>
    <string>http</string>
    <string>--bind</string>
    <string>${AI_MEMORY_BIND}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${HOME}/Library/Logs/ai-memory/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${HOME}/Library/Logs/ai-memory/stderr.log</string>
</dict>
</plist>
EOF
  fi

  uid="$(id -u)"
  launchctl bootout "gui/${uid}/com.github.akitaonrails.ai-memory" 2>/dev/null || true
  launchctl bootstrap "gui/${uid}" "${PLIST_DST}"
  launchctl kickstart -k "gui/${uid}/com.github.akitaonrails.ai-memory" 2>/dev/null || true
  echo "install-ai-memory: LaunchAgent loaded"
fi

# Wait briefly for bind
for _ in 1 2 3 4 5 6 7 8 9 10; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://${AI_MEMORY_BIND}/mcp" || true)"
  if [[ "${code}" == "405" || "${code}" == "200" || "${code}" == "401" ]]; then
    echo "install-ai-memory: server reachable (${code}) at ${AI_MEMORY_BIND}"
    break
  fi
  sleep 0.5
done

if [[ "${AI_MEMORY_SKIP_WIRE:-}" != "1" ]]; then
  # Run installers via real binary path (not symlink) — older releases had #546
  echo "install-ai-memory: wiring Cursor MCP + hooks"
  "${BIN}" install-mcp --client cursor --apply
  "${BIN}" install-hooks --agent cursor --apply
fi

echo
echo "install-ai-memory: done"
echo "  binary:  ${BIN}"
echo "  bind:    http://${AI_MEMORY_BIND}"
echo "  next:    Reload Cursor MCP; verify docs/tools/10-ai-memory.md"
echo "  ensure:  ~/.local/bin is on PATH"
