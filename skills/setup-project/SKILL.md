---
name: setup-project
description: >
  Bootstrap or repair a repo for the Bossmann Cursor stack (cursor-kit templates,
  token-engine, pstack models, Matt Pocock engineering skills, cursor-team-kit,
  continual-learning, verification-planning, simplify, blindspot-pass). Use
  whenever the user asks to set up / setar / scaffold a project or repo for
  agents, wire AGENTS.md + PROJECT.md + .cursor/state, run first-time Cursor kit
  install, or says the repo is missing agent memory, checkpoints, docs/agents, or
  stack integration — even if they do not say "setup-project". Prefer this over
  ad-hoc copying of templates.
disable-model-invocation: false
---

# Setup project

Orchestrate one coherent per-repo setup on top of the global Cursor environment.
Compose existing skills and templates — do not rewrite them inline.

Canonical kit root: `~/cursor-kit` (symlink to this repo when installed that way).
If missing, resolve from the plugin/repo path that contains `AGENTS.md.template`.

Read `references/layers.md` before writing files so global vs per-repo stays clear.

## Locked decisions (this skill)

- **A2**: per-repo setup + **global repair** when MCP / hooks / pstack rule are missing
- **B3**: support **new empty repo** and **existing workspace** — ask which at start
- **C**: ask interview depth **1 (minimal)** or **2 (completo)** before phase 2+
- Idempotent: never clobber filled `AGENTS.md` / `PROJECT.md`; only create or fill gaps
- Portuguese OK in chat; keep paths, identifiers, and file contents in English unless the target project is PT-first

## Process

### 0. Mode + interview depth

Ask two questions up front (one answer each; lead with the recommended default):

1. **Target mode** (recommended: existing workspace if a project root is already open)
   - **Existing repo** — scaffold into the current project root
   - **New repo** — confirm name + parent dir (prefer `~/Projects/` or `~/Developer/` if present, else `~`), create dir, `git init`, then `move_agent_to_root` into it **before** writing files

2. **Interview depth**
   - **1 — Minimal**: issue tracker (via Matt Pocock setup) + "fill PROJECT.md now?"
   - **2 — Completo**: everything in 1, plus confirm stack summary, offer codebase-memory index, note poteto/pstack as default for non-trivial work, **offer quality gates** for JS/TS (measure-only; point at kit playbook + `docs/prompts/05-quality-gates-install.md`), **arrumar ai-memory** (install/repair companion via `/setup-ai-memory`; see §6c), remind kit skills `verification-planning` + `simplify` + `blindspot-pass`, and point at `docs/02-playbook-onboarding.md` for the stranger path

If the user already stated mode/depth in the trigger message, skip the matching question.

### 1. Global pré-check (repair only if broken)

Check, do not duplicate:

| Check | Healthy signal | Repair |
|-------|----------------|--------|
| pstack models | `~/.cursor/rules/pstack-models.mdc` exists | Follow `/setup-pstack` (detect models → confirm → write rule) |
| token-engine MCP | `~/.cursor/mcp.json` has `token-engine` pointing at a real Python/venv | Point at `~/token-engine` / `~/.cursor/repos/token-engine`; remind user to enable MCP + reload if needed |
| Hooks | `~/.cursor/hooks.json` has sessionStart / postToolUse / stop | Restore via kit `./sync-hooks.sh` (**merge-safe** — preserves companions like ai-memory); do not invent a second hook system inside the repo; do not overwrite hooks.json from scratch when companions are present |
| ai-memory companion | Binary on PATH or `~/Applications/ai-memory/ai-memory`; `curl` `http://127.0.0.1:49374/mcp` → 405; MCP `ai-memory` in `~/.cursor/mcp.json`; hooks.json has kit **and** ai-memory commands | **Repair if broken** via `/setup-ai-memory` (or `scripts/install-ai-memory.sh`). If never installed: depth 1 → one-line note + skip; depth 2 → install/repair in §6c (default recommend yes on this stack). Keep AGENTS/PROJECT/checkpoint authoritative |
| Plugins | cursor-team-kit, continual-learning, pstack available | If missing, tell user to `/add-plugin` (or install this `cursor-kit` plugin); do not fake plugin install |

Summarize what was OK vs repaired in one short block before continuing.

### 2. Cursor-kit scaffold (idempotent)

From kit templates (`AGENTS.md.template`, `PROJECT.md.template`, `state/checkpoint.json.example`, `gitignore.snippet`):

1. Ensure `.cursor/state/` exists
2. Create `AGENTS.md` only if absent — continual-learning sections only:
   - `## Learned User Preferences`
   - `## Learned Workspace Facts`
3. Create `PROJECT.md` only if absent
4. Create `.cursor/state/checkpoint.json` only if absent
5. Append kit gitignore snippet if `checkpoint.json` ignore is missing

Prefer the kit's `install.sh` when the machine has `~/cursor-kit` linked; otherwise copy the same files from this plugin repo root.

Do **not** copy global `~/.cursor/rules` into the project.

### 3. Project brain

If `PROJECT.md` is still template-empty, or the user said yes to filling it:

- Derive stack/commands from manifests (`package.json`, `pyproject.toml`, README, CI)
- Keep the Decisions table for approved architecture only
- Never store secrets

Depth **1**: ask before filling an existing non-empty `PROJECT.md`.
Depth **2**: fill/refresh from manifests unless the user declines.

### 4. Matt Pocock engineering config

Run the **same process** as `/setup-matt-pocock-skills` (explore → section questions → confirm draft → write):

- `docs/agents/issue-tracker.md`
- `docs/agents/domain.md`
- `docs/agents/triage-labels.md` only if `triage` skill is installed
- `## Agent skills` block in existing `AGENTS.md` or `CLAUDE.md` (never create the other when one exists; if neither exists, `AGENTS.md` is the kit default — create it in phase 2 first)

Reuse the user's installed `setup-matt-pocock-skills` templates when present under `~/.cursor/skills/setup-matt-pocock-skills/`.

### 5. Continual-learning ready

Ensure `AGENTS.md` matches the plugin contract (two learned sections, plain bullets only).
Document for the user (do not invent secrets):

- Transcripts: `~/.cursor/projects/<workspace-slug>/agent-transcripts/`
- Incremental index: `.cursor/hooks/state/continual-learning-index.json` (created by the plugin when it runs)

Do not invent learned bullets during setup.

### 6. Team-kit + pstack reminders

- Confirm cursor-team-kit skills (CI/PR/review, `deslop`) are available; if not, instruct `/add-plugin cursor-team-kit`
- pstack: only invoke `/setup-pstack` when phase 1 found the rule missing; otherwise one line that models already apply to new sessions
- Depth **2** only: note that non-trivial engineering should prefer `/poteto-mode` when that skill is installed

### 6a. Kit verification / cleanup skills

Prefer the **cursor-kit plugin** (`~/.cursor/plugins/local/cursor-kit/skills/`
or marketplace/local plugin path). Do **not** also copy these into
`~/.cursor/skills/` on desktop — duplicates confuse which copy is live.

| Skill | When to point the user at it |
|-------|------------------------------|
| `verification-planning` | Before non-trivial implement — evidence path + budget |
| `simplify` | After behavior is proven — readability without behavior change |
| `blindspot-pass` | Second pass before ship (edges / silent failures) |

If the plugin is missing and Cloud/VM needs the kit skills, run
`scripts/install-cloud-skills.sh` (copies only when plugin absent, unless
`FORCE_USER_SKILLS=1`). Desktop sync: rsync kit → local plugin, then Reload.

Depth **2**: add a short **Agent skills** note in `AGENTS.md` or
`docs/agents/` only if the Matt phase already maintains an Agent skills block —
list the three triggers in one line each. Depth **1**: mention in the Done
report only.

### 6b. Quality gates offer (depth 2 only)

If interview depth is **2** and the repo looks JS/TS (`package.json` with js/ts tooling, or `*.ts`/`*.tsx` dominant):

1. Ask whether to install **measure-only** quality gates from `templates/quality-gates/` (recommended default when no ESLint max-lines rule exists).
2. If yes, follow kit `docs/prompts/05-quality-gates-install.md` (copy templates, adapt paths, run measure, **do not autofix**).
3. Always point to kit `docs/02-playbook-onboarding.md` and `docs/tools/05-quality-gates.md`.
4. If not JS/TS, one line: quality-gates templates are N/A; document whatever gate the stack uses in `PROJECT.md`.
5. If the target repo will be used from Cursor **Projects** (Cloud) and has no `.cursor/environment.json`, offer to copy kit `templates/cloud/environment.json` → `.cursor/environment.json` so Builds install kit skills on the VM (see `docs/tools/09-cloud-projects.md`).

### 6c. ai-memory companion — arrumar (always check; install on depth 2)

Part of stack setup. Delegate to `/setup-ai-memory` — do not reimplement upstream.

1. **Always (depth 1 + 2):** if companion is installed but broken (no binary, server down, MCP missing, or hooks wiped), **repair** via `/setup-ai-memory` / `scripts/install-ai-memory.sh`. After repair, confirm kit hooks still present (`./sync-hooks.sh` is merge-safe).
2. **Depth 2 only:** if companion was never installed, **install** it (recommended default on this stack; user may decline once). Point at `docs/prompts/07-ai-memory-wire.md` + `docs/tools/10-ai-memory.md`.
3. **Depth 1:** if never installed, one line: long-horizon wiki skipped; use depth 2 or `/setup-ai-memory` later.
4. Reminder: new Cursor repos auto-capture once companion is healthy — no per-repo reinstall. Optional `.ai-memory.toml` only if the user wants custom workspace/project naming.
5. Keep AGENTS / PROJECT / checkpoint authoritative. Report: OK | repaired | installed | declined | N/A (non-macOS / blocked).

Do not reinvent matt-pocock, pstack, or ai-memory core here.

### 7. Optional smoke (depth 2 or when user asks)

Offer, do not force:

1. Ping token-engine (`caveman_stats` or a tiny compress) if MCP is up
2. `codebase-memory` `index_repository` / `list_projects` for this root
3. If ai-memory wired: `curl` loopback `/mcp` → 405, or MCP `memory_status`
4. Point at kit smoke A/B/C in `docs/02-playbook-onboarding.md` (continue / PROJECT decision / failure retry)

### 8. Done report

Always end with a compact checklist:

```markdown
## Setup complete

- Mode: existing | new (`path`)
- Interview: minimal | completo
- Global: OK | repaired (list)
- Created/updated: (file list)
- Matt Pocock: issue tracker = …
- Quality gates: offered | installed (measure) | N/A | declined
- ai-memory: OK | repaired | installed | declined | N/A
- Kit skills: verification-planning / simplify / blindspot-pass / setup-ai-memory = plugin | missing
- Plugins: team-kit / continual-learning / pstack = present | action needed
- Playbook: docs/02-playbook-onboarding.md
- External inventory: docs/EXTERNAL-COMPONENTS.md
- Next: reload window if MCP/plugins changed; then normal work (or `/poteto-mode` for non-trivial)
```

## Guardrails

- Composition over duplication: delegate to `setup-pstack`, `setup-matt-pocock-skills`, `/setup-ai-memory`; fill `PROJECT.md` from manifests inline (no separate `project-brain` skill)
- No competing **episodic** state — AGENTS.md + PROJECT.md + `.cursor/state` stay authoritative; ai-memory wiki is an optional long-horizon companion (not a second checkpoint)
- No Hermes / Claude Code / OMH runtime assumptions
- Windows users may still use `install.ps1`; on macOS/Linux prefer `install.sh`
- Global hooks: merge, do not clobber companions (`./sync-hooks.sh` is merge-safe)
- If `move_agent_to_root` fails after creating a new repo, stop and ask the user to open that folder before writing further project files

## Out of scope

- Implementing app features inside the target repo
- Packaging releases of token-engine or forking ai-memory
- Rewriting global hooks from scratch when they already work
- Full skill-creator eval loops (separate follow-up)
