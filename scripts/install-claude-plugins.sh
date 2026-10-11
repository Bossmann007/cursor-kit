#!/usr/bin/env bash
# Install pstack + superpowers (pinned copies from the Cursor plugin cache) and the official helper plugins into Claude Code.
# Local marketplace: ~/.claude/local-marketplace (name: bossmann-local). Idempotent. No network except the official directory.
# pstack tweaks (cost): poteto-agent and Comment Sicko run on Sonnet (see "model:" frontmatter). Re-run after updating pstack in Cursor.
set -euo pipefail
umask 022
CACHE="${HOME}/.cursor/plugins/cache/cursor-public"
M="${HOME}/.claude/local-marketplace"
command -v claude >/dev/null || { echo "claude CLI missing"; exit 0; }
[[ -d "$CACHE/pstack" && -d "$CACHE/superpowers" ]] || { echo "install-claude-plugins: Cursor cache for pstack/superpowers missing; skipping"; exit 0; }
latest() { ls -dt "$CACHE/$1"/*/ | head -1; }

mkdir -p "$M/.claude-plugin" "$M/plugins"
rsync -a --delete --exclude .git --exclude .cache-complete "$(latest pstack)" "$M/plugins/pstack/"
rsync -a --delete --exclude .git --exclude .cache-complete "$(latest superpowers)" "$M/plugins/superpowers/"

python3 - "$M" <<'PY'
import json,re,sys,os
M=sys.argv[1]
src=json.load(open(f'{M}/plugins/pstack/.cursor-plugin/plugin.json'))
ver=src['version']+'-local1'
man={k:src[k] for k in ('name','description','author','homepage','repository','license','keywords') if k in src}
man['version']=ver
os.makedirs(f'{M}/plugins/pstack/.claude-plugin',exist_ok=True)
json.dump(man,open(f'{M}/plugins/pstack/.claude-plugin/plugin.json','w'),indent=2)
for f in ('poteto-agent.md','comment-sicko.md'):
    p=f'{M}/plugins/pstack/agents/{f}';s=open(p).read()
    s=re.sub(r'^model:.*\n','',s,flags=re.M).replace('\n---\n','\nmodel: sonnet\n---\n',1)
    open(p,'w').write(s)
sp=json.load(open(f'{M}/plugins/superpowers/.claude-plugin/plugin.json'))
json.dump({"name":"bossmann-local","owner":{"name":"Enzo Bossmann"},"plugins":[
 {"name":"pstack","source":"./plugins/pstack","description":"pstack (poteto-mode, principles) with Sonnet subagents","version":ver},
 {"name":"superpowers","source":"./plugins/superpowers","description":"superpowers","version":sp['version']}]},
 open(f'{M}/.claude-plugin/marketplace.json','w'),indent=2)
PY

claude plugin marketplace list 2>/dev/null | grep -q bossmann-local || claude plugin marketplace add "$M"
claude plugin marketplace update bossmann-local >/dev/null
for p in pstack@bossmann-local superpowers@bossmann-local frontend-design@anthropic-plugin-directory commit-commands@anthropic-plugin-directory claude-md-management@anthropic-plugin-directory; do
  claude plugin list 2>/dev/null | grep -q "❯ $p" && echo "plugin $p: installed" || claude plugin install "$p" 2>&1 | tail -1
done
# pick up a changed local version
claude plugin update pstack@bossmann-local >/dev/null 2>&1 || true
claude plugin update superpowers@bossmann-local >/dev/null 2>&1 || true
echo "install-claude-plugins: done (restart Claude Code)"
