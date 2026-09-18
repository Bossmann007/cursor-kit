---
name: verification-planning
description: >
  Build a project-specific evidence path before non-trivial implement or when
  confidence claims need proof. Use before features, bug fixes, refactors,
  cross-system changes, or high-confidence behavior claims — and when the user
  says verify, evidence path, how do we prove, or verification plan. Prefer this
  over inventing tests without tying them to a claim. Complements blindspot-pass
  (after) and quality-gates (measure-only). Skip for tiny mechanical edits.
disable-model-invocation: false
---

# Verification planning

Before changing a non-trivial system, build an **evidence path**: a route from
the claim to evidence that can establish, limit, or refute it.

Purpose is not picking a familiar technique. Purpose is deciding how *this*
system can reveal the truth of *this* change.

Stack defaults (Bossmann Cursor):

- Explore via **codebase-memory** (`search_graph` / `trace_path` / `get_code_snippet`)
- Compress large logs via **token-engine**
- Record the plan in `.cursor/state/checkpoint.json` (`tests`, `next_action`)
- Prefer **measure-only** quality gates; do not autofix unless the user asks
- After the path runs, optional `/blindspot-pass` for missed edges

## When to skip

Small mechanical edits with an obvious existing check (one-liner, rename with
types green). Follow ordinary project commands directly.

## Process

### 1. Frame the claim

State the behavior that must become true and what could make a confident
conclusion wrong.

Name:

- what must change
- what must remain true
- which boundary the behavior crosses
- which failure would matter most

**Done when:** claim, uncertainty, and important failure modes are concrete.

### 2. Design the evidence path

Derive paths from the system itself: controllable inputs, observable effects,
state transitions, invariants, boundaries, artifacts, repeat/reverse ability.

Generate alternatives before choosing. Prefer the path that yields a
trustworthy conclusion with proportionate cost and safety.

**Done when:** preferred path + known limits + a weaker/stronger fallback exist.

### 3. Set a verification budget

List distinct claims. Assign one owner (agent step or command) per claim.
Choose the minimum non-duplicative evidence. Reuse evidence only while code,
inputs, environment, and state stay valid. Required repo/CI checks still apply.

### 4. Create a verification affordance when needed

If the decisive truth is too indirect, add the **smallest** capability that
makes the relevant state controllable, observable, repeatable, and diagnosable
for an agent (fixture, demo script, assert, narrow probe).

Treat the affordance as part of the evidence path, not an automatic product
feature. Decide temporary vs durable before building. Ask before new
dependencies or persistent diagnostic surfaces.

### 5. Make the path runnable

Prepare only narrow, repeatable support. Prefer commands already in
`PROJECT.md`. Write the chosen commands into checkpoint `tests`.

**Done when:** the path can be followed without guessing setup or interpretation.

### 6. Close the evidence path

After implementation, follow the planned path. Report whether each claim was
**established**, **limited**, or **refuted**. Separate known facts from remaining
uncertainty. No completion claims without fresh evidence (same spirit as
superpowers verification-before-completion).

## Output (compact)

```text
Claim: <behavior>
Uncertainty: <what could make confidence wrong>
Evidence path: <commands / checks / affordance>
Budget: <min checks; what skipped and why>
Status: established | limited | refuted | not-run-yet
```

## Compose with

| Skill / tool | Role |
|--------------|------|
| `dev-workflow` / `/poteto-mode` | Call this in PLAN (or before IMPLEMENT) for non-trivial work |
| `blindspot-pass` | Second pass after the path runs |
| `simplify` | Only after behavior is proven |
| quality-gates templates | Measure-only static gates — not a substitute for the claim |
| checkpoint | Persist `tests` + `next_action` in `.cursor/state/checkpoint.json` (agent owns semantics; hooks merge files) |
