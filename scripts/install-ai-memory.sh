#!/usr/bin/env bash
# Install / upgrade / repair ai-memory companion (macOS native default). Wires Claude Code (+ Cursor if present).
# Does not vendor upstream sources into cursor-kit. Idempotent where possible.
#
# Env overrides:
#   AI_MEMORY_HOME     install dir (default: ~/Applications/ai-memory)
#   AI_MEMORY_BIND     default 127.0.0.1:49374
#   AI_MEMORY_SKIP_LAUNCHD=1   skip LaunchAgent
#   AI_MEMORY_SKIP_WIRE=1      skip install-mcp / install-hooks
#   AI_MEMORY_AGENTS           space-separated agents to wire (default: "claude-code"; add "cursor")
#   AI_MEMORY_VERSION          pin a tag (default: latest GitHub release)
set -euo pipefail

AI_MEMORY_HOME="${AI_MEMORY_HOME:-${HOME}/Applications/ai-memory}"
AI_MEMORY_BIND="${AI_MEMORY_BIND:-127.0.0.1:49374}"
REPO="https://github.com/akitaonrails/ai-memory"
if [[ -n "${AI_MEMORY_VERSION:-}" ]]; then
  TAG="${AI_MEMORY_VERSION}"
else
  TAG="$(basename "$(curl -fsSL -o /dev/null -w '%{url_effective}' "${REPO}/releases/latest")")"
fi
[[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+ ]] || { echo "install-ai-memory: cannot resolve release tag (got '${TAG}')" >&2; exit 1; }
REPO_RELEASES="${REPO}/releases/download/${TAG}"
AGENTS="${AI_MEMORY_AGENTS:-claude-code}"

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
else
  have="$("${AI_MEMORY_HOME}/ai-memory" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  if [[ "${have}" != "${TAG#v}" ]]; then
    echo "install-ai-memory: installed ${have:-unknown} -> ${TAG#v}"
    need_download=1
  else
    echo "install-ai-memory: already at ${have}"
  fi
fi

if [[ "${need_download}" -eq 1 || "${AI_MEMORY_FORCE_DOWNLOAD:-}" == "1" ]]; then
  echo "install-ai-memory: downloading ${asset} (${TAG})"
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' EXIT
  curl -fsSL -o "${tmp}/${asset}" "${REPO_RELEASES}/${asset}"
  curl -fsSL -o "${tmp}/${asset}.sha256" "${REPO_RELEASES}/${asset}.sha256"
  want="$(awk '{print $1}' "${tmp}/${asset}.sha256")"
  got="$(shasum -a 256 "${tmp}/${asset}" | awk '{print $1}')"
  [[ "${want}" == "${got}" ]] || { echo "install-ai-memory: checksum mismatch, aborting" >&2; exit 1; }
  # stop service before replacing the binary; back up the old one
  launchctl bootout "gui/$(id -u)/com.github.akitaonrails.ai-memory" 2>/dev/null || true
  [[ -x "${AI_MEMORY_HOME}/ai-memory" ]] && cp "${AI_MEMORY_HOME}/ai-memory" "${AI_MEMORY_HOME}/ai-memory.prev"
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
  # bootout is async: wait for the service to unload, then retry bootstrap (EIO 5 if still loading)
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    launchctl print "gui/${uid}/com.github.akitaonrails.ai-memory" >/dev/null 2>&1 || break
    sleep 0.5
  done
  boot_ok=0
  for _ in 1 2 3 4 5; do
    if launchctl bootstrap "gui/${uid}" "${PLIST_DST}" 2>/dev/null; then boot_ok=1; break; fi
    sleep 1
  done
  [[ "${boot_ok}" == 1 ]] || { echo "install-ai-memory: launchctl bootstrap failed" >&2; exit 1; }
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
  for agent in ${AGENTS}; do
    client="${agent}"
    echo "install-ai-memory: wiring ${agent} MCP + hooks"
    "${BIN}" install-mcp --client "${client}" --apply
    "${BIN}" install-hooks --agent "${agent}" --apply
  done
fi

echo
echo "install-ai-memory: done"
echo "  binary:  ${BIN}"
echo "  bind:    http://${AI_MEMORY_BIND}"
echo "  next:    restart Claude Code (/mcp, /hooks); verify docs/tools/10-ai-memory.md"
echo "  ensure:  ~/.local/bin is on PATH"
