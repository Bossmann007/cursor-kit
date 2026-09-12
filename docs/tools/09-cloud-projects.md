# Cloud / aba Projects

A aba **Projects** usa Cloud Agents (VM Ubuntu). Ela **não** lê `~/.cursor/skills` do teu Mac.

## Opção C (este kit): install no Build

### Se o Project for o próprio `cursor-kit`

O repo já tem [`.cursor/environment.json`](../../.cursor/environment.json). No Build, roda:

```bash
bash scripts/install-cloud-skills.sh
```

Isso clona/atualiza o kit e copia `skills/*` → `~/.cursor/skills/` **dentro da VM**.

### Se o Project for outro repo (PUCPR, app, etc.)

1. Copia o template:

```bash
mkdir -p .cursor
cp /path/to/cursor-kit/templates/cloud/environment.json .cursor/environment.json
# ou baixe:
# curl -fsSL https://raw.githubusercontent.com/Bossmann007/cursor-kit/master/templates/cloud/environment.json \
#   -o .cursor/environment.json
```

2. Commit e push no **repo ligado ao Project**.
3. No dashboard Cloud Agents, gera um **Build** novo (ou deixa o próximo Build rodar o `install`).
4. Abre um **agent novo** no Project (chat antigo não herda skills do Build novo).

Conteúdo do template:

```json
{
  "install": "curl -fsSL https://raw.githubusercontent.com/Bossmann007/cursor-kit/master/scripts/install-cloud-skills.sh | bash"
}
```

### Variáveis opcionais

| Env | Default | Uso |
|-----|---------|-----|
| `CURSOR_KIT_REPO` | `https://github.com/Bossmann007/cursor-kit.git` | Fork |
| `CURSOR_KIT_REF` | `master` | Branch/tag |
| `CURSOR_KIT_DIR` | `$HOME/.cursor-kit-src` | Cache do clone na VM |

## O que isso instala

Só skills **versionadas em** `cursor-kit/skills/` (hoje: `setup-project`, `setup-pucpr`).

Skills só no teu laptop (`~/.cursor/skills/grill-me`, Matt, etc.) **não** entram por este script. Para essas:

- liga **Sync Skills for Cloud Agents**, ou
- copia a skill para `cursor-kit/skills/` e dá push, ou
- coloca `.cursor/skills/<nome>/` no próprio repo do Project.

## Depois do Build

No agent do Project, testa:

```text
/setup-project
```

ou

```text
/setup-pucpr
```

Se o `/` não listar a skill: Build falhou, `environment.json` não está no repo do Project, ou o chat é anterior ao Build.
