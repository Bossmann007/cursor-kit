# Skills curadas — Enzo (PUCPR 2026/2 + projetos)

## Matérias → skills Matt

| Disciplina | Skills úteis |
|------------|----------------|
| BD (71306) | `tdd`, `diagnosing-bugs`, `domain-modeling`, `research` |
| CPS (72011) | `diagnosing-bugs`, `research`, `prototype` |
| Ética (72006) | `grill-me`, `teach`, `wait-what` |
| Prog. Imperativa (72009) | `tdd`, `diagnosing-bugs`, `implement`, `code-review` |
| Prog. WEB (71310) | `tdd`, `prototype`, `implement`, `code-review`, `diagnosing-bugs` |
| Discreta (72005) | `teach`, `grill-me` |

## Projetos → skills

| Projeto | Skills |
|---------|--------|
| token-engine / Python | `tdd`, `implement`, `code-review`, `to-spec`, `domain-modeling` |
| Flutter / Unity | `prototype`, `implement`, `tdd` |
| GitHub solo | `resolving-merge-conflicts`, `to-spec` |

## Removidas (enterprise / time / meta / Windows-incompat)

`wayfinder`, `triage`, `improve-codebase-architecture`, `to-tickets`, `scaffold-exercises`, `setup-pre-commit`, `wizard`, `writing-for-agents`, `to-questionnaire`, `ask-matt`, `codebase-design`

## Removidas (kit env — pouco usadas; lógica coberta por rules/hooks/setup)

`context-engine`, `dev-workflow`, `project-brain`, `update-checkpoint`

## Sempre manter

Kit plugin (source of truth on desktop): `setup-project`, `setup-pucpr`, `setup-ai-memory`, `verification-planning`, `simplify`, `blindspot-pass`  
Env (`~/.cursor/skills/`): `find-skills` (+ Matt allowlist below)  
PUCPR: `pucpr-canvas`, `pucpr-tutor` (when installed)  
Matt core: `grill-me`, `grill-with-docs`, `grilling`, `handoff`, `wait-what`, `tdd`, `diagnosing-bugs`, `code-review`, `implement`, `to-spec`, `research`, `prototype`, `domain-modeling`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `teach`

Do **not** copy plugin-shipped skills into `~/.cursor/skills/` **or** `~/.agents/skills/` when the cursor-kit plugin is installed. Cursor loads both user paths; leftover copies there look like “not deleted”.
