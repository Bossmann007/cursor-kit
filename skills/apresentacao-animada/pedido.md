<!-- Ideia de esqueleto fixo + blocos por tipo adaptada, em paráfrase, de https://awesomeclaude.ai/opus-video-prompts (rodapé do site: MIT; LICENSE do repositório: CC0 1.0). -->

# Pedido de vídeo em um minuto

Exceção intencional à regra do kit de prompts para colar em inglês: este modelo fica em português porque é o Enzo quem o preenche, em português.

Copie o esqueleto, troque os `<...>` e cole as linhas da tabela. Tudo o que ficar de fora vira o padrão da skill (seção 1 do `SKILL.md`).

```text
/apresentacao-animada
Vídeo <tipo> sobre <assunto>. <duração> s, <proporção>.
Quem assiste precisa sair entendendo: <uma frase>.
Fatos (use só estes, confira no código/README): <lista ou caminho>.
Cenas: <batidas do tipo, tabela 1>.
Estilo: <nome de estilos.md | identidade do projeto | você escolhe e diz qual numa linha>.
Som: <linha da tabela 2>.
Storyboard com tempos primeiro; espere meu OK.
```

## 1. Batidas por tipo

| Tipo | Batidas (uma cena cada) |
|---|---|
| Lançamento de produto | a dor do público · o produto em uma frase · o recurso principal em ação · prova (número real) · marca, promessa e link |
| Recurso / demo de tela | a tela vazia ou o problema · o cursor faz a ação principal · a interface reage, zoom no detalhe · o resultado que a pessoa ganha |
| Explicação | a pergunta de quem assiste · a ideia central numa imagem · passo a passo, um por cena · um exemplo resolvido · a conclusão numa frase |
| Dados / resultados | o número mais surpreendente, grande · o gráfico montando série por série · uma anotação do que importa · fonte e conclusão |
| Changelog | o que mudou, em 3 itens · antes e depois de cada item (6–8 s) · onde pegar a versão |
| Marca / logo | as formas do logo real se montam (não redesenhe) · nome · logo parado 1 s |
| Entrega acadêmica | uma cena por exigência do enunciado (tabela "exigência → cena") · resultado · conclusão |

## 2. Linha de som

| Escolha | Linha |
|---|---|
| Mudo | Sem áudio; o ritmo vem do movimento, cortes numa grade de 120 BPM implícita. |
| NCS | Música NCS (a skill escolhe e explica); versão muda também. |
| Trilha própria | Trilha `<arquivo>`, `<BPM>` BPM; cortes caem na grade; o ffmpeg mixa, não gere áudio. |
| Voz do aluno (Entrega) | Roteiro de fala por cena antes; texto na tela mais curto que a fala. |

## 3. Proporção

| Onde passa | Tamanho | Área útil |
|---|---|---|
| Reels, TikTok, Shorts (9:16) | 1080x1920 | zonas seguras do modo Redes (160–1590 px) |
| YouTube, site, Entrega (16:9) | 1920x1080 | margem de 5% (96 px) |
| LinkedIn, X (1:1) | 1080x1080 | margem de 5% (54 px) |
| Feed do Instagram (4:5) | 1080x1350 | margem de 5% (54 px) |

O `render.mjs` sai em 9:16 por padrão; em qualquer outra proporção passe `--w` e `--h` (16:9: `--w 1920 --h 1080`).

## Correções em rodadas

Uma mudança por mensagem e diga o que fica. Frases prontas:

- "Mantém tudo; muda só a cena 3: <o quê>."
- "Mais devagar no meio (cenas 3 a 5); o resto igual."
- "Menos texto: mostra, depois rotula uma vez."
- "Usa a interface real em HTML, não screenshot."
- "Em toda cena algo precisa se mexer."
- "A troca de cena carrega o movimento da anterior."
- "Só os momentos-chave caem na batida."
