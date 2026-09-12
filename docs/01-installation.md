# Instalação

Referência rápida. Para o caminho narrado, use o [playbook](02-playbook-onboarding.md).

## 1. Clonar

```bash
git clone https://github.com/Bossmann007/cursor-kit.git
git clone https://github.com/Bossmann007/token-engine.git

# opcional (atalhos usados na docs)
ln -sfn /ABS/PATH/TO/cursor-kit ~/cursor-kit
ln -sfn /ABS/PATH/TO/token-engine ~/token-engine
```

Substitua `/ABS/PATH/TO/...` pelo caminho real. Não commite paths da sua máquina em templates públicos.

## 2. token-engine (venv + MCP)

```bash
cd ~/token-engine   # ou o clone real
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[cursor,dev]"
token-engine cursor-setup
token-engine benchmark --check-baseline
```

Copie o padrão de [`mcp.json.template`](../mcp.json.template) para `~/.cursor/mcp.json` (ou mescle). Troque os placeholders:

- `command` → `…/token-engine/.venv/bin/python` (Windows. `…\.venv\Scripts\python.exe`)
- `PYTHONPATH` → `…/token-engine/src`

Em Cursor. Settings → MCP → enable `token-engine` (e `codebase-memory` / `context7` se usar). Reload da janela.

## 3. Hooks do kit → `~/.cursor`

```bash
~/cursor-kit/sync-hooks.sh
# Windows: ~\cursor-kit\sync-hooks.ps1
```

Confirme `~/.cursor/hooks.json` com sessionStart / postToolUse / stop. Detalhes em [ARCHITECTURE](ARCHITECTURE.md).

## 4. Plugin cursor-kit + skills

```bash
ln -sfn ~/cursor-kit ~/.cursor/plugins/local/cursor-kit
```

Plugins recomendados (UI do Cursor, não inventados pelo kit).

- continual-learning
- cursor-team-kit
- pstack (depois `/setup-pstack` se `~/.cursor/rules/pstack-models.mdc` faltar)

Rules globais esperadas (ponytail, caveman, token-engine, cbm-first) costumam já viver em `~/.cursor/rules/`. O kit **não** as copia para cada repo.

## 5. Skills Matt Pocock (opcional mas usado pelo `/setup-project`)

Se ainda não tiver `~/.cursor/skills/setup-matt-pocock-skills`:

```powershell
# Windows (script do kit)
~\cursor-kit\install-skills.ps1
```

No macOS, clone/copie as skills Matt para `~/.cursor/skills/` conforme [SKILLS-CURATED](../SKILLS-CURATED.md), ou rode o fluxo que você já usa. `/setup-project` **delega** ao `setup-matt-pocock-skills`; não o reimplementa.

## 6. Scaffold manual de um repo (fallback)

Preferível. `/setup-project` no chat do Cursor.

Fallback:

```bash
~/cursor-kit/install.sh /ABS/PATH/TO/your-repo
```

## 7. Aba Projects (Cloud)

Skills do laptop **não** entram sozinhas. Opção C deste kit:

- Repo `cursor-kit`: já tem `.cursor/environment.json` → Build instala `skills/` na VM.
- Outro repo: copia `templates/cloud/environment.json` → `.cursor/environment.json`, commit, Build novo.

Detalhes: [tools/09-cloud-projects.md](tools/09-cloud-projects.md).

## Verificação mínima

1. MCP `token-engine` aparece enabled.
2. `sync-hooks` rodou sem erro.
3. Skill `/setup-project` aparece (plugin ou `~/.cursor/skills/setup-project`).

Problemas. [TROUBLESHOOTING](TROUBLESHOOTING.md).
