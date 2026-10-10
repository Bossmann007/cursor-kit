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
- Cursor-primary workflow: cursor-kit plugin is the sole skill SoT on desktop (`~/.cursor/plugins/local/cursor-kit/skills/`). Keep `~/.cursor/skills` empty. Do not keep kit or promoted skill copies under `~/.cursor/skills`, `~/.agents/skills`, or Agent Store. Codex is occasional only; if used, prefer the plugin path over local skill trees
- Long-horizon memory: optional **ai-memory** companion (`/setup-ai-memory`); kit AGENTS/PROJECT/checkpoint stay authoritative for prefs/decisions/live task
- Prefer impartial 0–100 rankings when comparing this stack to peer toolkits; do not self-favor

## Learned Workspace Facts

- Kit lives at `~/cursor-kit` → `~/.cursor/repos/cursor-kit` (GitHub `Bossmann007/cursor-kit`)
- Working branch for Enzo's personal kit config: `enzo` (default shipping branch remains `master` until merged)
- Pairs with [token-engine](https://github.com/Bossmann007/token-engine) at `~/token-engine` (GitHub `Bossmann007/token-engine`)
- Hooks + rules source of truth: `cursor-kit/hooks/` + `hooks.json.template` → `sync-hooks.sh` / `.ps1` (merge-safe; preserves companion hooks); `cursor-kit/rules/` (+ optional `sync-rules.sh`); pstack seed at `templates/pstack/pstack-models.mdc.example`
- Plugin entry: `.cursor-plugin/plugin.json` with `skills`, `rules`, `hooks` (setup orchestrators including `setup-matt-pocock-skills`, quality skills, and promoted engineering skills under `skills/`); desktop sync via rsync → `~/.cursor/plugins/local/cursor-kit/`; keep `~/.cursor/skills` and Agent Store empty of skill copies
- Companion plugins (UI install): continual-learning, cursor-team-kit, **pstack** as usage companion (skills stay in pstack plugin — not vendored into cursor-kit; then `/setup-pstack`); inventory in `docs/EXTERNAL-COMPONENTS.md`
- Optional long-horizon companion: [ai-memory](https://github.com/akitaonrails/ai-memory) via `scripts/install-ai-memory.sh` / `/setup-ai-memory` (native macOS + LaunchAgent); `sync-hooks` merge-safe so companion hooks survive kit sync
- Stranger onboarding docs: `docs/00-overview.md`, `docs/02-playbook-onboarding.md`, `docs/prompts/`, `templates/quality-gates/`
- Cursor Projects (Cloud) VMs should use the plugin or `scripts/install-cloud-skills.sh` / `templates/cloud/environment.json` only when the plugin is absent (script skips user-skills copy when local plugin is already present)
- Course folders default under `~/PUCPR`; academic setup is composed via `setup-pucpr` (does not replace `/setup-project`)
- Matt `/teach` (mission/lessons workspace) and pstack `/teach` (code explain via how/why) are different skills — do not conflate in wiring
- Removed unused kit env skills (`context-engine`, `dev-workflow`, `project-brain`, `update-checkpoint`); their intent lives in rules/hooks/`/setup-project` instead

<!-- ai-memory:profile:start -->
## Usual choices (ai-memory profile)

Written by `ai-memory profile apply` from the user's cross-project profile. Change the profile (`ai-memory profile show` / `forget`) and re-run the command instead of editing this block. Everything else in this file takes precedence.

- [javascript] JavaScript is one of the stacks this user usually works in. (`profile/stack/javascript.md`)
- `## Agent skills` block in existing `AGENTS.md` or `CLAUDE.md` (never create the other when one exists; (`profile/habits/agent-skills-block-in-existing-agents-md-or-claude-md-never.md`)
- Não use casos, vault_personal_notes, hardvault_*, mcp_runs nem as 26 capas. (`profile/habits/n-o-use-casos-vault-personal-notes-hardvault-mcp-runs-nem-as.md`)
- Não use o termo BYOAI. (`profile/habits/n-o-use-o-termo-byoai.md`)
- Never store secrets (`profile/habits/never-store-secrets.md`)
- on macOS/Linux prefer `install.sh` (`profile/habits/on-macos-linux-prefer-install-sh.md`)
- Prefer the kit's `install.sh` when the machine has `~/cursor-kit` linked; (`profile/habits/prefer-the-kit-s-install-sh-when-the-machine-has-cursor-kit.md`)
<!-- ai-memory:profile:end -->
