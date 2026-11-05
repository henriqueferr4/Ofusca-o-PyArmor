#!/usr/bin/env python3
"""
Gera graficos e tabelas a partir de resultados_brutos.csv.

Produz:
  - grafico_estatisticas.png : media, mediana, desvio padrao, minimo e maximo,
                               com um painel para cada entrada
  - grafico_barras.png       : media por versao, agrupada por entrada, com barra
                               de erro (desvio padrao)
  - grafico_overhead.png     : fator de overhead (tempo_ofuscado / tempo_baseline)
                               por entrada
  - tabela_estatisticas.png  : as cinco estatisticas, como imagem para o relatorio
  - tabela_estatisticas.md   : a mesma tabela, em Markdown

Uso:
    python3 plot_results.py
"""

import csv
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

CSV_RAW = "resultados_brutos.csv"

# Cada versao mantem a mesma cor em todos os graficos.
CORES = ["#2a78d6", "#eb6834", "#1baf7a"]
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
SUPERFICIE = "#fcfcfb"

COLUNAS = ["Versão", "Entrada", "Média (s)", "Mediana (s)",
           "Desvio padrão (s)", "Mínimo (s)", "Máximo (s)"]

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA_SECUNDARIA,
    "axes.titlecolor": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRADE,
    "grid.linewidth": 0.8,
    "xtick.color": TINTA_SECUNDARIA,
    "ytick.color": TINTA_SECUNDARIA,
    "xtick.bottom": False,
    "ytick.left": False,
    "text.color": TINTA,
    "legend.frameon": False,
})


def load():
    data = defaultdict(list)  # (versao, entrada) -> [tempos]
    with open(CSV_RAW, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["versao"], int(row["entrada"]))
            data[key].append(float(row["tempo_s"]))
    return data


def resumir(tempos):
    return {
        "media": statistics.mean(tempos),
        "mediana": statistics.median(tempos),
        "desvio": statistics.stdev(tempos) if len(tempos) > 1 else 0.0,
        "minimo": min(tempos),
        "maximo": max(tempos),
    }


def linhas_da_tabela(stats, versoes, entradas):
    linhas = []
    for e in entradas:
        for v in versoes:
            s = stats[(v, e)]
            linhas.append([v, str(e)] + ["{:.3f}".format(s[campo]) for campo in
                                         ("media", "mediana", "desvio", "minimo", "maximo")])
    return linhas


def grafico_estatisticas(stats, versoes, entradas):
    # Eixos independentes: o tempo muda muito de uma entrada para outra, e numa
    # escala comum a dispersao de cada caso ficaria invisivel.
    fig, eixos = plt.subplots(1, len(entradas), figsize=(4.2 * len(entradas), 5),
                              squeeze=False)
    for ax, e in zip(eixos[0], entradas):
        for x, (v, cor) in enumerate(zip(versoes, CORES)):
            s = stats[(v, e)]
            ax.vlines(x, s["minimo"], s["maximo"], color=cor, linewidth=2, zorder=2)
            ax.hlines([s["minimo"], s["maximo"]], x - 0.08, x + 0.08, color=cor,
                      linewidth=2, zorder=2)
            ax.bar(x, 2 * s["desvio"], bottom=s["media"] - s["desvio"], width=0.34,
                   color=cor, alpha=0.3, linewidth=0, zorder=3)
            ax.hlines(s["mediana"], x - 0.17, x + 0.17, color=TINTA, linewidth=2, zorder=4)
            ax.scatter(x, s["media"], s=70, color=cor, edgecolors=SUPERFICIE,
                       linewidths=1.5, zorder=5)
            ax.text(x + 0.22, s["media"], "{:.2f}".format(s["media"]), va="center",
                    fontsize=9, color=TINTA_SECUNDARIA, zorder=6)
        ax.set_xticks(range(len(versoes)))
        ax.set_xticklabels(versoes)
        ax.set_xlim(-0.5, len(versoes) - 0.3)
        ax.margins(y=0.12)
        ax.set_title("Entrada {}".format(e), fontsize=11)
    eixos[0][0].set_ylabel("Tempo (s)")

    cinza = TINTA_SECUNDARIA
    legenda = [
        Line2D([], [], marker="o", linestyle="", color=cinza, markersize=8,
               label="Média (valor indicado)"),
        Line2D([], [], color=TINTA, linewidth=2, label="Mediana"),
        Patch(facecolor=cinza, alpha=0.3, label="Média ± desvio padrão"),
        Line2D([], [], color=cinza, linewidth=2, marker="_", markersize=9,
               label="Mínimo a máximo"),
    ]
    fig.suptitle("Estatísticas de tempo por versão (os eixos variam entre os painéis)",
                 fontsize=12)
    fig.legend(handles=legenda, loc="lower center", ncol=4, fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig("grafico_estatisticas.png", dpi=150)
    plt.close(fig)
    print("gerado: grafico_estatisticas.png")


def grafico_barras(stats, versoes, entradas):
    fig, ax = plt.subplots(figsize=(9, 5))
    n_v = len(versoes)
    largura = 0.8 / n_v
    for idx, (v, cor) in enumerate(zip(versoes, CORES)):
        medias = [stats[(v, e)]["media"] for e in entradas]
        erros = [stats[(v, e)]["desvio"] for e in entradas]
        posicoes = [i + idx * largura for i in range(len(entradas))]
        ax.bar(posicoes, medias, largura, yerr=erros, capsize=4, label=v, color=cor,
               edgecolor=SUPERFICIE, linewidth=2,
               error_kw={"ecolor": TINTA_SECUNDARIA, "elinewidth": 1.2})
    ax.set_xticks([i + largura * (n_v - 1) / 2 for i in range(len(entradas))])
    ax.set_xticklabels([str(e) for e in entradas])
    ax.set_xlabel("Entrada (tamanho do problema)")
    ax.set_ylabel("Tempo médio (s)")
    ax.set_title("Tempo médio por versão e entrada (barra de erro = desvio padrão)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("grafico_barras.png", dpi=150)
    plt.close(fig)
    print("gerado: grafico_barras.png")


def grafico_overhead(stats, versoes, entradas):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axhline(1.0, color=EIXO, linewidth=1.5, label="baseline (1x)")
    for v, cor in zip(versoes, CORES):
        if v == "baseline":
            continue
        fatores = [stats[(v, e)]["media"] / stats[("baseline", e)]["media"]
                   for e in entradas]
        ax.plot(entradas, fatores, marker="o", markersize=8, linewidth=2, color=cor,
                markeredgecolor=SUPERFICIE, markeredgewidth=1.5, label=v)
    ax.set_xlabel("Entrada (tamanho do problema)")
    ax.set_ylabel("Overhead (x vezes o baseline)")
    ax.set_title("Custo relativo da ofuscação por tamanho de entrada")
    ax.legend()
    fig.tight_layout()
    fig.savefig("grafico_overhead.png", dpi=150)
    plt.close(fig)
    print("gerado: grafico_overhead.png")


def tabela_imagem(linhas):
    fig, ax = plt.subplots(figsize=(10, 0.36 * (len(linhas) + 1) + 0.3))
    ax.axis("off")
    tabela = ax.table(cellText=linhas, colLabels=COLUNAS, loc="center", edges="horizontal",
                      cellLoc="right", colLoc="right",
                      colWidths=[0.11, 0.11, 0.14, 0.15, 0.2, 0.14, 0.14])
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(10)
    tabela.scale(1, 1.5)
    for (lin, col), celula in tabela.get_celld().items():
        celula.set_edgecolor(GRADE)
        celula.set_facecolor(SUPERFICIE)
        if col == 0:
            celula.set_text_props(ha="left")
        if lin == 0:
            celula.set_text_props(fontweight="bold")
            celula.set_edgecolor(EIXO)
    fig.savefig("tabela_estatisticas.png", dpi=150, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("gerado: tabela_estatisticas.png")


def tabela_markdown(linhas):
    with open("tabela_estatisticas.md", "w") as f:
        f.write("| " + " | ".join(COLUNAS) + " |\n")
        f.write("|:--|" + "--:|" * (len(COLUNAS) - 1) + "\n")
        for linha in linhas:
            f.write("| " + " | ".join(linha) + " |\n")
    print("gerado: tabela_estatisticas.md")


def tabela_terminal(linhas):
    larguras = [max(len(COLUNAS[i]), *(len(l[i]) for l in linhas))
                for i in range(len(COLUNAS))]
    def formatar(celulas):
        return "  ".join(c.ljust(larguras[0]) if i == 0 else c.rjust(larguras[i])
                         for i, c in enumerate(celulas))
    print(formatar(COLUNAS))
    for linha in linhas:
        print(formatar(linha))
    print()


def main():
    data = load()
    versoes = sorted({k[0] for k in data}, key=lambda v: (v != "baseline", v))
    entradas = sorted({k[1] for k in data})
    stats = {chave: resumir(tempos) for chave, tempos in data.items()}
    linhas = linhas_da_tabela(stats, versoes, entradas)

    tabela_terminal(linhas)
    grafico_estatisticas(stats, versoes, entradas)
    grafico_barras(stats, versoes, entradas)
    grafico_overhead(stats, versoes, entradas)
    tabela_imagem(linhas)
    tabela_markdown(linhas)


if __name__ == "__main__":
    main()
