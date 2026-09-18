---
name: simplify
description: >
  Reduce complexity while preserving exact behavior. Use after a feature works
  and tests pass, during review when readability is flagged, or when nested
  logic / long functions / unclear names need cleanup — and when the user says
  simplify, declutter, readability, or reduce complexity. Complements deslop
  (AI-slop cleanup) and ponytail (minimum code up front). Do not use before
  understanding the code, or on already-clear code.
disable-model-invocation: false
---

# Simplify

Goal is not fewer lines. Goal is code a new reader understands faster than the
original — with **identical** behavior.

Inspired by common simplification playbooks (e.g. Osmani-style checklists);
this skill is Bossmann/cursor-kit native, not a vendored third-party copy.

## When to use

- Feature works and checks pass, but the implementation feels heavy
- Review flagged readability or complexity
- Deep nesting, long functions, unclear names, scattered duplication
- After merges that introduced inconsistency

## When not to use

- Code is already clear — do not simplify for its own sake
- Behavior is not understood yet — comprehend first (CBM / callers)
- Hot path where a simpler form would be measurably slower (prove with evidence)
- Behavior still unproven — run `/verification-planning` (or existing tests) first

## Principles

1. **Preserve behavior exactly** — same inputs, outputs, errors, side effects,
   ordering. If unsure, do not change.
2. **Follow project conventions** — match local naming, layering, and style.
3. **Reduce nesting and indirection** — early returns; delete one-caller wrappers
   that add no meaning (ponytail / minimize reader load).
4. **Names over comments** — rename; do not add narrating comments.
5. **Smallest useful diff** — no drive-by rewrites outside the task scope.

## Process

1. Understand responsibility, callers/callees, edge cases, and existing tests
   (prefer codebase-memory over whole-file reads).
2. List candidate simplifications; keep only those that preserve behavior.
3. Apply one coherent pass; avoid mixed refactors + feature work.
4. Re-run the evidence path / project checks from `PROJECT.md` or checkpoint
   `tests`. Do not claim done without fresh evidence.
5. Optional `/blindspot-pass` if the touch touched trust boundaries.

## Compose with

| Skill | Role |
|-------|------|
| `deslop` (cursor-team-kit) | Remove AI-generated slop on a branch diff |
| `verification-planning` | Prove behavior before / after simplify |
| `blindspot-pass` | Missed edges after cleanup |
| ponytail rule | Prefer never writing the complexity initially |

## Done checklist

- [ ] Existing tests / evidence path still pass without changing assertions for convenience
- [ ] Build / typecheck / lint still pass when the project has them
- [ ] Diff is scoped; no unrelated renames
