---
name: avaliar-como-professor
description: Avalia um trabalho da PUCPR como se fosse o professor da disciplina e dá a nota por critério da rubrica. Chama um agente que lê o enunciado, a rubrica, o plano de ensino e os slides do professor, inspeciona a entrega e devolve nota, evidências, o que falta para 10 e as perguntas que o professor faria. Use quando o aluno pedir "avalia como o professor", "que nota eu tiro", "corrige como o professor", "nota do trabalho", "simula a correção", ou antes de entregar um trabalho, mesmo sem dizer o nome da skill.
---

# Avaliar como o professor

O avaliador é um agente separado (contexto limpo), para não herdar a simpatia de quem construiu o trabalho. Ele só conhece o que o professor conhece: o enunciado, a rubrica, o que foi ensinado e a entrega.

## 1. Juntar as fontes (você, antes de chamar o agente)

1. **Pasta da disciplina:** a pasta acima da entrega que tem `Plano-de-Ensino.md` (ou o PDF do plano) e `AGENTS.md`. Anote o nome do professor (plano de ensino ou `AGENTS.md`).
2. **Enunciado e rubrica:** o arquivo do trabalho (geralmente em `Atividades/`, ou na pasta da entrega, como `Projeto CSCF - 2026.2.md`). Se a rubrica não estiver no enunciado, procure no Canvas exportado ou pergunte ao aluno. **Sem rubrica, não invente pesos:** avalie por exigência e diga que a nota é estimada.
3. **O que o professor ensinou:** `Slides/`, `Modulos/`, `Formativas/`, `Plano-de-Ensino.md`, `COURSE.md`. Liste só os arquivos ligados ao tema do trabalho (pelo título). PDFs grandes: o agente pode converter com `markitdown` (skill `digest-files`) ou ler as páginas que importam.
4. **A entrega:** a pasta do projeto (código, docs, vídeo, links). Liste os comandos de verificação que existem (testes, `scripts/verify`, build) e diga ao agente quais pode rodar.
5. **Regras do curso:** o que o `AGENTS.md` diz sobre o que é do aluno.

## 2. Chamar o professor

Use a ferramenta Agent (`general-purpose`, foreground) com o texto de `prompt-professor.md`, preenchendo os campos entre `{chaves}`. Regras do brief:

- Somente leitura: não editar, não fazer commit, não publicar em serviços externos (broker, site) fora de prefixos de teste.
- Evidência para cada ponto (`arquivo:linha`, saída de comando, trecho do enunciado). Sem evidência, o critério não recebe o nível.
- Ser exigente como o professor: dúvida entre dois níveis, fica com o menor e explica o que faltou.
- Nada que o professor não pediu nem ensinou pesa na nota (pode virar comentário).

Para uma nota mais confiável, rode **dois** professores independentes em paralelo (mesmo prompt) e compare: se discordarem em um critério, mostre os dois argumentos.

## 3. Devolver ao aluno

- Tabela: critério, peso, nível, nota, evidência curta.
- Nota final e o que falta para 10, em ordem de pontos ganhos por esforço.
- As perguntas que o professor faria na apresentação, com a resposta que o projeto sustenta.
- Separe o que foi verificado (comando rodado, arquivo lido) do que é suposição (ex.: "supondo que o Wokwi rode como o código diz").
- Não corrija nada sem o aluno pedir; a skill só avalia.
