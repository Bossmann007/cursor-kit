# Sync global hooks from cursor-kit source (run after editing hooks here)
# MERGE-SAFE: preserves non-kit companion commands (ai-memory, rtk, …).

$root = $PSScriptRoot
$src = Join-Path $root "hooks"
$dst = Join-Path $env:USERPROFILE ".cursor\hooks"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item (Join-Path $src "*.py") $dst -Force

$template = Join-Path $root "hooks.json.template"
$hooksJson = Join-Path $env:USERPROFILE ".cursor\hooks.json"
$mergePy = Join-Path $root "scripts\merge-hooks-json.py"
if (Test-Path $template) {
  $resolved = ($dst -replace '\\', '/')
  $kitResolved = Join-Path $env:TEMP "cursor-kit-hooks-kit.json"
  (Get-Content $template -Raw) -replace '__CURSOR_HOOKS_DIR__', $resolved | Set-Content -Path $kitResolved -NoNewline
  if (Test-Path $mergePy) {
    $merged = Join-Path $env:TEMP "cursor-kit-hooks-merged.json"
    $existingArg = @()
    if (Test-Path $hooksJson) { $existingArg = @('--existing', $hooksJson) }
    & python3 $mergePy --kit $kitResolved @existingArg --out $merged
    Move-Item -Force $merged $hooksJson
    Remove-Item -Force $kitResolved -ErrorAction SilentlyContinue
    Write-Host "Merged kit hooks into $hooksJson (companions preserved)"
  } else {
    Move-Item -Force $kitResolved $hooksJson
    Write-Host "Wrote $hooksJson (merge helper missing — full replace)"
  }
}

Write-Host "Synced hooks to $dst"
