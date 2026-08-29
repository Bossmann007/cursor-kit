# Install cursor-kit hooks into a project

Optional — global hooks in `~/.cursor/hooks.json` already apply to all projects.

Per-repo state only:

```powershell
param([string]$ProjectRoot = (Get-Location))

$kit = "$env:USERPROFILE\cursor-kit"
New-Item -ItemType Directory -Force "$ProjectRoot\.cursor\state" | Out-Null

if (-not (Test-Path "$ProjectRoot\AGENTS.md")) {
  Copy-Item "$kit\AGENTS.md.template" "$ProjectRoot\AGENTS.md"
}
if (-not (Test-Path "$ProjectRoot\PROJECT.md")) {
  Copy-Item "$kit\PROJECT.md.template" "$ProjectRoot\PROJECT.md"
}
if (-not (Test-Path "$ProjectRoot\.cursor\state\checkpoint.json")) {
  Copy-Item "$kit\state\checkpoint.json.example" "$ProjectRoot\.cursor\state\checkpoint.json"
}

$gi = Join-Path $ProjectRoot ".gitignore"
$snippet = Get-Content "$kit\gitignore.snippet" -Raw
if (Test-Path $gi) {
  if (-not (Select-String -Path $gi -Pattern "checkpoint.json" -Quiet)) {
    Add-Content $gi "`n$snippet"
  }
} else {
  Set-Content $gi $snippet
}

Write-Host "cursor-kit installed in $ProjectRoot"
