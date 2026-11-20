---
name: performance
description: >
  Make an app faster and lighter with evidence: set a budget, measure a baseline, find the limiter, change one thing,
  measure again, and lock the win into scripts/verify. Covers start time, latency, memory, bundle and binary size,
  queries, CPU, energy and token or API cost. Use on "performance", "otimizar", "mais rápido", "mais leve",
  "está lento", "usa muita memória", "bundle grande", or when emode reaches a step with a performance goal.
---

# performance

Rule: no number, no claim. Measure, find the limiter, change one thing, measure again (Kernighan: simple code unless
the measurement says otherwise). Regressions with an unknown cause go to `diagnosing-bugs` (its perf branch) first.

## 1. Budget (before touching code)

Pick what the user feels, not what is easy to count: the file they open, the screen they wait on, the machine it runs
on (the Nonno's PC, a phone on 4G), and write 1-3 budgets as sentences you would ship, e.g. "cold start under 1.5 s
on the target PC", "p95 /api/casos under 200 ms with 10k rows", "JS bundle under 200 kB gzip". No target from the
user: propose one from the current baseline and say it is a proposal.

## 2. Baseline (real run, same conditions every time)

Release build, production flags, realistic data, warm and cold where both matter, 5+ runs, median and p95.
Tools by kind (use what the project already has first):

| Kind | Measure | Find the limiter |
|---|---|---|
| CLI / process | `hyperfine`, `/usr/bin/time -l` (macOS RSS) | `py-spy`, `node --cpu-prof`, `perf`/`samply` |
| Web front | Lighthouse CI, `vite build` size report, `source-map-explorer` | Chrome Performance panel, bundle analyzer |
| API / server | `autocannon`, `k6`, `oha` | flame graph, query log, `EXPLAIN ANALYZE` |
| Database | query timings on seeded data | `EXPLAIN (ANALYZE, BUFFERS)`, missing index, N+1 |
| .NET / desktop | `dotnet-counters`, startup stopwatch | `dotnet-trace`, PerfView; AOT and trimming size |
| LLM / agents | tokens and cost per task, latency per call | prompt size, cache hits, calls per task |

## 3. One change at a time

Order of attack (cheapest win first): do less work (remove, cache, batch, index, lazy-load), then do it in a better
place (DB instead of app, build time instead of run time), then do it faster (algorithm, data structure), and only
last more hardware or concurrency. Each change: measure again on the same setup; keep it only if it moves the budget
metric beyond run-to-run noise. Revert changes that did not help (subtract before you add).

## 4. Prove it (before reporting a number)

Read pstack `benchmark-checklist` (installPath of `pstack@cursor-plugins`, `skills/benchmark-checklist/SKILL.md`)
and answer its questions for the claim. Report: budget, before, after, runs, machine, command to reproduce.
Never round a 3% change up to "faster"; noise is "no change".

## 5. Lock it in

Add the cheapest guard that fails when the win is lost: a size check, a timing test with headroom, a query-count
assertion, or a Lighthouse budget, called from `scripts/verify` (or CI when it is too slow for local). Write the
budget and its reason in the README or an ADR, so the next change knows it exists.

## Out of scope

No micro-tuning without a budget; no rewrite in another language or stack without `/emode` Decision route; no
trading correctness, security or readability for a gain the user cannot feel.
