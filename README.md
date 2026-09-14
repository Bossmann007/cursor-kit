<!-- ENZO-PORTFOLIO-BRAND -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:111111,100:7751FF&height=165&section=header&text=Cursor%20Kit&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Cursor-native%20toolkit%20for%20disciplined%20agent%20development.&descAlignY=57&descSize=14" alt="Cursor Kit" />
</p>

<p align="center"><strong>Python · Cursor · Agents</strong></p>

---

# Cursor Kit

**Repo:** [Bossmann007/cursor-kit](https://github.com/Bossmann007/cursor-kit) · pares com [token-engine](https://github.com/Bossmann007/token-engine)

Stack **Cursor-native** para desenvolvimento com agentes. Templates, hooks, memória e o orquestrador `/setup-project`. A compressão fail-closed vive no token-engine (MCP), não neste repo.

## Comece aqui

1. Leia a [visão geral (pilares)](docs/00-overview.md).
2. Siga a [instalação](docs/01-installation.md) (kit + token-engine + MCP + hooks).
3. Faça o [playbook de onboarding](docs/02-playbook-onboarding.md) até o smoke A/B/C.

Critério de sucesso. Um estranho clona os dois repos e, em cerca de 1–2h, tem fluxo disciplinado no Cursor.

## O que este kit é (e não é)

É runtime e embalagem para **Cursor**. Hooks globais, `.cursor/state`, `AGENTS.md` / `PROJECT.md`, skill `/setup-project`.

Não é um clone do Claude Code. Não inclui Obsidian, Graphify visual, agent-browser nem proxy CLI tipo RTK. Para tokens use [token-engine](https://github.com/Bossmann007/token-engine). Limitações honestas estão no [overview](docs/00-overview.md#limites).

## Atalhos depois do onboarding

| Precisa | Vá em |
|---------|--------|
| Orquestrar um repo | `/setup-project` (skill neste plugin) |
| Prompt colável | [docs/prompts/](docs/prompts/) |
| Quality gates (JS/TS) | [templates/quality-gates/](templates/quality-gates/) + [prompt medir](docs/prompts/05-quality-gates-install.md) |
| Card de ferramenta | [docs/tools/](docs/tools/) |
| Referência profunda | [ARCHITECTURE](docs/ARCHITECTURE.md), [MEMORY](docs/MEMORY.md), [WORKFLOWS](docs/WORKFLOWS.md), [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) |

## Plugin local

Cursor rejeita symlink cujo target fica fora de `~/.cursor/plugins/local/`. Sync ou clone in-place (detalhes em [docs/01-installation.md](docs/01-installation.md)):

```bash
rsync -a --delete --exclude '.git/' --exclude '__pycache__/' \
  ~/cursor-kit/ ~/.cursor/plugins/local/cursor-kit/
~/cursor-kit/sync-hooks.sh
~/cursor-kit/sync-rules.sh   # opcional se o plugin já carrega rules/
# depois: Developer → Reload Window
```

Branch de trabalho pessoal (Enzo). `enzo`. Default do repo continua `master` até merge.

## Testes do kit

```bash
python -m unittest discover -s ~/cursor-kit/tests
```

## Licença

MIT. Ver [LICENSE](LICENSE).

<!-- ENZO-PORTFOLIO-BRAND-FOOTER -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:111111,100:7751FF&height=85&section=footer" alt="Footer" />
</p>
