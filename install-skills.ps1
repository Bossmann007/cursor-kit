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
    'find-skills','pucpr-canvas','pucpr-tutor'
)

# Skills that ship in the cursor-kit plugin — do NOT copy into ~/.cursor/skills
# when the local plugin is present (plugin is source of truth on desktop).
$pluginShippedSkills = @(
    'setup-project','setup-pucpr','setup-ai-memory','verification-planning','simplify','blindspot-pass'
)
$pluginSkillsDir = Join-Path $env:USERPROFILE ".cursor\plugins\local\cursor-kit\skills"
$pluginPresent = Test-Path (Join-Path $pluginSkillsDir "setup-project\SKILL.md")


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

# cursor-kit plugin skills: only copy to ~/.cursor/skills when plugin is absent
# (Cloud / machines without local plugin). Desktop prefers the plugin.
$kitSkillsSrc = Join-Path $PSScriptRoot "skills"
$forceUser = $env:FORCE_USER_SKILLS -eq "1"
if ((-not $pluginPresent -or $forceUser) -and (Test-Path $kitSkillsSrc)) {
    Get-ChildItem $kitSkillsSrc -Directory | ForEach-Object {
        if (-not (Test-Path (Join-Path $_.FullName 'SKILL.md'))) { return }
        $dest = Join-Path $skillsDst $_.Name
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item $_.FullName $dest -Recurse -Force
        Write-Host "kit skill (user-skills fallback): $($_.Name)"
    }
} elseif ($pluginPresent) {
    Write-Host "cursor-kit plugin present — not copying plugin skills into $skillsDst"
    # Drop stale user-skills copies of plugin-shipped names
    foreach ($n in $pluginShippedSkills) {
        $stale = Join-Path $skillsDst $n
        if (Test-Path $stale) {
            Remove-Item $stale -Recurse -Force
            Write-Host "removed stale user-skills duplicate: $n"
        }
    }
}

# remove matt skills not in allowlist (keep env + plugin-shipped if still present as fallback)
Get-ChildItem $skillsDst -Directory | ForEach-Object {
    $n = $_.Name
    if ($cursorKitSkills -contains $n) { return }
    if ($pluginShippedSkills -contains $n) { return }
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
