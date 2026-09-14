# Sync global hooks from cursor-kit source (run after editing hooks here)

$root = $PSScriptRoot
$src = Join-Path $root "hooks"
$dst = Join-Path $env:USERPROFILE ".cursor\hooks"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item (Join-Path $src "*.py") $dst -Force

$template = Join-Path $root "hooks.json.template"
$hooksJson = Join-Path $env:USERPROFILE ".cursor\hooks.json"
if (Test-Path $template) {
  $resolved = ($dst -replace '\\', '/')
  (Get-Content $template -Raw) -replace '__CURSOR_HOOKS_DIR__', $resolved | Set-Content -Path $hooksJson -NoNewline
  Write-Host "Wrote $hooksJson"
}

Write-Host "Synced hooks to $dst"
