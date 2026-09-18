# Copy kit plugin rules into ~/.cursor/rules (global always-on).

$root = $PSScriptRoot
$src = Join-Path $root "rules"
$dst = Join-Path $env:USERPROFILE ".cursor\rules"
New-Item -ItemType Directory -Force $dst | Out-Null
if (-not (Test-Path $src)) {
  Write-Error "No rules/ in kit root"
  exit 1
}
Copy-Item (Join-Path $src "*.mdc") $dst -Force
Write-Host "Synced rules to $dst"

$pstackExample = Join-Path $root "templates\pstack\pstack-models.mdc.example"
$pstackDst = Join-Path $dst "pstack-models.mdc"
if ((Test-Path $pstackExample) -and -not (Test-Path $pstackDst)) {
  Copy-Item $pstackExample $pstackDst
  Write-Host "Seeded $pstackDst from example (run /setup-pstack to pin real models)"
}
