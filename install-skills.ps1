# Install mattpocock skills + agent-rules-books into ~/.cursor

param(
    [string]$TempDir = "$env:TEMP\cursor-skills-setup"
)

$skillsRepo = "https://github.com/mattpocock/skills.git"
$booksRepo = "https://github.com/mattpocock/agent-rules-books.git"
$skillsDst = "$env:USERPROFILE\.cursor\skills"
$rulesDst = "$env:USERPROFILE\.cursor\rules\books"

New-Item -ItemType Directory -Force $TempDir, $rulesDst | Out-Null

function Ensure-Clone($url, $path) {
    if (-not (Test-Path $path)) {
        git clone --depth 1 $url $path
    }
}

Ensure-Clone $skillsRepo (Join-Path $TempDir "mattpocock-skills")
Ensure-Clone $booksRepo (Join-Path $TempDir "agent-rules-books")

# find-skills (vercel-labs)
npx skills add vercel-labs/skills@find-skills -y 2>$null
if (Test-Path "$env:USERPROFILE\.agents\skills\find-skills") {
    Copy-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\find-skills" "$skillsDst\find-skills"
}

# mattpocock skills (full dirs)
$src = Join-Path $TempDir "mattpocock-skills\skills"
$skip = @('deprecated', 'in-progress')
Get-ChildItem $src -Directory | Where-Object { $skip -notcontains $_.Name } | ForEach-Object {
    Get-ChildItem $_.FullName -Directory | ForEach-Object {
        if (Test-Path (Join-Path $_.FullName 'SKILL.md')) {
            Copy-Item $_.FullName (Join-Path $skillsDst $_.Name) -Recurse -Force
        }
    }
}

# book rules (mini -> mdc)
$books = Join-Path $TempDir "agent-rules-books"
Get-ChildItem $books -Directory | Where-Object { $_.Name -notmatch '^(docs|_rule-workbench)$' } | ForEach-Object {
    $mini = Get-ChildItem $_.FullName -Filter "*.mini.md" | Select-Object -First 1
    if (-not $mini) { return }
    $name = $_.Name
    $title = ($name -replace '-', ' ')
    $body = Get-Content $mini.FullName -Raw
    $mdc = @"
---
description: Book rules ($title) — reviews, refactors, architecture aligned with this book.
alwaysApply: false
---

# $title (mini)

$body
"@
    Set-Content -Path (Join-Path $rulesDst "$name.mdc") -Value $mdc -Encoding utf8
}

Write-Host "Skills: $skillsDst"
Write-Host "Book rules: $rulesDst"
Write-Host "Run setup-matt-pocock-skills once per repo in Cursor."
