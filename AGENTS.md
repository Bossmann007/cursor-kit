# AGENTS.md — cursor-kit

## Learned User Preferences

- Cursor-only dev environment (macOS primary; Windows scripts still shipped)
- Prefer minimal tokens: caveman_stats on demand only
- Prefer `/setup-project` for new or existing repos on this stack
- `/setup-project` locked decisions: A2 (per-repo + global repair if broken), B3 (existing or new — ask), interview depth 1 minimal vs 2 completo — ask; ship as plugin inside cursor-kit
- Prefer `/poteto-mode` for non-trivial kit packaging/architecture work
- Human-facing kit docs may be PT; pasteable prompts stay English; avoid absolute machine-specific paths in shared docs
- New kit skills should be prompt-driven orchestrators (compose existing skills/templates), not monoliths; draft SKILL.md for approval before running setup against real repos
- Steal onboarding/playbook/quality-gates/skill *form* from peer toolkits when useful; create native skills (do not vendor third-party SKILL.md verbatim); wire into `setup-project` / `setup-pucpr`; keep stack advantages (token-engine, hooks + `.cursor/state`, `/setup-project`, ponytail/caveman/cbm, continual-learning, pstack/team-kit)
- Quality gates are first-class: measure-only vs autofix stay separate; `/setup-project` depth 2 may offer measure-only gates and optional ai-memory companion
- Prefer cursor-kit plugin as source of truth for kit-shipped skills (`setup-project`, `setup-pucpr`, `setup-ai-memory`, `verification-planning`, `simplify`, `blindspot-pass`); do not keep duplicate copies under `~/.cursor/skills` on desktop
- Long-horizon memory: optional **ai-memory** companion (`/setup-ai-memory`); kit AGENTS/PROJECT/checkpoint stay authoritative for prefs/decisions/live task
- Prefer impartial 0–100 rankings when comparing this stack to peer toolkits; do not self-favor

## Learned Workspace Facts

- Kit lives at `~/cursor-kit` → `~/.cursor/repos/cursor-kit` (GitHub `Bossmann007/cursor-kit`)
- Working branch for Enzo's personal kit config: `enzo` (default shipping branch remains `master` until merged)
- Pairs with [token-engine](https://github.com/Bossmann007/token-engine) at `~/token-engine` (GitHub `Bossmann007/token-engine`)
- Hooks + rules source of truth: `cursor-kit/hooks/` + `hooks.json.template` → `sync-hooks.sh` / `.ps1` (merge-safe; preserves companion hooks); `cursor-kit/rules/` (+ optional `sync-rules.sh`); pstack seed at `templates/pstack/pstack-models.mdc.example`
- Plugin entry: `.cursor-plugin/plugin.json` with `skills`, `rules`, `hooks` (includes `setup-project`, `setup-pucpr`, `setup-ai-memory`, `verification-planning`, `simplify`, `blindspot-pass`); desktop sync → `~/.cursor/plugins/local/cursor-kit/`
- Companion plugins (UI install): continual-learning, cursor-team-kit, pstack (then `/setup-pstack`); inventory in `docs/EXTERNAL-COMPONENTS.md`
- Optional long-horizon companion: [ai-memory](https://github.com/akitaonrails/ai-memory) via `scripts/install-ai-memory.sh` / `/setup-ai-memory` (native macOS + LaunchAgent); `sync-hooks` merge-safe so companion hooks survive kit sync
- Stranger onboarding docs: `docs/00-overview.md`, `docs/02-playbook-onboarding.md`, `docs/prompts/`, `templates/quality-gates/`
- Cursor Projects (Cloud) VMs do not read Mac `~/.cursor/skills`; use `scripts/install-cloud-skills.sh` / `templates/cloud/environment.json` (script skips user-skills copy when local plugin is already present)
- Course folders default under `~/PUCPR`; academic setup is composed via `setup-pucpr` (does not replace `/setup-project`)
- Matt `/teach` (mission/lessons workspace) and pstack `/teach` (code explain via how/why) are different skills — do not conflate in wiring
- Removed unused kit env skills (`context-engine`, `dev-workflow`, `project-brain`, `update-checkpoint`); their intent lives in rules/hooks/`/setup-project` instead
