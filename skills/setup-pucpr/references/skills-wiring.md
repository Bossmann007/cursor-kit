# Skills wiring — faculdade (detect, do not invent)

Compose. List what is present; document triggers in `COURSE.md` → **Agent skills**.
Never stub a missing skill. Never auto-run heavy skills during setup.

## Two different `teach` skills

| Source | Path hint | Role for PUCPR |
|--------|-----------|----------------|
| **Matt / user `teach`** (primary) | `~/.cursor/skills/teach` | Multi-session teaching workspace: `MISSION.md`, `lessons/`, `learning-records/`, `RESOURCES.md`, `NOTES.md` |
| **pstack `teach`** | pstack plugin skills | Explain a body of code: runs `how` + `why`, plain understanding — **not** the course workspace orchestrator |

If both exist, document both with distinct triggers in `COURSE.md`:

- Prefer Matt `/teach` for “estudar esta disciplina / missão / lição”
- Prefer pstack `/teach` (or `/how` + `/why`) for “explica este `.c` / este exemplo do professor”

## Wire by default (depth 1+: detect + document)

### Matt Pocock / user skills

| Skill | When it helps | Setup action |
|-------|---------------|--------------|
| **`teach`** (Matt) | Primary study loop for the discipline folder | **First-class.** Depth 1: document trigger. Depth 2: if `MISSION.md` missing, **offer** stub from teach `MISSION-FORMAT.md` + empty `learning-records/` — do not invent lessons HTML |
| **`grilling` / `grill-me`** | Stress-test study plan, PBL *approach*, prova scope — not the solution | Document; do not auto-grill |
| **`grill-with-docs`** | Domain-heavy courses (e.g. BD) when building glossary/ADRs while grilling | Document when `domain-modeling` also present |
| **`domain-modeling`** | Ubiquitous language / `CONTEXT.md` for modeling courses | Offer only if disciplina is domain-heavy and user wants glossary |
| **`research`** | Cite primary sources (docs/specs); still prefer professor PDFs first | Document; never invent enunciado |
| **`diagnosing-bugs`** | Student code fails to compile/run | Document as “debug my program” path |
| **`wait-what`** | Last explanation did not land — re-pitch | Document |
| **`handoff`** | End of study session / pass context | Document optional |
| **`create-learning-path`** (teaching plugin) | `prova-prep` roadmaps | Offer on prova-prep; do not auto-run |
| **`run-learning-retrospective`** | After a study block | Document if installed |
| **`pucpr-canvas`** (if any) | LMS/Canvas helpers | Detect only; never fake |

### pstack (good fit — selective)

| Skill | When it helps | Setup action |
|-------|---------------|--------------|
| **`how`** | “Como funciona este código / este fluxo?” | Document as companion to code walkthroughs |
| **`why`** | “Por que está assim?” (design rationale) — usually overkill for homework | Document optional; keep narrow |
| **`teach`** (pstack) | Weave how+why into one explanation | Document as **code-explain teach**, distinct from Matt teach |
| **`recall`** | “Onde parei nesta disciplina?” across chats | Document for resume |
| **`figure-it-out`** | Stuck debugging with evidence | Document optional |
| **`technical-writing`** | Relatórios / texto de entrega (not solution code) | Document optional |

## Do **not** wire by default (say N/A or skip)

Temptation to complete coursework or overkill for a course folder:

- `implement`, `to-spec`, `prototype` — push toward finishing PBL
- `setup-matt-pocock-skills` issue tracker / GitHub labels — default remains local `.scratch`
- `poteto-mode`, `arena`, `swarm`, `architect`, `interrogate` — heavy eng panels
- `tdd` — only if student explicitly practices TDD on a project
- `typescript-best-practices`, `make-bot-ui`, Benny automations
- `show-me-your-work`, `reflect`, `automate-me` — meta/agent-maintain, not course study
- Whole `principle-*` catalog — leave to pstack; do not list in COURSE.md

If user insists on full eng stack, point at `/setup-project` instead of bloating this skill.

## Depth behavior

- **Depth 1:** detect presence; write short **Agent skills** table in `COURSE.md`; Done report lists present/missing
- **Depth 2:** same, plus offer Matt-teach stubs (`MISSION.md` / `learning-records/`) when missing; offer `create-learning-path` on prova-prep; still no auto lesson generation

## Conflict: existing teach workspace

If `MISSION.md` / `lessons/` / `learning-records/` already exist (common under `~/PUCPR/Programação Imperativa`):

- Leave them untouched
- Link paths from `COURSE.md`
- Prefer continuing with Matt `/teach` over re-scaffolding
