---
name: blindspot-pass
description: >
  Second-pass review for missed edge cases, security, and silent failures before
  shipping. Use after the main fix/feature looks done, or when the user says
  blindspot, second pass, or what did we miss. Complements verification-planning
  (evidence path before/during) — do not invent scope.
disable-model-invocation: false
---

# Blindspot pass

After the main fix/feature looks done:

1. Confirm the **evidence path** from `/verification-planning` (or checkpoint
   `tests`) was run with fresh results — if no path exists for non-trivial work,
   draft one first
2. List assumptions that were not verified
3. Check error paths, empty inputs, auth / trust boundaries
4. Confirm tests cover the failure mode, not only the happy path
5. Fix only real gaps; do not invent scope
