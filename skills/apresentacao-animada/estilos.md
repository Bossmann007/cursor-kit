<!-- Ideia de "estilo como números" e regras de alguns estilos adaptadas, em paráfrase, de https://awesomeclaude.ai/claude-motion-graphics (MIT). -->

# Estilos em números

Adjetivo ("moderno", "elegante") vira sempre o mesmo vídeo genérico. Estilo bom é uma lista de números que dá para conferir num quadro. Escreva o bloco abaixo antes do código, cole como comentário no topo do `<style>`, passe os valores para `:root` e confira a folha de contato contra ele.

## Bloco STYLE

```text
STYLE <nome>
meio:       <uma frase: o que é o vídeo como material, ex. "interface de produto refeita em HTML">
paleta:     fundo #...  texto #...  apoio #...  destaque #...  (destaque em um só elemento por cena)
tipo:       <família(s)>; escala em px a 1080 de largura: título / subtítulo / corpo / legenda / rótulo
curvas:     entrada = cubic-bezier(...)  saída = cubic-bezier(...)  (nomeie e use só estas)
tempo:      movimento N quadros; grupo entra com N quadros de intervalo; troca de cena N s
fps:        30 (só mude se o estilo pedir)
câmera:     parada | zoom lento x% por cena | segue o cursor; sem tremida
margens:    N px (5% da largura) em volta; zonas seguras do modo Redes por cima
transição:  <wipe | corte | troca cruzada 0,4 s | forma que cresce>; uma só no vídeo inteiro
evitar:     lista padrão + <extras do estilo>
```

## Lista "evitar" padrão (vale para todo estilo)

Explosão de partículas, lens flare, neon brilhando, separação RGB, glitch, easing elástico em tudo, gradiente só de enfeite, sombra pesada, texto que repete o que a imagem já mostra, tempo morto (cena em que nada se move), mais de duas famílias de fonte, ícone genérico no lugar da interface real.

## Cinco estilos prontos

### Keynote escuro (produto, anúncio)

```text
STYLE keynote-escuro
meio:       palco escuro de lançamento, um número ou frase por vez
paleta:     fundo #0b0d12  texto #f5f7fa  apoio #8a93a6  destaque #4f8cff
tipo:       Inter ou a fonte do projeto; 150 / 96 / 56 / 44 / 32; peso 700 nos títulos
curvas:     entrada = cubic-bezier(.16,1,.3,1)  saída = cubic-bezier(.7,0,.84,0)
tempo:      movimento 30–45 quadros; grupo com 4 quadros de intervalo; cena 4–6 s
fps:        30
câmera:     parada; um zoom de 104% ao longo da cena final
margens:    54 px
transição:  troca cruzada 0,4 s
evitar:     padrão + mais de uma cor de destaque, fundo com textura
```
Número-herói: ocupa ~30% da altura e conta até o valor exato (inteiro arredondado só no último quadro). Revelação de palavra por uma faixa de luz que passa da esquerda para a direita em 18 quadros.

### UI viva (feature, demo de tela)

```text
STYLE ui-viva
meio:       a interface real refeita em HTML/CSS com o texto e as cores do código
paleta:     tokens do projeto; fora da UI: fundo #f4f5f7  texto #111418  destaque = cor primária do projeto
tipo:       a fonte do projeto; tamanhos da própria UI x 1,5 a 2 para caber no celular
curvas:     cursor = cubic-bezier(.45,0,.2,1)  zoom = cubic-bezier(.16,1,.3,1)
tempo:      cursor viaja 20–30 quadros; para 8 quadros antes do clique; uma ação a cada 3–4 s
fps:        30
câmera:     zoom 1,6x no detalhe que muda, segura, volta em 24 quadros
margens:    54 px; a janela da UI ocupa a faixa de cards (640–1460 px no 9:16)
transição:  a própria ação leva à tela seguinte; troca cruzada 0,4 s só entre recursos
evitar:     padrão + screenshot, mockup com texto inventado, recurso que o produto não tem
```
Regras: o cursor anda em curva, nunca em linha reta perfeita; clique mostra um anel de 12 quadros; texto digitado entra a 12–18 letras por segundo; o resultado da ação fica parado pelo menos 1,5 s. Toda string da tela sai do código (`grep`).

### Legendas e tipo cinético (vertical, sem som)

```text
STYLE legendas
meio:       frases curtas que contam a história sozinhas, no miolo de 80% da tela
paleta:     fundo #111111  texto #ffffff  apoio #9a9a9a  destaque #ffd23f (uma palavra por frase)
tipo:       sans grossa (Inter 800 ou a do projeto); 170 / 110 / 72 / 44 / 32
curvas:     entrada = cubic-bezier(.34,1.4,.64,1) (passa 6 quadros e assenta)  saída = cubic-bezier(.7,0,.84,0)
tempo:      blocos de 1 a 4 palavras; cada bloco segue a regra de leitura; 3 quadros entre palavras do bloco
fps:        30
câmera:     parada; uma escala de 100→103% por bloco
margens:    108 px (10%) nas laterais; nada nos 15% de baixo além da legenda do app
transição:  corte seco no tempo do bloco
evitar:     padrão + destaque por cor e escala ao mesmo tempo, frase inteira numa linha só
```

### História de dados (resultados, métricas)

```text
STYLE dados
meio:       um gráfico por cena, cada número tirado dos dados reais com a fonte na tela
paleta:     fundo #fffdf7  texto #222222  apoio #8d99ae  destaque #d62828  série 2 #457b9d
tipo:       sans com algarismos tabulares (font-variant-numeric: tabular-nums); 120 / 72 / 44 / 32 / 28
curvas:     entrada = cubic-bezier(.22,1,.36,1)
tempo:      barra cresce da base em 20 quadros; contador para no valor exato; uma série por vez
fps:        30
câmera:     parada
margens:    54 px; rótulos de eixo nunca menores que 28 px a 1080
transição:  o gráfico vira o próximo (barras se reorganizam), sem troca cruzada
evitar:     padrão + 3D, arco-íris, eixo cortado sem aviso, número sem fonte
```
Abra pelo número mais surpreendente; uma anotação por cena diz o que importa; última cena: linha de fonte e conclusão em uma frase.

### Suíço (marca, abertura, changelog)

```text
STYLE suico
meio:       grade de 12 colunas com tipo grande e blocos de cor chapada
paleta:     fundo #f2f0eb  texto #111111  apoio #6b6b6b  destaque #e4002b
tipo:       uma família só (Helvetica Neue, Inter ou a do projeto); 170 / 96 / 56 / 40 / 28; alinhado à esquerda
curvas:     tudo = cubic-bezier(.7,0,.2,1)
tempo:      wipe/clip de 12–18 quadros; grupo com 3 quadros de intervalo
fps:        30
câmera:     parada
margens:    4% (43 px) e grade de 12 colunas com 24 px de gutter
transição:  wipe por clip-path, nunca troca cruzada
evitar:     padrão + overshoot, sombra, segunda família, texto centralizado
```

## Loop perfeito

Para fundo ou vídeo que repete: todo movimento contínuo usa `Math.sin` e `Math.cos` de `2 * Math.PI * t / T` (com `T` = `TOTAL` ou um divisor dele), então o último quadro emenda no primeiro. Aleatório com semente fixa e fase também em função de `t`. Confira: quadro `0` e quadro `TOTAL` (`--quadros 0,<TOTAL>`) iguais.
