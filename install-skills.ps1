# Install curated skills for Enzo (PUCPR + solo dev projects)
# See SKILLS-CURATED.md for mapping

param(
    [string]$TempDir = "$env:TEMP\cursor-skills-setup"
)

$skillsRepo = "https://github.com/mattpocock/skills.git"
$booksRepo = "https://github.com/mattpocock/agent-rules-books.git"
$skillsDst = "$env:USERPROFILE\.cursor\skills"
$rulesDst = "$env:USERPROFILE\.cursor\rules\books"

$mattAllow = @(
    'code-review','diagnosing-bugs','domain-modeling','grill-me','grill-with-docs',
    'grilling','handoff','implement','prototype','research','resolving-merge-conflicts',
    'setup-matt-pocock-skills','tdd','teach','to-spec','wait-what'
)

$bookAllow = @(
    'clean-code','refactoring','the-pragmatic-programmer',
    'working-effectively-with-legacy-code','domain-driven-design-distilled'
)

$cursorKitSkills = @(
    'blindspot-pass','context-engine','dev-workflow','find-skills',
    'project-brain','pucpr-canvas','pucpr-tutor','update-checkpoint'
)

New-Item -ItemType Directory -Force $TempDir, $rulesDst | Out-Null

function Ensure-Clone($url, $path) {
    if (-not (Test-Path $path)) { git clone --depth 1 $url $path }
}

Ensure-Clone $skillsRepo (Join-Path $TempDir "mattpocock-skills")
Ensure-Clone $booksRepo (Join-Path $TempDir "agent-rules-books")

# find-skills
npx skills add vercel-labs/skills@find-skills -y 2>$null
$findSrc = "$env:USERPROFILE\.agents\skills\find-skills"
if (Test-Path $findSrc) {
    $findDst = Join-Path $skillsDst "find-skills"
    if (Test-Path $findDst) { Remove-Item $findDst -Recurse -Force }
    Copy-Item $findSrc $findDst -Recurse -Force
}

# matt pocock — allowlist only
$src = Join-Path $TempDir "mattpocock-skills\skills"
$skip = @('deprecated', 'in-progress')
Get-ChildItem $src -Directory | Where-Object { $skip -notcontains $_.Name } | ForEach-Object {
    Get-ChildItem $_.FullName -Directory | ForEach-Object {
        if ($mattAllow -notcontains $_.Name) { return }
        if (-not (Test-Path (Join-Path $_.FullName 'SKILL.md'))) { return }
        $dest = Join-Path $skillsDst $_.Name
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item $_.FullName $dest -Recurse -Force
    }
}

# remove matt skills not in allowlist
Get-ChildItem $skillsDst -Directory | ForEach-Object {
    $n = $_.Name
    if ($cursorKitSkills -contains $n) { return }
    if ($mattAllow -contains $n) { return }
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "pruned skill: $n"
}

# book rules — allowlist only
$books = Join-Path $TempDir "agent-rules-books"
Get-ChildItem $books -Directory | Where-Object { $bookAllow -contains $_.Name } | ForEach-Object {
    $mini = Get-ChildItem $_.FullName -Filter "*.mini.md" | Select-Object -First 1
    if (-not $mini) { return }
    $name = $_.Name
    $title = ($name -replace '-', ' ')
    $body = Get-Content $mini.FullName -Raw
    $mdc = @"
---
description: Book rules ($title) — invoke for reviews, refactors, or modeling aligned with this book.
alwaysApply: false
---

# $title (mini)

$body
"@
    Set-Content -Path (Join-Path $rulesDst "$name.mdc") -Value $mdc -Encoding utf8
}

Get-ChildItem $rulesDst -Filter *.mdc | ForEach-Object {
    $base = $_.BaseName
    if ($bookAllow -notcontains $base) {
        Remove-Item $_.FullName -Force
        Write-Host "pruned book: $base"
    }
}

Write-Host "Done. See SKILLS-CURATED.md"
