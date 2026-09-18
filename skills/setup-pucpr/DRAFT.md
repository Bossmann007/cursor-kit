# setup-pucpr — install notes

Canonical path: `cursor-kit/skills/setup-pucpr/` (plugin `skills: ./skills/`).

User-skills install (same pattern as `setup-project`):

```bash
ln -sfn ~/cursor-kit/skills/setup-pucpr ~/.cursor/skills/setup-pucpr
# or: ln -sfn ~/.cursor/repos/cursor-kit/skills/setup-pucpr ~/.cursor/skills/setup-pucpr
```

Also ensure the plugin is installed under `~/.cursor/plugins/local/` as a **real directory** (Cursor rejects symlinks whose target is outside that folder):

```bash
rsync -a --delete --exclude '.git/' --exclude '__pycache__/' \
  ~/cursor-kit/ ~/.cursor/plugins/local/cursor-kit/
```

Then **reload Cursor** (or new agent chat) so `/setup-pucpr` appears.

If slash-command still missing: attach the skill manually or say “run setup-pucpr”.
