# Trabalho IV — Ofuscação de código Python

Este trabalho mede quanto custa, em tempo de execução, ofuscar um programa Python.
A ideia de fundo é simples: muitas vezes um código roda num ambiente que não é
confiável (a máquina do cliente, um servidor de terceiros) e a equipe que
desenvolveu quer dificultar que alguém leia a lógica ou mexa no funcionamento.
A ofuscação entra aí como uma camada de defesa. Ela não impede que a pessoa tenha
o arquivo em mãos, mas aumenta bastante o esforço necessário para entender e
alterar o programa.

Nada disso é de graça. Cada transformação aplicada (renomear variáveis, embaralhar
o fluxo, empacotar o binário, etc.) tende a deixar o programa mais lento. Existe,
portanto, um equilíbrio entre segurança e desempenho, e a proposta aqui é
justamente colocar número nesse equilíbrio: rodar o mesmo programa com e sem
ofuscação e comparar os tempos.

## O que é o benchmark

Benchmark é um programa que serve de régua para medir desempenho. Ele não tem uma
utilidade prática em si; existe só para dar uma carga constante e repetível à CPU,
de modo que dê para cronometrar de forma justa. Comparar o mesmo benchmark com e
sem ofuscação isola o efeito da ofuscação, porque a única coisa que muda entre as
execuções é ela.

Os benchmarks usados aqui são dois, com cargas de naturezas diferentes:

- `t4-multi-python.py` — multiplicação de duas matrizes quadradas, com três laços
  aninhados. É uma carga numérica, e o tempo cresce com o cubo do tamanho.
- `t4-palavras.py` — contagem de palavras com um dicionário, sobre um corpus
  gerado em memória a partir de um vocabulário de oito palavras. É uma carga de
  strings e dicionário, e o tempo cresce de forma linear.

Eles foram escolhidos por não lerem disco nem rede, o que poderia mascarar o custo
da ofuscação, e por serem determinísticos — não usam números aleatórios, então as
repetições são comparáveis entre si. Cada programa recebe um único argumento, o
tamanho do problema (ordem da matriz ou número de palavras), arredondado para cima
até o múltiplo de oito mais próximo. É esse argumento que gera as diferentes
"entradas" do experimento.

## Os arquivos

- `t4-multi-python.py` e `t4-palavras.py` — os programas medidos e ofuscados.
  Recebem o tamanho pela linha de comando, conferem o próprio resultado e imprimem
  `ok` ou `bad`, além do tempo gasto na parte principal do cálculo.

- `run_experiment.py` — automatiza o experimento de um benchmark por vez. Roda as
  três versões do programa (original e as duas ofuscadas) para cada entrada,
  repetindo dez vezes cada caso, cronometra tudo e salva os resultados em CSV, já
  com média, mediana, desvio padrão, mínimo e máximo. O benchmark e as entradas são
  definidos nas listas `VERSIONS` e `INPUTS`, no início do arquivo.

- `plot_results.py` — lê os resultados e gera dois gráficos: um de barras com o
  tempo médio de cada versão e um de linha mostrando quantas vezes cada versão
  ofuscada é mais lenta que a original.

- `calibrate.py` — foi escrito para o benchmark anterior (`benchmark.py`) e supõe
  que o tempo cresce de forma linear. Não serve para os scripts `t4-*`, cujas
  entradas precisam ser calibradas na mão.

## Como foi ofuscado

A ferramenta usada foi o PyArmor. Ele obfusca os objetos de código e, por padrão,
envolve cada função num mecanismo que a restaura no momento da chamada e a volta a
ofuscar quando ela retorna. Esse envelope é o eixo que separa as duas configurações
testadas:

- Configuração A — padrão, com o envelope de função ligado. Mais segura.
- Configuração B — mesma ofuscação, mas com o envelope desligado (`--no-wrap`).
  Menos segura.

Comparar as duas mostra o preço concreto dessa camada específica. Como o envelope
age a cada chamada de função e os dois benchmarks fazem o trabalho pesado dentro de
uma única chamada, a diferença entre A e B pode ser pequena.

## Como usar

Dentro do ambiente virtual, com o PyArmor e o matplotlib instalados:

    pip install pyarmor matplotlib

Gere as duas versões ofuscadas a partir dos originais:

    pyarmor gen -O dist_A t4-multi-python.py t4-palavras.py
    pyarmor gen -O dist_B --no-wrap t4-multi-python.py t4-palavras.py

Confira que as três versões de cada benchmark terminam com `ok` (a linha `time`
muda a cada execução):

    python3 t4-multi-python.py 200
    python3 dist_A/t4-multi-python.py 200
    python3 dist_B/t4-multi-python.py 200

    python3 t4-palavras.py 1000000
    python3 dist_A/t4-palavras.py 1000000
    python3 dist_B/t4-palavras.py 1000000

O `run_experiment.py` mede um benchmark por vez. Antes de rodar, aponte a lista
`VERSIONS` para o benchmark desejado:

    VERSIONS = [
        ("baseline", ["python3", "t4-multi-python.py", "{input}"]),
        ("obf_A",    ["python3", "dist_A/t4-multi-python.py", "{input}"]),
        ("obf_B",    ["python3", "dist_B/t4-multi-python.py", "{input}"]),
    ]

Ajuste também a linha `INPUTS` com as três entradas calibradas para a máquina e
para esse benchmark (a menor precisa durar pelo menos vinte segundos no código não
ofuscado, e cada uma deve ser ao menos cinquenta por cento maior que a anterior).
Depois rode o experimento, gere os gráficos e guarde tudo numa pasta própria,
porque a rodada seguinte sobrescreve os CSVs e as imagens:

    python3 run_experiment.py
    python3 plot_results.py
    mkdir -p resultados_multi
    mv resultados_*.csv grafico_*.png resultados_multi/

Repita o processo para o `t4-palavras.py`, guardando os resultados em outra pasta.

O experimento demora, porque são dois benchmarks, três versões, três entradas e dez
repetições de cada caso, ou seja, 180 execuções. Convém deixar a máquina só com isso
rodando.

## Cuidados com a medição

Para os números fazerem sentido, a plataforma precisa estar controlada. Antes de
rodar para valer: feche os outros programas, mantenha o laptop na tomada e, se
possível, fixe a frequência da CPU em modo de desempenho, para que ela não fique
variando sozinha durante os testes.

Há dois tempos diferentes em jogo. O `time` impresso pelos benchmarks cobre só a
parte principal do cálculo. Já o `run_experiment.py` cronometra o processo inteiro,
incluindo a inicialização do Python e do PyArmor, a geração do corpus e a conferência
do resultado, e é esse tempo que vai para os CSVs e os gráficos.

O `t4-palavras.py` guarda o corpus inteiro na memória, cerca de 280 MB a cada cinco
milhões de palavras, e a entrada precisa caber na RAM livre. Se a máquina começar a
usar swap, a medição passa a refletir o disco, e não a ofuscação. Confira o consumo
de memória ao calibrar as entradas.

A base de comparação é sempre o código não
ofuscado na mesma linguagem — um programa em Python é naturalmente mais lento que
o equivalente em C, então não faz sentido comparar entre linguagens; o que
interessa aqui é a diferença entre original e ofuscado dentro do próprio Python.

Também vale testar entradas de tamanhos diferentes porque o custo da ofuscação não
é necessariamente proporcional ao tamanho da entrada. Ele pode pesar mais numa
carga grande do que numa pequena, e só dá para enxergar isso medindo em mais de um
ponto.

## Ambiente de teste 1

- Sistema: Ubuntu 24.04.2 LTS
- Processador: Intel Core i5-1235U
- Memória: 8 GB
- Python 3.13
- PyArmor 9.3.0 (versão trial)

## Observações sobre a versão trial do PyArmor

A versão gratuita do PyArmor tem limitações que apareceram durante o trabalho e
que valem registro. Ela recusa alguns recursos com a mensagem `out of license`,
entre eles o nível mais alto de ofuscação de código (`--obf-code 2`) e o
embaralhamento de strings (`--mix-str`), e não libera os modos BCC e RFT. Também
há um limite para o tamanho do script. Por isso as duas configurações testadas
ficaram restritas ao que o nível gratuito permite. Os dois scripts `t4-*` são
curtos e foram ofuscados sem problemas nessa versão.
