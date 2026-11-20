---
name: senior-check
description: >
  Read-only audit of whether a repo is built the way a senior engineer would: process (emode steps, verify, CI, PR
  flow), versions (lockfile, pinned runtime, tags matching the manifest, changelog), docs (README, SPEC, ADRs),
  git hygiene, secrets, and the default approaches in `principles` part A. Use on "senior check", "estamos fazendo
  certo?", "boas práticas", "auditoria do projeto", before a PR that ends a phase, or when emode §5 calls it.
---

# senior-check

Answers one question with evidence: "is this repo being built the way a senior engineer would, by our own rules?"
It reports and never edits tracked files; `--run-verify` runs the repo's own `scripts/verify`, which may write (the
script reports leftovers). Fixes go through `/emode` like any other change.

## 1. Run the script (facts first)

`scripts/senior-check.sh <repo> --run-verify` (from this skill folder; any path inside the repo works). One line per
check: PASS / WARN / FAIL with evidence; exit 0 = no FAIL, 1 = FAIL, 2 = bad usage. Never restate a line the script did not
print. It checks the repo root only: a monorepo's sub-packages need a manual look.

- FAIL: blocks closing the phase, not the "built" of one change (no verify, verify red, commits only on this disk,
  most recent commits on the default branch without a PR, manifest without a committed lockfile, no README, secret
  in history).
- WARN: a gap a senior would close soon (no CI, runtime not pinned, tag behind the manifest, no CHANGELOG, no ADRs,
  SPEC without `Approved:`, a few direct commits: rebase-merged PRs look direct, so confirm before reporting).
- gitleaks FAIL: triage with `gitleaks git . --redact -v` before you report it; a demo fixture is a false positive,
  a real key means "tell Enzo to rotate it" (never print the value). A triaged false positive goes to
  `.gitleaksignore` by fingerprint, in a PR.

## 2. Judge what a script cannot (read, then cite `file:line`)

Only for the current phase or the open PR, not the whole history:

1. **emode was followed**: SPEC written and approved before code; scope frozen during the PR; docs (SPEC, ADR,
   README) changed in the same PR as the behavior; `blindspot-pass` and a fresh review on large changes.
2. **Tests prove behavior**: new behavior has a test that would fail without it; no skipped or deleted tests to get green.
3. **Dependencies**: run the ecosystem's audit (`npm audit --omit=dev`, `uv pip list --outdated` or `pip-audit`,
   `dotnet list package --vulnerable`); report high/critical only. A major version behind with a known CVE is a FAIL.
4. **Default approaches**: `principles` part A (Engineering); check the ones that apply to code. Each is a default,
   not a law: a different choice is fine when it is written down (ADR or PR body) with the reason.
5. **Performance**: if the project has a budget, it is checked in `scripts/verify`; if not, say so (see `performance`).

## 3. Report

Lead with the verdict (`pronto para seguir` / `seguir depois de N correções`), then at most 5 findings, worst first,
each as cause and fix with evidence (script line or `file:line`). End with the one next step. A finding that needs
code becomes an `/emode` task (T3 Code brief), not a fix inside this skill.
