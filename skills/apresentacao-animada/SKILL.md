---
name: apresentacao-animada
description: Motion graphics em HTML renderizado para MP4. Dois modos. Entrega - apresentação de trabalho acadêmico com notas do apresentador, folhas, roteiro de gravação e montagem do vídeo com a voz do aluno. Redes - vídeo vertical curto de um projeto ou produto, só legenda, música NCS opcional. Use em "monta a apresentação", "apresentação animada", "motion graphics", "vídeo da entrega", "roteiro do vídeo", "folhas para apresentar", "vídeo para as redes", "vídeo para postar", "motion da extensão", "prompt de vídeo", "storyboard", ou quando um enunciado exigir vídeo/demonstração.
---

# Apresentação animada e motion

Arquivos de apoio nesta pasta: `estilos.md` (bloco STYLE, lista "evitar", 5 estilos prontos, UI viva, loop), `pedido.md` (modelo de pedido por tipo de vídeo, mensagens de correção), `exemplo.html` (página 9:16 mínima com `renderAt` e `TEXTS`), `scripts/`.

## Pré-requisitos

- **Node** 20 ou mais novo, com `playwright-core@1.65.1` instalado na pasta do vídeo (seção 5).
- **ffmpeg** e **ffprobe** no `PATH` (render, mixagem e conferência).
- **`rsvg-convert`** (pacote `librsvg`; macOS `brew install librsvg`, Debian/Ubuntu `apt install librsvg2-bin`), só no modo Entrega: desenha a legenda de cada cena como PNG, porque muitos builds do ffmpeg vêm sem o filtro `drawtext`. Se `ffmpeg -filters | grep drawtext` achar o filtro, pode usar `drawtext` no lugar.
- **Navegador Chromium** (Chrome, Brave ou Chromium); o render não baixa navegador. No macOS ele acha o app em `/Applications`; em outro caso, aponte o executável com `--navegador <caminho>` ou `NAVEGADOR=<caminho>` (ex.: `NAVEGADOR=$(command -v chromium) node render.mjs ...`).
- **Python 3**, só para a música (`scripts/ncs.py`).

## 1. Modo e briefing

| Pedido | Modo | Entrega |
|---|---|---|
| Trabalho acadêmico, apresentação, vídeo da entrega com voz | **Entrega** (seção 3) | HTML com teclas + notas, `FOLHAS.md`, `APRESENTACAO.md`, roteiro, `montar.sh`, MP4 final |
| Vídeo para postar (Reels, TikTok, Shorts, LinkedIn) de um projeto ou produto | **Redes** (seção 4) | um MP4 vertical (padrão `~/Downloads`), mais a versão com música se pedir |

Sem pedido de formato: Entrega para trabalho acadêmico, Redes para produto. Não pergunte o modo.

**Briefing numa mensagem só.** Antes de começar, leia o que já existe (pedido, enunciado, README, código) e pergunte **uma vez**, numa só mensagem, só o que faltar destes cinco: (1) o que o espectador precisa entender ao fim, em uma frase; (2) duração e proporção; (3) fatos reais que podem aparecer (números, nomes, telas) e onde conferi-los; (4) áudio: mudo, NCS, trilha própria (BPM) ou voz do aluno; (5) estilo: um de `estilos.md`, a identidade do projeto ou "você escolhe". O que o usuário não responder vira padrão declarado (ex.: "30 s, 9:16, mudo, estilo do projeto"). Não pergunte de novo depois. Se o pedido já cobre os cinco, não pergunte nada. Para o usuário montar o pedido, aponte `pedido.md`.

## 2. Regras dos dois modos

1. **Verdade:** toda frase na tela bate com o código, o README ou o enunciado (valores, nomes, botões, resultados de teste). Recurso que não existe ou ainda não foi lançado não entra. Afirmação sobre o mundo real só com fonte; sem fonte, sai.
2. **Dados:** dados reais do projeto (log, saída de comando) quando forem do projeto; dados de pessoa (notas, nomes, RA, e-mail) sempre inventados. Números de exemplo seguem as regras do produto (arredondamento, pesos): calcule e confira.
3. **Determinístico:** `window.renderAt(t)` desenha cada quadro como função pura do tempo; nada de contador de quadros, `Date.now()` ou aleatório sem semente; `window.TOTAL` em segundos; `window.pronto = true` depois de `document.fonts.ready`. Aberto no navegador, a página toca sozinha (Espaço pausa, ← → 1 s). Modelo: `exemplo.html`.
4. **Estilo em números:** escreva o bloco `STYLE` de `estilos.md` (paleta hex, escala de tipo, curvas nomeadas, fps, câmera, margens, transição, "evitar") no topo do `<style>` como comentário e em `:root`, e confira os quadros contra ele. Se o projeto tem identidade (site, extensão), copie os tokens, as fontes (`@font-face` com caminho relativo ao `.woff2` do repositório) e o logo (`<symbol>` SVG); não invente outro estilo. A lista "evitar" padrão vale sempre.
5. **Tempo de leitura:** cada texto fica na tela pelo menos `letras/15 + 1,5 s`; título pelo menos 4 s, legenda pelo menos 1,8 s. Declare `window.TEXTS` (todo texto visível, com `kind` = `title`, `subtitle` ou `text`, contando só o tempo em que está inteiro na tela, sem as transições) e rode `--leitura` (seção 5). Texto que não cabe no tempo: corte o texto ou alongue a cena, nunca aceite a violação.
6. **Créditos:** todo ativo de terceiros (fonte, trilha, imagem, mapa, ícone, biblioteca embutida) entra num `CREDITS.md` ao lado do HTML: nome, autor, licença, link, onde aparece. Sem licença que permita o uso, não entra. Referência de estilo ensina, não se copia (personagem, logo, melodia).
7. **Disciplina:** em coursework, siga o `AGENTS.md` da pasta do curso, se existir (o que é do aluno e o que pode ser feito por IA).

## 3. Modo Entrega

Se o usuário tiver uma apresentação anterior neste formato, leia antes e copie a estrutura, não o conteúdo. Sem modelo, siga as peças abaixo. O formato: guia com cola rápida, cena por cena, glossário e perguntas; folhas Na tela / Falar / Mais para falar / Se perguntarem; teclas Espaço, ←, →, R, N (notas em outra janela).

Antes: leia o enunciado inteiro e faça a tabela "exigência → cena" (cada item que o vídeo precisa mostrar e cada pergunta que a equipe deve saber responder vira uma cena).

Peças:
1. **`docs/apresentacao/folhas.json`**: uma parte por cena, com `titulo`, duração, `tela`, `falar`, `mais` e `pergunta` [pergunta, resposta].
2. **`template.html` + `build.py`**: geram `apresentacao-animada.html` (um arquivo, abre offline: fontes e bibliotecas embutidas) e regeneram `docs/FOLHAS.md`. Teclas: Espaço, ←, →, R (reinicia), N (notas em outra janela).
3. **Motion** (método https://awesomeclaude.ai/claude-motion-graphics): abertura com o lugar real quando fizer sentido (prédios do OpenStreetMap via Overpass, uma consulta salva em JSON, crédito "© OpenStreetMap contributors" na tela, extrudados em Three.js); dados reais do projeto mostrados como saíram (estilo "história de dados" de `estilos.md`); demo de tela no estilo "UI viva".
4. **Render:** `scripts/render.mjs` desta skill com `--w 1920 --h 1080` (seção 5).
5. **`video/roteiro.md`**: por cena, o que deixar na tela, ações em ordem, duração e a **fala exata** (`falaNN`), com os nomes reais dos botões.
6. **`video/montar.sh`**: junta `video/gravacoes/cenaNN.mov` + `falaNN.m4a` (o usuário grava tela e voz) com o MP4 animado; normaliza para 1920x1080 30 fps; legenda com o título da cena via `rsvg-convert` (ver Pré-requisitos); concatena em `video/<projeto>-final.mp4`. Teste com arquivos falsos (`testsrc2` + `sine`) antes de o usuário gravar.
7. **`docs/APRESENTACAO.md`**: cola rápida, como usar, cenas, glossário, perguntas do enunciado com resposta pronta.

## 4. Modo Redes (só motion)

Sem folhas, roteiro, `montar.sh` nem gravações. Se o usuário tiver um vídeo anterior neste formato, copie dele o motor de animação do `<script>` e os estilos de legenda, e troque cenas e tokens; sem modelo, escreva o motor descrito abaixo.

- **Storyboard antes do código.** Mostre uma tabela com tempos e **espere o OK** antes de escrever HTML. Uma linha por cena: `início–fim (s)`, o que aparece, **leituras** (cada coisa que o espectador precisa ler ou notar, com o tempo de cada uma pela regra 5), texto exato na tela (com a fonte do `grep`), transição de saída. Some as leituras: se passam do tempo da cena, corte leitura ou alongue a cena. Corrigir uma linha da tabela custa uma mensagem; corrigir cena pronta, um render.
- **Formato:** 1080x1920, 30 fps, 30 a 40 s, 6 a 8 cenas de 4 a 6 s (cena com título: pelo menos 4,8 s, porque o título fica 4 s inteiro na tela e as trocas comem o resto). Cena 1 é o gancho (a dúvida do público em serifa grande, 150 a 170px, que se entende sem som no primeiro segundo); a última é a marca, a promessa em 3 linhas curtas e o link num botão, parada de 0,8 a 1,2 s no fim. Algo se move em toda cena; um conceito novo por vez. Termine num quadro que funciona em loop (loop perfeito: `estilos.md`).
- **Zonas seguras:** nada importante acima de 160px nem abaixo de 1590px (botões e legenda do app); marca pequena no topo a partir de 170px; título da cena a partir de 300px; cards entre 640 e 1460px.
- **Legenda queimada:** uma frase por cena que se entende sem som e cabe no tempo da regra 5 (40 letras pedem 4,2 s na tela, então cena de 5 s); faixa da cor do texto com letra clara, 44px, `box-decoration-break:clone`, `bottom:330px`. Card nunca encosta na legenda.
- **Conteúdo:** um recurso por cena, com o texto real da interface (copie a string do código com `grep`). Mostre a ação (digitar, clicar com cursor, marcar ✓, data riscada) e o resultado, não uma lista de recursos. Tela de produto: regras de "UI viva" em `estilos.md` (UI refeita em HTML, nunca screenshot).
- **Motor:** `data-in` (segundo de entrada), `data-a` (`up`, `left`, `drop`, `pop`, `fade`, `sx` para marca-texto e risco), `data-d` (duração); cenas com `data-ini`/`data-fim` e troca cruzada de 0,4 s; interações escritas em `renderAt(t)`; `window.TEXTS` lido das mesmas cenas (como em `exemplo.html`).
- **Saída:** `~/Downloads/<nome>-video.mp4` (ou `--saida`). No repositório, só o HTML, o `CREDITS.md` e o `package.json`; `node_modules/` e `frames/` no `.gitignore`.
- **Música (se pedir; padrão NCS):** `python3 -I scripts/ncs.py` lista as faixas da home do ncs.io (título, artista, gênero, segundo do trecho forte, slug); `python3 -I scripts/ncs.py get "<título>" <arquivo>.mp3` baixa. Prefira House, Deep House ou Future Bass para produto. Mixe (áudio nunca gravado do navegador):

  ```sh
  ffmpeg -i video.mp4 -ss <trecho forte> -t <duração> -i faixa.mp3 \
    -filter_complex "[1:a]afade=t=in:d=0.3,afade=t=out:st=<duração-2.5>:d=2.5,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart <nome>-video-ncs.mp4
  ```

  Mantenha a versão muda. Você não ouve a faixa: diga qual escolheu e por quê (gênero, trecho marcado) e ofereça trocar. **Uso e crédito ([política NCS](https://ncs.io/usage-policy)):** livre para criadores independentes no YouTube e na Twitch, inclusive monetizado, com o crédito do artista e da faixa na descrição. Copie o crédito da página da faixa (`ncs.io/<slug>`; se o slug saiu vazio, procure a faixa no ncs.io) ou da descrição do vídeo dela no canal oficial; não monte de memória. A política também pede o link do upload da NCS (o vídeo da faixa no canal oficial) na descrição; em live na Twitch ou no YouTube, use a linha que ela dá: "Music provided by http://spoti.fi/NCS". A política não cita TikTok, Reels, Shorts nem LinkedIn, e marca ou serviço promovendo um produto deve falar com o time de parcerias da NCS: nesses casos, diga ao usuário para conferir a política (ou pedir licença) antes de publicar.

## 5. Ferramentas desta skill

- **`scripts/render.mjs`**: copie para a pasta do vídeo, `npm i playwright-core@1.65.1` ali (sem baixar navegador; usa `--navegador`/`NAVEGADOR`, senão Brave, Chrome ou Chromium).
  - `node render.mjs --html x.html` → `~/Downloads/x-video.mp4` (1080x1920, H.264 com cor marcada BT.709: primárias, transferência, matriz, faixa tv); `--w 1920 --h 1080` para 16:9; `--de 7 --ate 13` para um trecho; `--saida` muda o arquivo. Se o MP4 de saída já existe, o render para com erro; use outra `--saida` ou `--sobrescrever`.
  - `--quadros 2.5,9,15 --pasta frames` só grava PNGs para revisão.
  - `--leitura` só confere o tempo de leitura de `window.TEXTS` (função `t => [{text, kind}]` ou lista `[{text, kind, from, to}]`): imprime cada texto curto com o tempo que teve e o que precisa, e sai com código 3.
  - `--relogio` para página animada por GSAP, CSS ou `requestAnimationFrame` sem `renderAt`: relógio virtual (`performance.now`, `Date.now` e rAF falsos; animações CSS/Web Animations pausadas no tempo de cada quadro). Duração de `window.TOTAL` ou `--duracao <s>`. Não cobre `setTimeout`/`setInterval`, iframes, animação ligada ao scroll, nem os eventos de fim (`finished`, `animationend`): encadeie cenas pelo tempo. Setup assíncrono (fetch, imagem): comece com `window.pronto = false` e marque `true` sem depender de rAF ou animação (o relógio só anda depois). `new Date()` continua no tempo real. Tempos de `--quadros`/`--de` caem no quadro mais próximo. Também: `playbackRate`, `reverse()`, `animation-play-state` e seek próprio da página são sobrescritos (a animação anda para a frente a 1x desde que apareceu); laço de espera em `Date.now` durante o carregamento trava; animação criada dentro de promise começa um quadro depois. Com GSAP, prefira o modo padrão: timeline pausada e `window.renderAt = t => tl.seek(t)`.
  - Sai com código 2 se a página teve erro ou se alguma `@font-face` não carregou (a fonte reserva entra calada sem esse aviso).
- **Folha de contato:** `ffmpeg -pattern_type glob -i 'frames/t*.png' -vf "scale=432:768,tile=5x2:padding=8:color=gray" frames/sheet.png` e leia a imagem (10 quadros num print só; 16:9: `scale=768:432,tile=3x3`, 9 quadros).
- **Prévia leve:** `ffmpeg -i x.mp4 -vf "scale=540:960,fps=24" -c:v libx264 -crf 30 -an previa.mp4` (16:9: `scale=854:480`).

## 6. Rodadas e conferência

**Rodadas.** Storyboard (OK do usuário) → quadros de estilo (`--quadros` de 2 ou 3 cenas, conferidos contra o STYLE) → render completo → conferência abaixo → **uma rodada de correção** feita por você antes de entregar. Pedidos de mudança do usuário: uma mudança por vez, mantendo o resto (frases em `pedido.md`).

1. Quadros do meio de cada cena na folha de contato: texto cortado, card sobre a legenda, fonte errada, palavra órfã numa linha, item pequeno demais para celular, algo da lista "evitar".
2. Quadros das trocas, tirados do MP4 final (`ffmpeg -ss <t> -i x.mp4 -frames:v 1`): nenhuma cena fantasma fora da sua janela.
3. `node render.mjs --html x.html --leitura` sai 0.
4. `ffprobe -v error -show_streams -show_entries format=duration x.mp4`: tamanho, `r_frame_rate=30/1`, `color_space`, `color_transfer` e `color_primaries` = `bt709`, `color_range=tv`, duração; versão muda sem stream de áudio; versão com música em torno de -14 LUFS (`-af ebur128`).
5. Quadro preto: `ffmpeg -i x.mp4 -vf blackdetect=d=0.1:pix_th=0.10 -an -f null - 2>&1 | grep black_start` sem saída. Em estilo escuro, um fundo quase preto com pouco texto também acusa: abra o quadro do tempo indicado antes de mudar algo.
6. Verdade: cada frase da tela conferida com `grep` no código ou no README. Na Entrega, uma review em contexto limpo: "toda afirmação da apresentação e do roteiro bate com o código e com a pesquisa?". Corrija e renderize de novo.
7. Arquivos acima de ~50 MB e os quadros de revisão ficam fora do git. Commit, push e publicação só quando o usuário pedir.

**Relatório final:** caminho do MP4, storyboard como ficou, o bloco STYLE usado, `CREDITS.md`, e os dois momentos mais fracos com como melhorar.
