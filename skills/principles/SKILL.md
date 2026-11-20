---
name: principles
description: >
  Default approaches with when to do differently and how to check them. Part A, Engineering: KISS, size first, done
  has proof, small PRs, reuse, guards as tools, pinned versions, Hyrum, Postel (RFC 9413), Goodhart, Gall, YAGNI,
  Chesterton, Lindy, bus factor. Part B, Work and life: deadlines, study, projects, relationships, money, health,
  numbers. Use when choosing a design (emode Size/Decision), before review (emode Verify), in senior-check, or on
  "princípios", "boas práticas", "KISS", "estamos complicando?".
---

# principles

These are defaults, not laws: a different choice is fine when it is deliberate and written down (ADR or PR body)
with the reason. A law is not an excuse either: "it's Parkinson" does not replace a plan. Review now and then
whether you used the default or chose otherwise on purpose, and why; keep, adjust or drop items from that.

## A. Engineering

Each block: **Default**, **Different when**, **Check** (a command, a file, or a reviewer question).

### 1. KISS: the simplest thing that solves it

- Default: fewest parts, least config, least code. If config grows, stop and simplify first. Clever code only where
  performance was measured, with a comment ([Kernighan](https://lawsofsoftwareengineering.com/laws/kernighans-law/)).
  Complexity only moves ([Tesler](https://lawsofsoftwareengineering.com/laws/teslers-law/)): choose who pays it.
  Source: [KISS](https://en.wikipedia.org/wiki/KISS_principle). Removing first: pstack `principle-subtract-before-you-add`.
- Different when: security, data formats and consent need the extra care even if less simple.
- Check: "can one part, flag or file go and it still works?"

### 2. Size first; large work needs an approved SPEC; docs in the same PR

- Default: say small, medium or large before coding. Large gets `SPEC.md` (in, out, how to verify) and code starts
  only with an `Approved: <name> <date>` line. SPEC, ADR and README change in the same PR as the behavior. Source:
  emode + [Hofstadter](https://lawsofsoftwareengineering.com/laws/hofstadters-law/).
- Different when: a one-line fix or small task: do it and run the check.
- Check: `grep -n '^Approved:' SPEC.md`; the PR diff touches the docs its behavior changes.

### 3. Done has proof: verify exit 0 and a review of the exact head

- Default: built = `scripts/verify` exit 0 with the output shown; done = a real user used it on a real case. Built is
  not done. Merge only with a review of the exact commit and verify green on it; nothing pushed after the review.
  Source: emode + [90-90 rule](https://lawsofsoftwareengineering.com/laws/ninety-ninety-rule/). Method: pstack
  `principle-prove-it-works`.
- Different when: a throwaway draft or prototype, marked as such.
- Check: `scripts/verify; echo $?` prints 0; the reviewed SHA equals `git rev-parse HEAD`.

### 4. Small PRs, about 400 lines at most

- Default: past ~400 changed lines, split into slices that stand alone. Big PRs slow review and hide bugs; when
  behind, cut scope ([Brooks](https://lawsofsoftwareengineering.com/laws/brooks-law/)).
- Different when: generated files (lockfile, auto migration) or a mechanical rename, explained in the PR body.
- Check: `git diff --stat <default-branch>...HEAD | tail -1`.

### 5. Reuse, don't copy

- Default: the same script or logic in two places means import or call the original; copies drift
  ([DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)). Example: a copied verify script went stale in an hour.
- Different when: two things only look alike today and will change for different reasons; then a copy beats coupling.
- Check: "is there already a file, function or skill that does this?" (`grep -rn`, `/prior-art-check`).

### 6. The guard is a tool, not goodwill

- Default: a rule that matters becomes an automatic check (verify, hook, CI) that fails on its own, e.g. verify rejects
  an AI co-author trailer. What can fail once will ([Murphy](https://lawsofsoftwareengineering.com/laws/murphys-law/),
  as margin). When it broke: pstack `principle-fix-root-causes`.
- Different when: a harmless style preference; it stays in the rule text.
- Check: "which command fails if this rule is broken?" No command, no guard.

### 7. Pinned versions

- Default: dependencies locked with versions and hashes (e.g. `uv.lock`), GitHub Actions by SHA, language version
  pinned. Upgrading is a deliberate change in its own PR. Source: `senior-check` dependency checks + Lindy (below).
- Different when: a one-afternoon local experiment.
- Check: `senior-check` lockfile and runtime lines; `grep -n 'uses:' .github/workflows/*` shows SHAs.

### 8. Public behavior changes on purpose

- Default: an API, CLI flag or file format others use changes only with a new version and a CHANGELOG line
  ([Hyrum](https://lawsofsoftwareengineering.com/laws/hyrums-law/)).
- Different when: nobody uses it but you.
- Check: the PR that changes public behavior also bumps the version and edits `CHANGELOG.md`.

### 9. Accept the standard format, refuse the rest with a clear error

- Default: unexpected input returns an explained error instead of a guess. Never relax validation, approvals or
  injection guards. [Postel](https://lawsofsoftwareengineering.com/laws/postels-law/) as revised by
  [RFC 9413](https://www.rfc-editor.org/rfc/rfc9413): too much tolerance locks you into others' bugs.
- Different when: reading messy data only to display it, where accepting it is harmless; mark it '?'.
- Check: a test that feeds bad input and asserts the error message.

### 10. The metric is not the goal

- Default: coverage, benchmark scores and test counts are for conversation; before celebrating, check the number
  still tracks the goal ([Goodhart](https://lawsofsoftwareengineering.com/laws/goodharts-law/)).
- Different when: the number is the contract itself (an agreed max latency, a size limit).
- Check: "if this number improved and the goal did not, how would we notice?"

### Also (one line each)

- [Gall](https://lawsofsoftwareengineering.com/laws/galls-law/): the smallest end-to-end version works before it grows; differ when a mature system already exists to reuse.
- [YAGNI](https://lawsofsoftwareengineering.com/laws/yagni/): no feature or abstraction without a use today, except data formats, security, consent.
- [Chesterton](https://en.wikipedia.org/wiki/Chesterton%27s_fence): know why something exists before removing it, unless you made it recently and know.
- [Lindy](https://lawsofsoftwareengineering.com/laws/lindy-effect/): mature dependencies by default; a new one needs an ADR saying why.
- [Bus factor](https://lawsofsoftwareengineering.com/laws/bus-factor/): how to run, deploy and recover is written (README, runbook), not only in a head.

## B. Work and life

Each line: the default (the law, linked); when to differ.

- **Time and deadlines**: estimate, double it, and book the first work block right away
  ([Hofstadter](https://lawsofsoftwareengineering.com/laws/hofstadters-law/), [planning fallacy](https://en.wikipedia.org/wiki/Planning_fallacy));
  differ for a task done many times, where the real average holds. Give open-ended tasks a short explicit timebox
  ([Parkinson](https://lawsofsoftwareengineering.com/laws/parkinsons-law/)); differ when depth is the goal. Keep a
  day of slack and a plan B for deliveries that matter ([Murphy](https://lawsofsoftwareengineering.com/laws/murphys-law/), as margin); differ when redoing is cheap.
- **Study**: practice with feedback over passive watching ([deliberate practice](https://en.wikipedia.org/wiki/Practice_(learning_method)));
  differ on first contact with a topic. Start with the 20% that matters most ([Pareto](https://lawsofsoftwareengineering.com/laws/pareto-principle/));
  differ for foundational subjects, where the rest matters too.
- **Projects**: a small fixed number of active fronts; a new idea waits in a queue; delays are fixed by cutting scope
  ([Brooks](https://lawsofsoftwareengineering.com/laws/brooks-law/), [opportunity cost](https://en.wikipedia.org/wiki/Opportunity_cost));
  differ for a short-lived opportunity with a clear owner, which swaps places with a front instead of adding one. For a
  stalled project ask "would I start this today?" ([sunk cost](https://lawsofsoftwareengineering.com/laws/sunk-cost-fallacy/));
  differ when it is hours from a useful delivery. Design how the parts should talk before building a team or system
  ([Conway](https://lawsofsoftwareengineering.com/laws/conways-law/)); differ for short solo work.
- **Relationships and career**: cooperate first, warn once, return to cooperating ([tit-for-tat](https://en.wikipedia.org/wiki/Tit_for_tat));
  differ after a repeated serious breach or fraud. Before an "extra", ask "would I do this every time?"
  ([Hyrum](https://lawsofsoftwareengineering.com/laws/hyrums-law/)); differ when you want that expectation. Be tolerant
  in what you receive and careful in what you deliver ([Postel](https://lawsofsoftwareengineering.com/laws/postels-law/));
  differ for security and money, where vague input is refused.
- **Money**: pay the full card balance, never the minimum, and move a small fixed share to savings the day income
  arrives ([compound interest](https://en.wikipedia.org/wiki/Compound_interest)); differ in a real health or family emergency.
- **Health and sleep**: fixed exercise slots and a sleep cutoff; work that misses the cutoff means the estimate failed
  ([deliberate practice](https://en.wikipedia.org/wiki/Practice_(learning_method)), [compound interest](https://en.wikipedia.org/wiki/Compound_interest));
  differ for a single chosen night, never as a deadline habit.
- **Numbers and news**: before chasing a number or trusting a statistic, ask if it became an empty target, and find the
  primary source ([Goodhart](https://lawsofsoftwareengineering.com/laws/goodharts-law/), [Campbell](https://en.wikipedia.org/wiki/Campbell%27s_law));
  differ when the number is the goal itself.
