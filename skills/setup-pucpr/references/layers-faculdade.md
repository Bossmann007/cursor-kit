# Layers — global vs disciplina (faculdade)

Use this when deciding what to write. Prefer repair/detect over duplicate.
Compose with `setup-project` `references/layers.md` when the folder is also a
full Cursor agent repo.

## Global (`~/.cursor/`) — shared across projects

| Asset | Expected path | Role |
|-------|---------------|------|
| User skills | `~/.cursor/skills/` | `setup-project`, Matt `teach`, `grilling`, `research`, `diagnosing-bugs`, … |
| pstack plugin | Cursor plugin UI | `how`, `why`, pstack `teach`, `recall`, … (code-explain — not Matt teach) |
| Teaching plugins | Cursor plugin UI | e.g. teaching (`create-learning-path`), optional `pucpr-*` |
| Rules | `~/.cursor/rules/*.mdc` | stack rules; do **not** copy into course by default |
| MCP / hooks | `~/.cursor/mcp.json`, `hooks.json` | repair via `/setup-project`, not this skill |

Global work for `setup-pucpr`: **detect** teaching skills; **offer**
`/setup-project` if the user wants full stack. Do not invent missing Canvas
or teach skills.

## Per-disciplina — created/updated by this skill

| Asset | Path | Role |
|-------|------|------|
| Durable memory | `AGENTS.md` | Continual Learning + pedagogical prefs/facts |
| Course brain | `COURSE.md` | Stack acadêmico, slides, entregas, scope |
| Study entry | `README.md` | Short orientation (optional if strong MOC exists) |
| Deliverables | `PBLs/`, `Listas/`, `Projeto/`, `TDE*` | Work-type dirs; never clobber contents |
| Scratch | `.scratch/` | Local notes; gitignored |
| Official sources | `Modulos/`, `Slides/`, `Plano-de-Ensino*` | Professor materials — map, do not invent |
| Optional agent state | `.cursor/state/` | Only if also `/setup-project` / full agent repo |

## External sources (do not fork into the skill body)

- Generic stack: `/setup-project` + `~/cursor-kit`
- Teaching UX: Matt `teach`, `grilling`, learning-path; pstack `how`/`why`/`teach`/`recall`
- Wiring matrix: `skills/setup-pucpr/references/skills-wiring.md`
- Course parent default: `~/PUCPR` when present
- Templates: `~/cursor-kit/templates/faculdade/`

## Conflict policy

| Situation | Prefer |
|-----------|--------|
| `COURSE.md` vs `PROJECT.md` both useful | Keep both if `/setup-project` ran; else `COURSE.md` is enough for pure study folders |
| Existing `MISSION.md` / `NOTES.md` / MOC | Leave in place; link from `COURSE.md` |
| Existing filled `AGENTS.md` | Fill gaps only; never wipe learned bullets |
| Student code under `PBLs/` | Never overwrite |
