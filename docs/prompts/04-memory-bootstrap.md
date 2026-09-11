# Prompt 04. Memory bootstrap

**PT (wrapper).** Sobe as camadas de memória do kit sem inventar fatos. AGENTS + PROJECT + checkpoint. Não cria vault Obsidian.

**When to use.** Repo novo ou memória vazia após `/setup-project`.

---

## Paste this to the agent (English)

```text
Bootstrap Cursor-kit memory layers for this repo. Do not invent user preferences or workspace facts.

Layers:
1. AGENTS.md — only sections "## Learned User Preferences" and "## Learned Workspace Facts". Plain bullets. Leave placeholders if unknown. Never store secrets.
2. PROJECT.md — fill Stack / Commands / Architecture from manifests (package.json, pyproject, README, CI). Decisions table only for approved choices; ask before inventing decisions.
3. .cursor/state/checkpoint.json — set status idle unless there is an active task; do not fabricate progress.
4. Do not clobber non-empty AGENTS.md or PROJECT.md content. Merge carefully; prefer leave-and-report.

If continual-learning plugin is present, document (do not create) the index path .cursor/hooks/state/continual-learning-index.json.

Output a short report of files created vs skipped.
```
