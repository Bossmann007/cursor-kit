# AGENTS.md — cursor-kit

## Learned User Preferences

- Cursor-only dev environment (macOS primary; Windows scripts still shipped)
- Prefer minimal tokens: caveman_stats on demand only
- Prefer `/setup-project` for new or existing repos on this stack
- `/setup-project` locked decisions: A2 (per-repo + global repair if broken), B3 (existing or new — ask), interview depth 1 minimal vs 2 completo — ask; ship as plugin inside cursor-kit
- Prefer `/poteto-mode` for non-trivial kit packaging/architecture work
- Human-facing kit docs may be PT; pasteable prompts stay English; avoid absolute machine-specific paths in shared docs
- New kit skills should be prompt-driven orchestrators (compose existing skills/templates), not monoliths; draft SKILL.md for approval before running setup against real repos
- Steal onboarding/playbook/quality-gates *form* from peer toolkits when useful; keep stack advantages (token-engine, hooks + `.cursor/state`, `/setup-project`, ponytail/caveman/cbm, continual-learning, pstack/team-kit)
- Quality gates are first-class: measure-only vs autofix stay separate; `/setup-project` depth 2 may offer installing measure-only gates

## Learned Workspace Facts

- Kit lives at `~/cursor-kit` → `~/.cursor/repos/cursor-kit`
- Pairs with [token-engine](https://github.com/Bossmann007/token-engine) at `~/token-engine`
- Public GitHub: `Bossmann007/cursor-kit` and `Bossmann007/token-engine`
- Hooks source of truth: `cursor-kit/hooks/` synced to `~/.cursor/hooks` via `sync-hooks.sh` / `sync-hooks.ps1`
- Plugin entry: `.cursor-plugin/plugin.json` with `skills: ./skills/` (includes `setup-project`; `setup-pucpr` drafted under `skills/setup-pucpr/` + `templates/faculdade/`)
- Stranger onboarding docs: `docs/00-overview.md`, `docs/02-playbook-onboarding.md`, `docs/prompts/`, `templates/quality-gates/`
- Course folders default under `~/PUCPR`; academic setup is composed via `setup-pucpr` (does not replace `/setup-project`)
- Matt `/teach` (mission/lessons workspace) and pstack `/teach` (code explain via how/why) are different skills — do not conflate in wiring
