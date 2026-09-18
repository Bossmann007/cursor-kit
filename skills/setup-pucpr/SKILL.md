---
name: setup-pucpr
description: >
  Bootstrap or repair a PUCPR / faculdade course folder for agent-assisted
  study (discipline scaffold, COURSE.md brain, pedagogical AGENTS contract,
  slides/PDF mapping, hand-in checklist). Use whenever the user asks to setar /
  setup / scaffold a disciplina, curso PUCPR, pasta de faculdade, PBL workspace,
  prova-prep folder, or says the course repo is missing AGENTS/COURSE, Modulos/
  Slides wiring, or teaching guardrails — even if they do not say "setup-pucpr".
  Prefer this over ad-hoc copying of course templates. Does NOT replace
  /setup-project (generic Cursor stack); compose with it and with Matt /teach
  (primary study loop), selective Matt skills (grilling, research,
  diagnosing-bugs, …), and selective pstack how/why/teach/recall. Does NOT
  solve PBLs or invent enunciados.
disable-model-invocation: false
---

# Setup PUCPR (faculdade)

Orchestrate one coherent **per-discipline** setup for PUCPR / user coursework.
Compose existing skills and templates — do not rewrite them inline, do not ship
a monolith skill that reimplements `/setup-project` or `/teach`.

Canonical course parent: `~/PUCPR` when present; else ask (e.g. `~/ADAPUCPR`,
`~/Courses/`). Canonical kit root: `~/cursor-kit` (symlink to this repo when
installed that way).

Read `references/layers-faculdade.md` before writing files so global vs
discipline-folder stays clear.

Read `references/skills-wiring.md` before phase 4 so Matt `/teach`, pstack
`how`/`why`/`teach`, and related skills are composed correctly (two different
`teach` skills exist — do not conflate them).

**Status note for maintainers:** this skill scaffolds study workspaces. It
never completes coursework for the student.

## Locked decisions (this skill)

- **A2**: per-discipline folder setup + **global repair** only when teaching
  stack pieces are missing/broken (detect skills; optionally remind
  `/setup-project` if the folder will also be a full agent repo)
- **B3**: support **existing discipline folder** and **new folder** — ask which
  at start
- **C**: ask interview depth **1 (minimal)** or **2 (completo)** before phase 2+
- Idempotent: never clobber filled `AGENTS.md` / `COURSE.md` / student work;
  only create or fill gaps
- Portuguese OK in chat; paths and identifiers in English; academic content
  may be **PT-first** when the discipline is PT (match enunciado / slide names)
- Default tracker: **local markdown / `.scratch`** — do **not** force Matt
  Pocock GitHub issue-tracker wiring unless the user explicitly wants it

## What this is / is not

| Is | Is not |
|----|--------|
| Orchestrator: scaffold + wire + pedagogical contract | Replacement for `/setup-project` |
| Maps official sources (`Modulos/`, `Slides/`, `Plano-de-Ensino*`, `PBLs/`) | Inventor of enunciados or professor materials |
| Teaching guardrails (step-by-step; no full PBL solution) | Autocomplete of PBL/prova for the student |
| Detects installed teach skills and points at them | Reimplementation of `teach` / `grilling` / learning-path |

## Process

### 0. Mode + depth + disciplina + work type

Ask up front (one answer each; lead with recommended defaults). Skip any
question the user already answered in the trigger message.

1. **Target mode** (recommended: existing folder if a course root is already open
   or clearly named under `~/PUCPR/`)
   - **Existing discipline** — scaffold into current workspace / chosen path
   - **New discipline folder** — confirm **name** + **parent** (prefer `~/PUCPR`
     if it exists), create dir, then `move_agent_to_root` into it **before**
     writing files

2. **Interview depth**
   - **1 — Minimal**: folder structure + academic `AGENTS.md` / `COURSE.md` +
     ask “where are the slides/PDFs?”
   - **2 — Completo**: everything in 1, plus map PDFs/módulos into `COURSE.md`,
     write explicit pedagogical rules (AGENTS bullets and/or a local
     `.cursor/rules` only if user wants), optional smoke (`gcc --version` /
     open slide path exists), point at learning-path / teach playbooks when
     installed

3. **Disciplina** — list folders detected under preferred parent (`~/PUCPR/`)
   plus **outra** (free text). Seed known names when detectable, e.g.:
   Programação Imperativa, Arquitetura de Banco de Dados, Programação WEB,
   Conectividade em Sistemas Ciberfísicos, Ética, Resolução de Problemas de
   Natureza Discreta.

4. **Work type** (changes scaffold defaults):
   - **PBL** → ensure `PBLs/` (or keep existing)
   - **lista** → ensure `Listas/`
   - **prova-prep** → ensure room for cram plan / formativa notes; do not invent exam content
   - **projeto** → ensure `Projeto/` (or user-named deliverable dir)

### 1. Pré-check (compose, do not duplicate)

Check, summarize in one short block, then continue:

| Check | Healthy signal | Action |
|-------|----------------|--------|
| Matt `/teach` | `~/.cursor/skills/teach` (MISSION / lessons workspace skill) | Primary study skill — required for full teach wiring; if missing, say so |
| pstack explain trio | plugin skills `how`, `why`, `teach` | Optional code-explain path; distinct from Matt teach |
| Other study skills | `grilling`/`grill-me`, `research`, `diagnosing-bugs`, `wait-what`, `domain-modeling`, `handoff`; plugin `create-learning-path`; optional `pucpr-canvas` | List present vs missing per `references/skills-wiring.md`; **do not invent** |
| `/setup-project` already applied | `AGENTS.md` continual-learning sections + `.cursor/state/` present | If absent: **offer** run `/setup-project` first (full Cursor stack) **or** continue with **academic-only** scaffold |
| ai-memory companion (when full stack) | MCP `ai-memory` + server `127.0.0.1:49374` healthy if user also wants kit agent stack | If broken/missing and user chose full stack / already ran `/setup-project`: **repair/arrumar** via `/setup-ai-memory`. Academic-only path: skip with one line |
| Kit templates | `~/cursor-kit/templates/faculdade/` (or this skill’s bundled copies) | Prefer kit path; fall back to files beside this skill |
| Parent courses dir | `~/PUCPR` exists | Use as default parent for new folders |

Never invent a second hook/MCP system inside the course folder. Do not fork ai-memory into the folder.

### 2. Scaffold idempotente

From kit templates (`templates/faculdade/` or skill-local copies):

1. Ensure work-type dirs exist (`PBLs/`, `Listas/`, `Projeto/`, `.scratch/` as needed) — create empty dirs only; never delete student files
2. Create `AGENTS.md` only if absent — continual-learning sections **plus** seed
   pedagogical preference bullets appropriate to the disciplina (PT-first when
   applicable). Do **not** invent personal grades or secrets
3. Create `COURSE.md` only if absent (academic project-brain; see template) —
   include an **Agent skills** table (filled in phase 4)
4. Create a short `README.md` only if absent (how to study in this folder +
   pointer to official sources + Matt `/teach` as primary study entry)
5. Append faculdade `.gitignore` snippet if missing (ignore `.scratch/` noise,
   OS junk; do **not** ignore deliverable source the student must hand in)
6. Optionally create `.cursor/state/` **only** if the user also wants full
   agent-repo behavior or already ran `/setup-project` — otherwise skip

Prefer filling gaps over replacing existing `MISSION.md`, `NOTES.md`,
`Plano-de-Ensino*`, `Modulos/`, `Slides/`, `PBLs/`, `learning-records/`,
`lessons/`.

Do **not** copy global `~/.cursor/rules` into the course folder by default.

### 3. Course brain (`COURSE.md`)

Analogous to `project-brain`, but academic:

- Detect stack from existing files (`*.c` → C + `gcc`; SQL/slides BD → modeling;
  web → HTML/CSS/JS or whatever manifests show)
- Record commands the student actually uses (e.g. `gcc …`, unzip/hand-in notes)
- Map official paths: `Modulos/`, `Slides/`, `Plano-de-Ensino*`, enunciados under
  `PBLs/`, formativa/gabarito if present
- Capture exam scope **only** from user-approved or already-documented facts
  (e.g. “não cai X”) — never invent restrictions
- Keep a Decisions table for approved study/architecture choices only
- Never store secrets, credentials, or sensitive personal notes

Depth **1**: ask “where are the slides?” and write paths the user confirms;
  leave deep PDF inventory for later.
Depth **2**: inventory detectable PDFs/PPTX under `Modulos/` / `Slides/` into
  `COURSE.md` (names + paths only; do not OCR entire decks into memory).

### 4. Wiring ensino (+ Matt + pstack selectivo)

Follow `references/skills-wiring.md`. Summary:

**Matt `/teach` is first-class** (multi-session course learning). pstack
`/teach` is a different skill (explain code via `/how` + `/why`).

1. **Detect** Matt teach, pstack how/why/teach, and the “wire by default” set
   in `skills-wiring.md`. Summarize present vs missing.
2. **Write `COURSE.md` → Agent skills** with concrete triggers (PT OK in the
   trigger column). Always list Matt `/teach` first when present.
3. **Matt teach workspace (depth 2, or user asks):**
   - If `MISSION.md` / `learning-records/` already exist → link only; do not
     clobber; say “continue with `/teach`”
   - If missing and Matt teach is installed → **offer** minimal stubs:
     `MISSION.md` from teach’s `MISSION-FORMAT.md`, empty `learning-records/`,
     optional `NOTES.md` / `RESOURCES.md` placeholders — **never** generate
     full `lessons/*.html` during setup
   - Depth 1: document only; do not create teach stubs unless user asks
4. **Also document when present (do not auto-run):**
   - `grilling` / `grill-me` — stress-test plano de estudo / abordagem de PBL
   - `grill-with-docs` + `domain-modeling` — cursos de modelagem (ex. BD)
   - `research` — fontes primárias (ainda assim professor PDFs first)
   - `diagnosing-bugs` — código do aluno não compila/roda
   - `verification-planning` — opcional em `projeto` / labs (evidence path); nunca para auto-completar PBL
   - `wait-what` — reexplicar
   - `handoff` — fim de sessão
   - `create-learning-path` — oferecer em **prova-prep**
   - pstack `how` / `why` / `teach` — explicar código/exemplo
   - pstack `recall` — “onde parei nesta disciplina?”
5. **Skip by default** (see skills-wiring): `implement`, `to-spec`, `simplify`,
   issue tracker Matt, `poteto-mode`/`arena`/`swarm`/`interrogate`, full
   `principle-*` list — point heavy eng at `/setup-project` instead
6. **Default: no GitHub issue tracker.** Only if user insists, delegate to
   `/setup-matt-pocock-skills` / `/setup-project` phase 4
7. Optional `pucpr-canvas`: detect only; never fake

### 5. Continual-learning ready

Ensure `AGENTS.md` matches the plugin contract:

- `## Learned User Preferences`
- `## Learned Workspace Facts`
- plain bullets only

Seed **durable** pedagogical prefs when creating a new file (examples of shape,
not invented secrets):

- Teach step-by-step; user iterates (e.g. pastes partial `.c`, says `pronto`)
- Do not finish PBLs or write the full solution
- Ground steps in professor `Modulos/` / `Slides/` before inventing patterns
- Before zip/hand-in: real files not folders; flatten; compile/check when asked

Do not invent learned bullets from thin air during setup beyond the confirmed
disciplina facts and user answers from this interview.

### 6. Regras pedagógicas explícitas

Encode in `AGENTS.md` (and optionally one short local rule file **only if**
depth 2 and user asks):

1. **No full PBL/prova solution** — guide the next step only
2. **Official sources first** — `Modulos/*.pdf`, `Slides/`, enunciados in `PBLs/`
3. **PT-first** when the disciplina materials are PT
4. **Hand-in checklist** (surface in Done report and `COURSE.md`):
   - deliverable paths are files, not empty folder shells mistaken for sources
   - flatten when the LMS expects a flat zip
   - `gcc` / language check when applicable
5. Respect user scope corrections over plano wording alone when studying for exams

### 7. Optional smoke (depth 2 or when user asks)

Offer, do not force:

1. Confirm slide/PDF paths exist (`test -f` / list dir)
2. Toolchain sniff when relevant (`gcc --version`, `node -v`, etc.)
3. If `/setup-project` was also applied: optional token-engine / codebase-memory
   pings; if ai-memory is in play, confirm loopback `/mcp` → 405 or note repair via `/setup-ai-memory`
   (delegate; do not duplicate those instructions here)

### 8. Done report

Always end with a compact checklist:

```markdown
## Setup PUCPR complete

- Mode: existing | new (`path`)
- Interview: minimal | completo
- Disciplina: …
- Work type: PBL | lista | prova-prep | projeto
- setup-project: already present | offered | skipped (academic-only)
- ai-memory: OK | repaired | skipped (academic-only) | N/A
- Matt teach: present | missing | stubs offered/created/skipped
- pstack how/why/teach: present | missing
- Other wired skills: (list) | skipped-as-N/A: (short)
- Created/updated: (file list)
- Official sources mapped: Modulos/Slides/Plano/PBLs = …
- Pedagogical guardrails: seeded in AGENTS | declined
- Smoke: ran | skipped
- Next: `/teach` (Matt) for study sessions; pstack `/how`/`/teach` for code
  explain; `/setup-project` if full Cursor stack still missing
```

## Guardrails

- Composition over duplication: delegate to `setup-project`, `/setup-ai-memory`, Matt `teach`,
  `grilling`, `create-learning-path`, pstack `how`/`why`/`teach`,
  `project-brain` patterns, `pucpr-*` when installed — see
  `references/skills-wiring.md`
- No competing **episodic** state — prefer `AGENTS.md` + `COURSE.md` (+ `.cursor/state`
  only when acting as full agent repo); ai-memory wiki is optional companion when full stack is on
- Never store secrets, passwords, LMS cookies, or sensitive personal data in
  AGENTS/COURSE (nor in ai-memory wiki)
- Idempotent: never clobber student solutions, enunciados, or filled brains
- If `move_agent_to_root` fails after creating a new folder, **stop** and ask
  the user to open that folder before writing further files
- Do not run setup against a real course folder in skill-authoring sessions
  without explicit user approval of this SKILL.md

## Out of scope

- Solving PBLs, TDEs, listas, or exams for the student
- Inventing enunciados, gabaritos, or “o que cai” without evidence
- Replacing `/setup-project` for generic non-academic repos
- Packaging releases of token-engine / rewriting global hooks
- Full skill-creator eval loops (separate follow-up when the user asks)

## Templates (kit)

Prefer:

- `~/cursor-kit/templates/faculdade/AGENTS.md.faculdade.template`
- `~/cursor-kit/templates/faculdade/COURSE.md.template`
- `~/cursor-kit/templates/faculdade/README.md.faculdade.template`
- `~/cursor-kit/templates/faculdade/gitignore.faculdade.snippet`

If the kit path is missing, use copies under this skill’s
`references/templates/` (when vendored) or the same filenames beside
`references/layers-faculdade.md` in the plugin checkout.
