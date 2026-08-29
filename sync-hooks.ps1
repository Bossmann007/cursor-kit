# Sync global hooks from cursor-kit source (run after editing hooks here)

$src = "$PSScriptRoot\hooks"
$dst = "$env:USERPROFILE\.cursor\hooks"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item "$src\*.py" $dst -Force
Write-Host "Synced hooks to $dst"
