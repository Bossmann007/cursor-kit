#!/usr/bin/env bash
# Senior-engineering audit of one git repo. Prints one line per check: PASS / WARN / FAIL + evidence.
# Edits no tracked file. --run-verify runs the repo's own scripts/verify (which may write) after the git checks,
# and reports any file it leaves behind. Exit 0 = no FAIL, 1 = at least one FAIL, 2 = bad usage.
# Usage: senior-check.sh <repo-dir> [--run-verify]
set -uo pipefail
shopt -s nullglob
usage() { echo "usage: senior-check.sh <git-repo-dir> [--run-verify]" >&2; exit 2; }
[[ $# -ge 1 && $# -le 2 ]] || usage
repo="$1"; run_verify=0
if [[ $# -eq 2 ]]; then [[ "$2" == --run-verify ]] && run_verify=1 || usage; fi
[[ -d "$repo" ]] || usage
top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || usage
cd "$top" || usage
fails=0
out() { printf '%-4s %-22s %s\n' "$1" "$2" "$3"; [[ "$1" == FAIL ]] && fails=$((fails+1)); return 0; }
tracked() { git ls-files --error-unmatch "$1" >/dev/null 2>&1; }

def=$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
[[ -n "$def" ]] || def=$(git rev-parse -q --verify origin/main >/dev/null && echo main || echo master)
branch=$(git branch --show-current 2>/dev/null)
has_origin=0; git rev-parse -q --verify "origin/$def" >/dev/null && has_origin=1

# 1. Git hygiene first, before anything (verify included) can touch the tree.
before=$(git status --porcelain)
dirty=$(printf '%s' "$before" | grep -c .)
[[ "$dirty" -eq 0 ]] && out PASS worktree "clean" || out WARN worktree "$dirty uncommitted paths on branch ${branch:-detached}"
if unpushed=$(git rev-list --count '@{u}..HEAD' 2>/dev/null); then :
elif [[ $has_origin -eq 1 ]]; then unpushed=$(git rev-list --count "origin/$def..HEAD")
else
  n=$(git rev-list --count HEAD 2>/dev/null || echo 0)
  [[ "$n" -eq 0 ]] && out WARN pushed "no commits and no remote" || out FAIL pushed "no remote: $n commits only on this disk"
  unpushed=-1
fi
if [[ "$unpushed" -ge 0 ]]; then
  [[ "$unpushed" -eq 0 ]] && out PASS pushed "no local-only commits" || out FAIL pushed "$unpushed commits not on the remote"
fi
[[ "$branch" == "$def" && "$dirty" -gt 0 ]] && out FAIL on-default "editing directly on $def"

# 2. Process: work ships by PR, CI runs, one command proves health.
if [[ $has_origin -eq 0 ]]; then out WARN pr-flow "no origin/$def to check (no remote or not fetched)"
else
  # First-parent history: a merge commit (2 parents) or a "(#N)" subject is a PR; anything else looks direct.
  # Rebase-merged PRs look direct too, so only a clear majority is a FAIL.
  direct=$(git log --first-parent --format='%P%x09%s' -20 "origin/$def" | awk -F'\t' '{ if (split($1,p," ")<2 && $2 !~ /\(#[0-9]+\)$/) n++ } END { print n+0 }')
  total=$(git log --first-parent --oneline -20 "origin/$def" | grep -c .)
  if [[ "$direct" -le 2 ]]; then out PASS pr-flow "$direct/$total recent commits on $def outside a PR"
  elif [[ "$direct" -le 10 ]]; then out WARN pr-flow "$direct/$total recent commits on $def look direct (rebase-merged PRs count here)"
  else out FAIL pr-flow "$direct/$total recent commits pushed to $def without a PR"; fi
fi
ci=(.github/workflows/*.yml .github/workflows/*.yaml)
[[ ${#ci[@]} -gt 0 ]] && out PASS ci "${ci[*]}" || out WARN ci "no GitHub Actions workflow"
if [[ -x scripts/verify ]]; then
  if [[ $run_verify -eq 1 ]]; then
    if log=$(mktemp "${TMPDIR:-/tmp}/senior-check.XXXXXX"); then
      scripts/verify >"$log" 2>&1; rc=$?
      [[ $rc -eq 0 ]] && out PASS verify "scripts/verify exit 0" || out FAIL verify "scripts/verify exit $rc (log: $log)"
      [[ "$(git status --porcelain)" == "$before" ]] || out WARN verify-clean "scripts/verify left changed or untracked files (git status)"
    else out FAIL verify "could not create a log file; verify not run"; fi
  else out PASS verify "scripts/verify exists (pass --run-verify to run it)"; fi
else out FAIL verify "no executable scripts/verify"; fi

# 3. Versions: reproducible installs, a pinned runtime, releases that match the manifest. Root of the repo only.
manifest=(); lockreq=()
[[ -f package.json ]] && manifest+=(package.json)
[[ -f pyproject.toml ]] && grep -qE '^dependencies *=|^\[tool\.poetry\.dependencies\]|^\[project\.optional-dependencies\]|^\[dependency-groups\]' pyproject.toml && manifest+=(pyproject.toml)
for f in Cargo.toml go.mod requirements*.txt; do [[ -f $f ]] && manifest+=("$f"); done
have=(); for f in package-lock.json pnpm-lock.yaml yarn.lock bun.lock bun.lockb uv.lock poetry.lock Cargo.lock go.sum packages.lock.json; do tracked "$f" && have+=("$f"); done
for f in requirements*.txt; do
  tracked "$f" && ! grep -vE '^\s*(#|$|-)' "$f" | grep -qv '==' && have+=("$f (all pinned)")
done
csproj=(*.csproj)
if [[ ${#manifest[@]} -eq 0 && ${#csproj[@]} -eq 0 ]]; then out PASS lockfile "no dependency manifest at the root"
elif [[ ${#have[@]} -gt 0 ]]; then out PASS lockfile "${have[*]}"
elif [[ ${#manifest[@]} -eq 0 ]]; then out WARN lockfile ".NET project without packages.lock.json (opt-in)"
else out FAIL lockfile "${manifest[*]} without a committed lockfile"; fi
pin=(); for f in .nvmrc .node-version .python-version .tool-versions global.json rust-toolchain.toml mise.toml; do [[ -f $f ]] && pin+=("$f"); done
grep -q '"engines"' package.json 2>/dev/null && pin+=("package.json engines")
grep -q 'requires-python' pyproject.toml 2>/dev/null && pin+=("requires-python")
[[ ${#pin[@]} -gt 0 ]] && out PASS runtime-pin "${pin[*]}" || out WARN runtime-pin "runtime version not pinned"
ver=""; [[ -f package.json ]] && ver=$(python3 -c 'import json;print(json.load(open("package.json")).get("version",""))' 2>/dev/null)
[[ -z "$ver" && -f pyproject.toml ]] && ver=$(sed -n 's/^version *= *"\([^"]*\)".*/\1/p' pyproject.toml | head -1)
lasttag=$(git describe --tags --abbrev=0 2>/dev/null)
if [[ -n "$ver" ]]; then
  [[ "${lasttag#v}" == "$ver" ]] && out PASS release-tag "v$ver tagged" || out WARN release-tag "manifest $ver, last tag '${lasttag:-none}'"
  [[ -f CHANGELOG.md ]] && out PASS changelog "CHANGELOG.md" || out WARN changelog "versioned project without CHANGELOG.md"
fi

# 4. Docs a senior leaves behind: how to run it, what it is for, why it is built this way.
readme=(README.*); [[ -f README ]] && readme+=(README)
[[ ${#readme[@]} -gt 0 ]] && out PASS readme "${readme[0]}" || out FAIL readme "no README"
s=(); for f in SPEC.md PROJECT.md docs/SPEC.md; do [[ -f $f ]] && s+=("$f"); done
[[ ${#s[@]} -gt 0 ]] && out PASS spec "${s[*]}" || out WARN spec "no SPEC.md or PROJECT.md"
adr=(docs/adr/*.md docs/decisions/*.md)
[[ ${#adr[@]} -gt 0 ]] && out PASS adr "${#adr[@]} decision records" || out WARN adr "no ADRs (docs/adr/)"
if [[ -f SPEC.md ]]; then grep -q '^Approved: ' SPEC.md && out PASS spec-approved "$(grep -m1 '^Approved: ' SPEC.md)" || out WARN spec-approved "SPEC.md has no 'Approved:' line"; fi

# 5. Safety: no secret in the history (.gitleaksignore holds triaged false positives).
if command -v gitleaks >/dev/null; then
  gitleaks git . --no-banner --redact >/dev/null 2>&1 && out PASS secrets "gitleaks: no leaks in history" \
    || out FAIL secrets "gitleaks flagged history; triage: gitleaks git . --redact -v (fixtures can be false positives)"
else out WARN secrets "gitleaks not installed"; fi

echo "---"; echo "$fails FAIL"
[[ $fails -eq 0 ]]
